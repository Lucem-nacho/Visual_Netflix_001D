"""
StreamView Analytics — integración de fuentes (Películas + Series).

Uso desde la raíz del proyecto:
    python src/prep.py

Lee los dos CSV originales de data/raw/ (sin modificarlos) y genera en data/processed/:
    catalogo_unificado.csv   una fila por contenido (fuente principal del dashboard)
    catalogo_generos.csv     una fila por contenido-género (géneros armonizados)
    catalogo_paises.csv      una fila por contenido-país
    kpis_referencia.csv      valores de control para verificar los KPIs del dashboard
    calidad_datos.csv        resumen de calidad por fuente y variable
    decisiones_integracion.csv  decisiones de integración (página de metodología del dashboard)

Todas las reglas están documentadas en README.md y en notebooks/02_integracion_EDA.ipynb.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"

MOVIES_FILE = RAW / "netflix_movies_detailed_up_to_2025.csv"
SERIES_FILE = RAW / "netflix_tv_shows_detailed_up_to_2025.csv"

# Umbrales de negocio (documentados en el README)
MIN_VOTOS = 10            # valoración "confiable": al menos 10 votos
MIN_PRESUPUESTO_ROI = 1_000_000  # ROI solo con presupuesto >= US$1 M (evita presupuestos mal cargados)
PERCENTIL_ALTO = 75       # popularidad alta = percentil >= 75 dentro de su tipo
VALORACION_ALTA = 7.0     # valoración alta = >= 7 (escala 0-10)

# Armonización de géneros: TMDB usa taxonomías distintas para películas y series.
# Se llevan a una lista común en español para poder compararlas (Regla de Negocio #2).
GENEROS = {
    # comunes
    "Drama": "Drama", "Comedy": "Comedia", "Animation": "Animación", "Family": "Familia",
    "Crime": "Crimen", "Mystery": "Misterio", "Documentary": "Documental", "Western": "Western",
    # películas -> categoría común
    "Action": "Acción y Aventura", "Adventure": "Acción y Aventura",
    "Science Fiction": "Ciencia ficción y Fantasía", "Fantasy": "Ciencia ficción y Fantasía",
    "War": "Bélico y Política",
    # series -> categoría común
    "Action & Adventure": "Acción y Aventura", "Sci-Fi & Fantasy": "Ciencia ficción y Fantasía",
    "War & Politics": "Bélico y Política",
    # solo películas
    "Thriller": "Suspenso", "Horror": "Terror", "Romance": "Romance", "History": "Historia",
    "Music": "Música", "TV Movie": "Película para TV",
    # solo series
    "Reality": "Reality", "Kids": "Infantil", "Talk": "Talk show", "Soap": "Telenovela",
    "News": "Noticias",
    # sin información
    "Unknown": None,
}

IDIOMAS = {
    "en": "Inglés", "zh": "Chino (mandarín)", "cn": "Chino (cantonés)", "ja": "Japonés",
    "ko": "Coreano", "es": "Español", "fr": "Francés", "de": "Alemán", "hi": "Hindi",
    "tl": "Tagalo", "pt": "Portugués", "ru": "Ruso", "it": "Italiano", "tr": "Turco",
    "ar": "Árabe", "nl": "Neerlandés", "th": "Tailandés", "pl": "Polaco", "sv": "Sueco",
    "da": "Danés", "no": "Noruego", "id": "Indonesio", "cs": "Checo", "he": "Hebreo",
    "ta": "Tamil", "el": "Griego", "ur": "Urdu", "fi": "Finés", "te": "Telugu",
    "hu": "Húngaro", "fa": "Persa", "ca": "Catalán", "ml": "Malayalam", "af": "Afrikáans",
    "sr": "Serbio", "uk": "Ucraniano", "ro": "Rumano", "ms": "Malayo", "vi": "Vietnamita",
    "bn": "Bengalí", "kn": "Canarés", "mr": "Maratí", "is": "Islandés",
}


DECISIONES = [
    ("Llave del catálogo", "show_id se repite entre películas y series (397 ids)", "content_id = M-<id> / S-<id>"),
    ("Duplicados", "9 show_id repetidos en series", "Se conserva la fila con más votos"),
    ("Géneros", "Taxonomías distintas entre fuentes (Action vs Action & Adventure)", "22 géneros armonizados en español; tabla puente catalogo_generos"),
    ("Países", "Campo multivaluado (coproducciones)", "Tabla puente catalogo_paises; cada país cuenta"),
    ("Popularidad", "Escalas no comparables (mediana 10,9 películas vs 36,2 series)", "popularidad_percentil calculado dentro de cada tipo"),
    ("Valoración", "vote_average = 0 sin votos; 62% de series con < 10 votos", "valoracion_valida solo con >= 10 votos"),
    ("Clasificación etaria", "rating = vote_average en 100% de los registros", "Excluida; KPIs de clasificación no calculables"),
    ("Duración", "Vacía en películas; constante '1 Seasons' en series", "Excluida"),
    ("Tendencia temporal", "1.000 títulos por año y tipo; date_added = año de estreno", "No se informa crecimiento del catálogo; sí tendencias de valoración"),
    ("Finanzas", "budget/revenue en 0 (69,7% / 64,7%) y presupuestos de US$1-400", "0 = no informado; ROI solo con presupuesto >= US$1 M; alcance 22% de películas"),
    ("Segmentos", "Se necesita priorizar contenidos", "Estrella / Joya oculta / Popular valoración media / Estándar (percentil 75 y valoración 7)"),
]


def _split(s):
    """Separa un campo multivaluado 'A, B, C' en lista limpia."""
    if pd.isna(s):
        return []
    return [x.strip() for x in str(s).split(",") if x.strip()]


def _generos(s):
    vistos = []
    for g in _split(s):
        h = GENEROS.get(g, g)
        if h and h not in vistos:
            vistos.append(h)
    return vistos


def cargar():
    movies = pd.read_csv(MOVIES_FILE)
    series = pd.read_csv(SERIES_FILE)
    return movies, series


def integrar(movies: pd.DataFrame, series: pd.DataFrame) -> pd.DataFrame:
    m = movies.copy()
    s = series.copy()

    # 1) Duplicados: las series traen 9 show_id repetidos (mismo título). Se conserva la fila con más votos.
    s = (s.sort_values("vote_count", ascending=False)
           .drop_duplicates(subset="show_id", keep="first")
           .sort_index())

    # 2) Llave compuesta: show_id NO es único entre fuentes (397 ids se repiten entre películas y series).
    m["content_id"] = "M-" + m["show_id"].astype(str)
    s["content_id"] = "S-" + s["show_id"].astype(str)
    m["tipo"] = "Película"
    s["tipo"] = "Serie"

    # 3) Columnas que solo existen en películas
    s["budget"] = np.nan
    s["revenue"] = np.nan

    cols = ["content_id", "show_id", "tipo", "title", "director", "cast", "country", "date_added",
            "release_year", "genres", "language", "description", "popularity", "vote_count",
            "vote_average", "budget", "revenue"]
    df = pd.concat([m[cols], s[cols]], ignore_index=True)
    # 'rating' (idéntica a vote_average en ambas fuentes) y 'duration' (vacía en películas,
    # constante "1 Seasons" en series) no aportan información y se excluyen.

    out = pd.DataFrame({
        "content_id": df["content_id"],
        "tipo": df["tipo"],
        "titulo": df["title"],
        "anio_estreno": df["release_year"].astype(int),
        "fecha_incorporacion": pd.to_datetime(df["date_added"]).dt.date,
    })
    out["periodo"] = pd.cut(out["anio_estreno"], bins=[2009, 2014, 2019, 2025],
                            labels=["2010-2014", "2015-2019", "2020-2025"]).astype(str)

    # Géneros armonizados
    gl = df["genres"].apply(_generos)
    out["genero_principal"] = gl.apply(lambda x: x[0] if x else "Sin información")
    out["n_generos"] = gl.apply(len)
    out["generos"] = gl.apply(lambda x: ", ".join(x) if x else None)

    # Países
    pl = df["country"].apply(_split)
    out["pais_principal"] = pl.apply(lambda x: x[0] if x else "Sin información")
    out["n_paises"] = pl.apply(len)
    out["coproduccion"] = np.where(out["n_paises"] > 1, "Sí", "No")

    # Idioma
    out["idioma_codigo"] = df["language"]
    out["idioma"] = df["language"].map(IDIOMAS).fillna("Otro")

    # Director principal (series: 68% sin dato)
    out["director"] = df["director"].apply(lambda x: _split(x)[0] if _split(x) else None)

    # Popularidad: índice TMDB; las escalas de películas y series NO son comparables
    # (mediana 10,9 vs 36,2), por eso se agrega un percentil dentro de cada tipo.
    out["popularidad"] = df["popularity"].round(2)
    out["popularidad_percentil"] = (df.groupby("tipo")["popularity"]
                                      .rank(pct=True).mul(100).round(1))

    # Valoración: vote_average = 0 cuando no hay votos. Solo se considera confiable con >= MIN_VOTOS.
    out["votos"] = df["vote_count"].astype(int)
    out["valoracion"] = df["vote_average"].round(2)
    confiable = df["vote_count"] >= MIN_VOTOS
    out["valoracion_confiable"] = np.where(confiable, "Sí", "No")
    out["valoracion_valida"] = df["vote_average"].where(confiable).round(2)

    # Segmento de atractivo (popularidad relativa x valoración)
    alta_pop = out["popularidad_percentil"] >= PERCENTIL_ALTO
    alta_val = out["valoracion_valida"] >= VALORACION_ALTA
    out["segmento"] = np.select(
        [~confiable, alta_pop & alta_val, alta_pop & ~alta_val, ~alta_pop & alta_val],
        ["Sin valoración suficiente", "Estrella", "Popular, valoración media", "Joya oculta"],
        default="Estándar",
    )

    # Finanzas (solo películas). 0 = dato no informado.
    b = df["budget"].replace(0, np.nan)
    r = df["revenue"].replace(0, np.nan)
    tiene_fin = b.notna() & r.notna()
    out["presupuesto_usd"] = b.where(tiene_fin)
    out["ingresos_usd"] = r.where(tiene_fin)
    out["datos_financieros"] = np.where(out["tipo"] == "Serie", "No aplica (serie)",
                                np.where(tiene_fin, "Sí", "No informados"))
    roi_ok = tiene_fin & (b >= MIN_PRESUPUESTO_ROI)
    out["roi"] = (r / b).where(roi_ok).round(3)
    out["resultado_financiero"] = np.select(
        [~roi_ok, out["roi"] >= 3, out["roi"] >= 1],
        ["Sin ROI calculable", "Alto retorno (ROI >= 3)", "Recupera inversión (1-3)"],
        default="Pérdida (ROI < 1)",
    )
    out["rango_presupuesto"] = pd.cut(
        out["presupuesto_usd"], bins=[0, 1e6, 1e7, 5e7, 1e8, np.inf],
        labels=["< 1 M", "1-10 M", "10-50 M", "50-100 M", "> 100 M"], right=False,
    ).astype(str).replace("nan", None)

    out["descripcion"] = df["description"]
    return out, gl, pl


def tablas_explotadas(cat, gl, pl):
    base = ["content_id", "tipo", "titulo", "anio_estreno", "periodo", "idioma",
            "popularidad", "popularidad_percentil", "votos", "valoracion_valida", "segmento"]
    gen = cat[base].assign(genero=gl).explode("genero").dropna(subset=["genero"])
    pai = cat[base].assign(pais=pl).explode("pais").dropna(subset=["pais"])
    return gen, pai


def kpis(cat: pd.DataFrame, gen: pd.DataFrame, pai: pd.DataFrame) -> pd.DataFrame:
    pel = cat[cat["tipo"] == "Película"]
    fin = pel[pel["datos_financieros"] == "Sí"]
    roi = pel.dropna(subset=["roi"])
    filas = [
        ("Total de contenidos", len(cat), "COUNT_DISTINCT(content_id)"),
        ("Total de películas", len(pel), "COUNT_DISTINCT(content_id) con tipo = Película"),
        ("Total de series", (cat["tipo"] == "Serie").sum(), "COUNT_DISTINCT(content_id) con tipo = Serie"),
        ("Países representados", pai["pais"].nunique(), "COUNT_DISTINCT(pais) en catalogo_paises"),
        ("Idiomas disponibles", cat["idioma_codigo"].nunique(), "COUNT_DISTINCT(idioma_codigo)"),
        ("Géneros (armonizados)", gen["genero"].nunique(), "COUNT_DISTINCT(genero) en catalogo_generos"),
        ("Popularidad mediana - películas", pel["popularidad"].median(), "MEDIAN(popularidad)"),
        ("Popularidad mediana - series", cat.loc[cat["tipo"] == "Serie", "popularidad"].median(), "MEDIAN(popularidad)"),
        ("% con valoración confiable", (cat["valoracion_confiable"] == "Sí").mean() * 100, "COUNT(valoracion_valida)/COUNT(content_id)"),
        ("Valoración promedio confiable", cat["valoracion_valida"].mean(), "AVG(valoracion_valida)"),
        ("Valoración promedio confiable - películas", pel["valoracion_valida"].mean(), "AVG(valoracion_valida)"),
        ("Valoración promedio confiable - series", cat.loc[cat["tipo"] == "Serie", "valoracion_valida"].mean(), "AVG(valoracion_valida)"),
        ("Joyas ocultas", (cat["segmento"] == "Joya oculta").sum(), "COUNT con segmento = Joya oculta"),
        ("Estrellas", (cat["segmento"] == "Estrella").sum(), "COUNT con segmento = Estrella"),
        ("Películas con datos financieros", len(fin), "COUNT con datos_financieros = Sí"),
        ("Cobertura financiera (% películas)", len(fin) / len(pel) * 100, "Películas con datos / total películas"),
        ("Presupuesto promedio (USD)", fin["presupuesto_usd"].mean(), "AVG(presupuesto_usd)"),
        ("Ingresos promedio (USD)", fin["ingresos_usd"].mean(), "AVG(ingresos_usd) — solo películas con datos"),
        ("Presupuesto total (USD)", fin["presupuesto_usd"].sum(), "SUM(presupuesto_usd)"),
        ("Ingresos totales (USD)", fin["ingresos_usd"].sum(), "SUM(ingresos_usd)"),
        ("ROI agregado (ingresos totales / presupuesto total)", roi["ingresos_usd"].sum() / roi["presupuesto_usd"].sum(), "SUM(ingresos_usd)/SUM(presupuesto_usd) sobre roi no nulo"),
        ("ROI mediano", roi["roi"].median(), "MEDIAN(roi)"),
        ("% películas que recuperan inversión", (roi["roi"] >= 1).mean() * 100, "COUNT(roi>=1)/COUNT(roi)"),
    ]
    return pd.DataFrame(filas, columns=["kpi", "valor", "calculo_en_looker"]).assign(
        valor=lambda d: d["valor"].astype(float).round(2))


def calidad(movies, series) -> pd.DataFrame:
    filas = []
    for nombre, df in [("Películas", movies), ("Series", series)]:
        n = len(df)
        for col in df.columns:
            filas.append({"fuente": nombre, "variable": col, "registros": n,
                          "nulos": int(df[col].isna().sum()),
                          "pct_nulos": round(df[col].isna().mean() * 100, 1),
                          "valores_distintos": int(df[col].nunique())})
    return pd.DataFrame(filas)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    movies, series = cargar()
    cat, gl, pl = integrar(movies, series)
    gen, pai = tablas_explotadas(cat, gl, pl)
    cat.to_csv(OUT / "catalogo_unificado.csv", index=False)
    gen.to_csv(OUT / "catalogo_generos.csv", index=False)
    pai.to_csv(OUT / "catalogo_paises.csv", index=False)
    kpis(cat, gen, pai).to_csv(OUT / "kpis_referencia.csv", index=False)
    calidad(movies, series).to_csv(OUT / "calidad_datos.csv", index=False)
    pd.DataFrame(DECISIONES, columns=["tema", "hallazgo", "decision"]).to_csv(
        OUT / "decisiones_integracion.csv", index=False)
    print(f"catalogo_unificado: {len(cat):,} filas | generos: {len(gen):,} | paises: {len(pai):,}")


if __name__ == "__main__":
    main()
