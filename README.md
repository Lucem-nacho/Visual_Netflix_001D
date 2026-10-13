# StreamView Analytics — Visual Analytics del catálogo (EP2)

Proyecto ADY1104 – Visualización de Datos · Evaluación Parcial II (EP3 encargo + EP4 presentación).
Equipo consultor: Bastián Roman · Ignacio Gómez · Vicente Contreras.

En la EP1 analizamos solo el catálogo de películas. En la EP2 **integramos las dos fuentes oficiales del caso**
(películas y series) en un catálogo unificado de 31.991 contenidos. Con él construimos un dashboard en Looker Studio
orientado a tres audiencias: Directorio, Contenidos/Adquisición y Marketing.

**Dashboard publicado:** _(pegar aquí el enlace de Looker Studio)_

## Estructura

```
streamview/
├── data/
│   ├── raw/                                   # fuentes originales del caso (no se modifican)
│   │   ├── netflix_movies_detailed_up_to_2025.csv
│   │   └── netflix_tv_shows_detailed_up_to_2025.csv
│   └── processed/                             # generado por src/prep.py
│       ├── catalogo_unificado.csv             # 1 fila por contenido (fuente principal del dashboard)
│       ├── catalogo_generos.csv               # 1 fila por contenido x género armonizado
│       ├── catalogo_paises.csv                # 1 fila por contenido x país
│       ├── kpis_referencia.csv                # valores de control de los KPIs
│       ├── calidad_datos.csv                  # nulos y cardinalidad por fuente y variable
│       ├── decisiones_integracion.csv         # decisiones de integración (página de metodología)
│       └── movies_clean_EP1.csv               # salida de la EP1 (referencia)
├── notebooks/
│   ├── 01_EDA_Data_Movies_EP1.ipynb           # EP1: limpieza y EDA de películas
│   └── 02_integracion_EDA.ipynb               # EP2: calidad, integración y EDA del catálogo unificado
├── src/
│   └── prep.py                                # pipeline de integración reutilizable
├── dashboard/
│   └── GUIA_LOOKER_STUDIO.md                  # construcción del dashboard paso a paso (páginas, KPIs, filtros)
├── images/                                    # gráficos estáticos (PNG, 200 dpi) para informe y presentación
├── requirements.txt
└── README.md
```

## Cómo ejecutar

```bash
pip install -r requirements.txt
python src/prep.py                     # regenera data/processed/
jupyter notebook notebooks/02_integracion_EDA.ipynb   # ejecutar desde la carpeta notebooks/
```

Todas las rutas son relativas al proyecto, así que funciona en cualquier computador.
Después se suben los CSV de `data/processed/` a Looker Studio siguiendo `dashboard/GUIA_LOOKER_STUDIO.md`.

## Decisiones de integración y calidad

| # | Hallazgo | Decisión |
|---|---|---|
| 1 | `show_id` se repite entre películas y series (397 ids) | Llave compuesta `content_id` = `M-<id>` / `S-<id>` |
| 2 | 9 `show_id` duplicados en series | Se conserva la fila con más votos |
| 3 | Taxonomías de géneros distintas (`Action` vs `Action & Adventure`) | 22 géneros armonizados en español |
| 4 | `genres` y `country` multivaluados | Tablas puente `catalogo_generos` y `catalogo_paises` |
| 5 | Escalas de popularidad no comparables (mediana 10,9 vs 36,2) | `popularidad_percentil` dentro de cada tipo |
| 6 | `vote_average` = 0 sin votos; 62% de las series con menos de 10 votos | `valoracion_valida` solo con ≥ 10 votos |
| 7 | `rating` = `vote_average` en el 100% de ambas fuentes | Se excluye como clasificación etaria |
| 8 | `duration` vacía (películas) / constante "1 Seasons" (series) | Se excluye |
| 9 | 1.000 títulos por año y tipo; `date_added` = año de estreno | No se reporta crecimiento del catálogo |
| 10 | `budget`/`revenue` en 0 y presupuestos de US$1–400 | 0 = no informado; ROI solo con presupuesto ≥ US$1 M (22% de las películas) |

## Diccionario del catálogo unificado

| Campo | Descripción |
|---|---|
| `content_id` | Llave única (`M-` película, `S-` serie) |
| `tipo` | Película / Serie |
| `titulo`, `anio_estreno`, `fecha_incorporacion`, `periodo` | Identificación y tiempo (periodo: 2010-2014, 2015-2019, 2020-2025) |
| `genero_principal`, `generos`, `n_generos` | Primer género y lista armonizada |
| `pais_principal`, `n_paises`, `coproduccion` | País principal y si es coproducción |
| `idioma_codigo`, `idioma` | Idioma original (código ISO y nombre en español) |
| `popularidad` | Índice de popularidad TMDB (no comparable entre tipos) |
| `popularidad_percentil` | Percentil 0–100 de popularidad dentro de su tipo |
| `votos`, `valoracion` | Votos y valoración original (0 = sin votos) |
| `valoracion_confiable`, `valoracion_valida` | Sí/No si tiene ≥ 10 votos; valoración solo cuando es confiable |
| `segmento` | Estrella (popularidad ≥ p75 y valoración ≥ 7) · Joya oculta (< p75 y ≥ 7) · Popular, valoración media · Estándar · Sin valoración suficiente |
| `presupuesto_usd`, `ingresos_usd`, `datos_financieros` | Solo películas con ambos datos informados |
| `roi`, `resultado_financiero`, `rango_presupuesto` | ROI = ingresos / presupuesto (presupuesto ≥ US$1 M) |

## Fuentes

Datasets *Netflix Movies Detailed up to 2025* y *Netflix TV Shows Detailed up to 2025*, entregados con el
Caso Semestral StreamView Analytics (ADY1104). No se usaron fuentes externas.
