"""Figuras de la evaluación crítica (EP5/EP6): árbol de preguntas, top 10 por tipo,
sensibilidad de umbrales, cobertura de votos, recencia, matriz de mejoras, paleta y segmentos.
Uso (desde la raíz del proyecto): python src/figuras_ep3.py   -> guarda en images/"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch

REPO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else REPO / "images"
OUT.mkdir(parents=True, exist_ok=True)
for f in font_manager.findSystemFonts():
    if "Inter" in f and f.endswith((".otf", ".ttf")):
        font_manager.fontManager.addfont(f)
plt.rcParams.update({"font.family": ["Inter", "DejaVu Sans"], "font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#B5B3AD", "axes.labelcolor": "#4B5060", "xtick.color": "#4B5060",
                     "ytick.color": "#4B5060", "axes.titleweight": "bold", "axes.titlesize": 14,
                     "axes.titlelocation": "left", "figure.dpi": 100, "savefig.dpi": 200})
TXT, TXT2 = "#1F2430", "#4B5060"
PEL, SER, JOYA, ESTR, POP, EST, SIN = "#2A78D6", "#E8702A", "#6250D6", "#127A55", "#E8B630", "#A8A5AD", "#DEDBD3"
GRIS = "#C9C6BF"

d = pd.read_csv(REPO / "data/processed/catalogo_unificado.csv", low_memory=False)


def save(fig, name, source="Fuente: catálogo unificado StreamView (31.991 contenidos), elaboración propia."):
    fig.text(0.01, 0.005, source, fontsize=8.5, color=TXT2, ha="left", va="bottom")
    fig.savefig(OUT / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# 1 · Árbol de preguntas -------------------------------------------------------
def box(ax, x, y, w, h, text, fc, tc="white", fs=10.5, bold=False):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.012,rounding_size=0.02",
                                fc=fc, ec="none"))
    ax.text(x, y, text, ha="center", va="center", color=tc, fontsize=fs, fontweight="bold" if bold else "normal", wrap=True)


fig, ax = plt.subplots(figsize=(13, 6.2))
ax.set_xlim(0, 1); ax.set_ylim(0, 1.08); ax.axis("off")
box(ax, 0.5, 0.9, 0.62, 0.11, "¿Qué contenidos de calidad no reciben atención\ny cómo debe actuar cada área de StreamView?", "#241F45", fs=12, bold=True)
mids = [(0.17, "¿Qué tiene el catálogo?\n(composición)", PEL), (0.5, "¿Qué es popular y qué está\nbien valorado? (desempeño)", JOYA),
        (0.83, "¿Cuánto podemos confiar\nen los datos? (calidad)", "#5A5F6E")]
leaves = {0.17: ["¿Qué géneros e idiomas\npredominan por tipo?", "¿De qué países\nviene el contenido?", "¿Qué géneros atraen\nmás dentro de su tipo?"],
          0.5: ["¿Cuántos títulos bien valorados\nestán fuera del 25% más popular?", "¿En qué idiomas y tipos\nse concentran las joyas?", "¿Qué presupuestos\nrecuperan la inversión?"],
          0.83: ["¿Qué % de títulos tiene\nvotos suficientes?", "¿El hallazgo cambia\nsi muevo los umbrales?", "¿Qué sesgos tienen\npopularidad y finanzas?"]}
for x, t, c in mids:
    ax.plot([0.5, x], [0.845, 0.66], color=GRIS, lw=1.5, zorder=0)
    box(ax, x, 0.62, 0.29, 0.1, t, c, fs=10.5, bold=True)
    for i, lt in enumerate(leaves[x]):
        y = 0.43 - i * 0.15
        ax.plot([x, x], [0.57, y + 0.05], color=GRIS, lw=1.2, zorder=0)
        box(ax, x, y, 0.27, 0.105, lt, "#F1EFFD" if c == JOYA else ("#EAF2FC" if c == PEL else "#EEEDEA"), tc=TXT, fs=9.5)
ax.text(0.0, 1.07, "Árbol de preguntas: de la pregunta de negocio a las preguntas analíticas", fontsize=14, fontweight="bold", color=TXT, va="top")
save(fig, "ep3_01_arbol_preguntas.png", "Elaboración propia.")

# 2 · Top 10 por tipo -----------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(13, 5.2), sharex=True)
for ax, t, c in zip(axes, ["Película", "Serie"], [PEL, SER]):
    top = d[d.tipo == t].nsmallest(10, "ranking_popularidad_tipo").iloc[::-1]
    vals = top.valoracion_valida
    cols = [ESTR if v >= 7 else GRIS for v in vals.fillna(0)]
    ax.barh(top.titulo.str.slice(0, 40), vals.fillna(0), color=cols, height=0.65)
    for yi, (v, n) in enumerate(zip(vals, top.votos)):
        ax.text((0 if pd.isna(v) else v) + 0.1, yi, "sin votos suficientes" if pd.isna(v) else f"{v:.2f}".replace(".", ","),
                va="center", fontsize=9.5, color=TXT)
    ax.axvline(7, color=TXT, ls="--", lw=1)
    ax.text(7.05, 9.6, "valoración 7", fontsize=9, color=TXT)
    n7 = int((vals >= 7).sum())
    ax.set_title(f"{'Películas' if t == 'Película' else 'Series'}: {n7} de 10 con valoración ≥ 7", fontsize=12.5, color=c)
    ax.set_xlim(0, 10); ax.tick_params(axis="y", labelsize=9.5)
fig.suptitle("Los 10 más populares de cada tipo: 7 películas tienen valoración de 7 o más; ninguna serie",
             x=0.01, ha="left", fontsize=14, fontweight="bold", color=TXT)
fig.tight_layout(rect=(0, 0.03, 1, 0.95))
save(fig, "ep3_02_top10_por_tipo.png", "Ranking de popularidad calculado dentro de cada tipo. Fuente: catálogo unificado StreamView, elaboración propia.")

# 3 · Sensibilidad de umbrales ----------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
for ax, mv in zip(axes, [10, 50]):
    grid = np.zeros((3, 3))
    for i, v in enumerate([6.5, 7, 7.5]):
        for j, pc in enumerate([70, 75, 80]):
            ok = d.votos >= mv
            good = ok & (d.valoracion >= v)
            hi = d.popularidad_percentil >= pc
            grid[i, j] = (good & ~hi).sum() / good.sum()
    im = ax.imshow(grid, cmap="Purples", vmin=0.3, vmax=0.8)
    for i in range(3):
        for j in range(3):
            val = grid[i, j]
            ax.text(j, i, f"{val*100:.0f}%", ha="center", va="center", fontsize=12, fontweight="bold",
                    color="white" if val > 0.6 else TXT)
            if mv == 10 and i == 1 and j == 1:
                ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False, ec="#E8702A", lw=3))
    ax.set_xticks(range(3), ["p70", "p75", "p80"]); ax.set_yticks(range(3), ["≥ 6,5", "≥ 7,0", "≥ 7,5"])
    ax.set_xlabel("Umbral de “popular” (percentil en su tipo)"); ax.set_ylabel("Umbral de “bien valorado”")
    ax.set_title(f"Mínimo de {mv} votos", fontsize=12.5)
    for s in ax.spines.values():
        s.set_visible(False)
fig.suptitle("El hallazgo resiste cambios de umbral: en 17 de 18 combinaciones, más de la mitad\nde lo bien valorado queda fuera del grupo más popular",
             x=0.01, ha="left", fontsize=14, fontweight="bold", color=TXT)
fig.tight_layout(rect=(0, 0.03, 1, 0.9))
save(fig, "ep3_03_sensibilidad_umbrales.png", "Celda: % de joyas ocultas sobre el total bien valorado. Recuadro naranjo: umbrales usados en el dashboard. Elaboración propia.")

# 4 · Cobertura de votos por idioma en series --------------------------------------
s = d[d.tipo == "Serie"]
cov = s.groupby("idioma_grupo").valoracion_confiable.apply(lambda x: (x == "Sí").mean()).sort_values()
n = s.groupby("idioma_grupo").size()
fig, ax = plt.subplots(figsize=(10, 4.4))
cols = [SER if k in ("Chino (mandarín)", "Francés", "Otros") else "#F3C4A4" for k in cov.index]
ax.barh(cov.index, cov.values, color=cols, height=0.62)
for yi, (k, v) in enumerate(cov.items()):
    ax.text(v + 0.01, yi, f"{v*100:.0f}%  ({n[k]:,} series)".replace(",", "."), va="center", fontsize=10, color=TXT)
ax.set_xlim(0, 0.85); ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
ax.set_title("Sesgo de cobertura: solo 11% de las series en chino tiene votos suficientes, frente a 64% en inglés")
fig.tight_layout(rect=(0, 0.04, 1, 1))
save(fig, "ep3_04_cobertura_votos_idioma.png", "% de series con 10 votos o más, por idioma original. Fuente: catálogo unificado StreamView, elaboración propia.")

# 5 · Popularidad y recencia ---------------------------------------------------------
med = d.groupby("anio_estreno").popularidad_percentil.median()
fig, ax = plt.subplots(figsize=(10, 4.2))
ax.plot(med.index[:-1], med.values[:-1], color=JOYA, lw=2.5, marker="o")
ax.plot(med.index[-2:], med.values[-2:], color=JOYA, lw=1.5, ls=":", marker="o")
for yr in (2010, 2024, 2025):
    ax.annotate(f"{med[yr]:.0f}", (yr, med[yr]), textcoords="offset points", xytext=(0, 9), ha="center", fontsize=10, color=TXT, fontweight="bold")
ax.axhline(50, color=GRIS, lw=1); ax.text(2010, 51.5, "mediana del catálogo (50)", fontsize=9, color=TXT2)
ax.set_ylim(0, 85); ax.set_ylabel("Percentil de popularidad mediano")
ax.set_xticks(range(2010, 2026, 2))
ax.set_title("La popularidad favorece lo reciente: percentil mediano 32 en 2010 y 70 en 2024")
ax.text(2025, 6, "2025: estrenos sin\nhistorial todavía", fontsize=9, color=TXT2, ha="center")
fig.tight_layout(rect=(0, 0.04, 1, 1))
save(fig, "ep3_05_popularidad_recencia.png")

# 6 · Matriz impacto / esfuerzo ----------------------------------------------------
mejoras = [  # (nombre, esfuerzo 1-5, impacto 1-5, prioridad)
    ("1. Campaña piloto con joyas\n(100+ votos) y medición", 1.6, 4.6, 1),
    ("2. Puntaje bayesiano\nde valoración", 2.0, 4.05, 1),
    ("3. Prueba con 5 usuarios\npor audiencia", 1.4, 3.2, 1),
    ("4. Actualización programada\nen Power BI Service", 2.9, 3.6, 2),
    ("5. Incentivar valoraciones\nde series", 3.1, 4.2, 2),
    ("6. Datos de reproducciones\ny usuarios", 4.5, 4.8, 3),
    ("7. Países en español y región", 1.2, 1.6, 3),
]
fig, ax = plt.subplots(figsize=(10.5, 6.2))
ax.axvline(3, color=GRIS, lw=1); ax.axhline(3, color=GRIS, lw=1)
for txt, x, y, ha in [("Victorias rápidas", 1.05, 5.25, "left"), ("Proyectos estratégicos", 4.95, 5.25, "right"),
                      ("Bajo valor", 1.05, 0.95, "left"), ("Evitar", 4.95, 2.8, "right")]:
    ax.text(x, y, txt, fontsize=10.5, color=TXT2, ha=ha, fontweight="bold")
pc = {1: JOYA, 2: SER, 3: EST}
for name, x, y, p in mejoras:
    ax.scatter(x, y, s=260, color=pc[p], zorder=3, edgecolor="white", lw=1.5)
    ax.text(x + 0.12, y, name, va="center", fontsize=9.5, color=TXT)
ax.set_xlim(0.8, 5.6); ax.set_ylim(0.7, 5.5)
ax.set_xlabel("Esfuerzo (tiempo, costo, dependencia de otras áreas) →"); ax.set_ylabel("Impacto en la decisión →")
ax.set_xticks([]); ax.set_yticks([])
for p, lab in [(1, "Prioridad 1 · próximas 4 semanas"), (2, "Prioridad 2 · trimestre"), (3, "Prioridad 3 · cuando haya datos")]:
    ax.scatter([], [], s=120, color=pc[p], label=lab)
ax.legend(loc="lower right", frameon=False, fontsize=9.5)
ax.set_title("Mejoras priorizadas por impacto y esfuerzo")
fig.tight_layout(rect=(0, 0.04, 1, 1))
save(fig, "ep3_06_matriz_mejoras.png", "Elaboración propia a partir de la evaluación crítica del dashboard.")

# 7 · Paleta bajo daltonismo ------------------------------------------------------
MAT = {"Visión típica": np.eye(3),
       "Deuteranopía": np.array([[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]]),
       "Protanopía": np.array([[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]]),
       "Tritanopía": np.array([[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.303900]])}
pal = [("Película", PEL), ("Serie", SER), ("Estrella", ESTR), ("Joya oculta", JOYA), ("Popular, val. media", POP), ("Estándar", EST), ("Sin valoración", SIN)]


def to_lin(h):
    c = np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)])
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def to_srgb(l):
    l = np.clip(l, 0, 1)
    return np.where(l <= 0.0031308, 12.92 * l, 1.055 * l ** (1 / 2.4) - 0.055)


fig, ax = plt.subplots(figsize=(11, 3.8))
for i, (vis, m) in enumerate(MAT.items()):
    for j, (lab, h) in enumerate(pal):
        ax.add_patch(plt.Rectangle((j, -i), 0.92, 0.8, color=to_srgb(m @ to_lin(h))))
    ax.text(-0.15, -i + 0.4, vis, ha="right", va="center", fontsize=10.5, color=TXT)
for j, (lab, h) in enumerate(pal):
    ax.text(j + 0.46, 0.9, lab.replace(" ", "\n", 1) if len(lab) > 9 else lab, ha="center", va="bottom", fontsize=9.5, color=TXT)
ax.set_xlim(-2.2, 7); ax.set_ylim(-3.3, 1.5); ax.axis("off")
ax.set_title("Dentro de cada gráfico, los colores se distinguen con los tres tipos de daltonismo", pad=12)
save(fig, "ep3_07_paleta_daltonismo.png", "Simulación con matrices de Machado et al. (2009), severidad completa. Elaboración propia.")
print("ok")

# 8 · Segmentos con la paleta accesible -----------------------------------------
orden = ["Estrella", "Joya oculta", "Popular, valoración media", "Estándar", "Sin valoración suficiente"]
colseg = {"Estrella": ESTR, "Joya oculta": JOYA, "Popular, valoración media": POP, "Estándar": EST, "Sin valoración suficiente": SIN}
tab = pd.crosstab(d.tipo, d.segmento, normalize="index")[orden].loc[["Serie", "Película"]]
fig, ax = plt.subplots(figsize=(11, 3.9))
left = np.zeros(2)
for seg in orden:
    v = tab[seg].values
    ax.barh(tab.index, v, left=left, color=colseg[seg], label=seg, height=0.6, edgecolor="white", lw=1.5)
    for yi, (l, w_) in enumerate(zip(left, v)):
        if w_ > 0.04:
            ax.text(l + w_ / 2, yi, f"{w_*100:.0f}%", ha="center", va="center", fontsize=10.5,
                    color="white" if seg in ("Estrella", "Joya oculta") else TXT)
    left += v
ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0)); ax.set_xlim(0, 1)
ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.14), frameon=False, fontsize=9.5)
ax.set_title("16% del catálogo son joyas ocultas: bien valoradas pero poco populares (15% de películas, 18% de series)", fontsize=13)
fig.tight_layout(rect=(0, 0.04, 1, 1))
save(fig, "ep3_08_segmentos.png", "Estrella y joya: valoración ≥ 7 con ≥ 10 votos; estrella además en el 25% más popular de su tipo. Elaboración propia.")
print("ok8")
