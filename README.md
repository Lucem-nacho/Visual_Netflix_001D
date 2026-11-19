# StreamView Analytics: calidad sin visibilidad

Proyecto del ramo ADY1104 Visualización de Datos (Duoc UC), caso semestral StreamView Analytics.
Equipo: Bastián Roman, Ignacio Gómez y Vicente Contreras.

StreamView tiene contenido muy bien valorado que su audiencia no está viendo. De los 7.973 títulos con valoración de 7 o más (y al menos 10 votos), 5.256 están fuera del 25% más popular de su tipo. Este repositorio tiene todo lo necesario para reproducir ese análisis y el dashboard que lo comunica.

| Entrega | Contenido |
|---|---|
| EP1 | Limpieza y EDA del catálogo de películas; dashboard en Looker Studio |
| EP2 | Integración de películas y series (31.991 títulos), dashboard de 5 páginas en Looker Studio, informe, infografía y storytelling |
| EP5 y EP6 | Dashboard migrado a Power BI con 6 páginas, evaluación crítica (sesgos, sensibilidad, accesibilidad), informe final y presentación |

## Estructura

```
Visual_Netflix_001D/
├── data/
│   ├── raw/                      CSV originales del caso (no se modifican)
│   └── processed/                generado por src/prep.py
│       ├── catalogo_unificado.csv     1 fila por contenido (tabla principal)
│       ├── catalogo_generos.csv       1 fila por contenido y género
│       ├── catalogo_paises.csv        1 fila por contenido y país
│       ├── kpis_referencia.csv        valores de control de los KPIs
│       ├── calidad_datos.csv          nulos por variable y fuente
│       ├── decisiones_integracion.csv las 11 decisiones de calidad
│       └── movies_clean_EP1.csv       salida de la EP1
├── notebooks/
│   ├── 01_EDA_Data_Movies_EP1.ipynb   EP1: películas
│   ├── 02_integracion_EDA.ipynb       EP2: integración y EDA del catálogo
│   └── 03_evaluacion_critica.ipynb    EP5/EP6: sesgos, ruido y sensibilidad de umbrales
├── src/
│   ├── prep.py                   integración y limpieza reproducible
│   └── figuras_ep3.py            figuras de la evaluación crítica
├── dashboard/
│   ├── powerbi/                  proyecto Power BI (StreamView.pbip) y StreamView.pbix
│   ├── GUIA_POWER_BI.md          cómo abrir, actualizar y publicar el dashboard
│   └── GUIA_LOOKER_STUDIO.md     versión EP2 en Looker Studio (referencia)
├── images/                       figuras EP2 y EP3, infografía y capturas del dashboard
├── reports/                      informe ejecutivo (PDF y Word), presentación (PPTX y PDF) y dashboard en PDF
├── requirements.txt
└── README.md
```

## Cómo ejecutar

```bash
pip install -r requirements.txt
python src/prep.py            # regenera data/processed/ desde data/raw/
python src/figuras_ep3.py     # regenera las figuras ep3_* en images/
```

Los notebooks se abren desde la carpeta `notebooks/` porque usan rutas relativas (`../data/processed/`).

Para el dashboard, abre `dashboard/powerbi/StreamView.pbip` en Power BI Desktop y cambia el parámetro `CarpetaDatos` por la ruta de `data/processed/` en tu computador (detalle en `dashboard/GUIA_POWER_BI.md`). Si solo quieres verlo, abre `StreamView.pbix` o `reports/Dashboard_StreamView_PowerBI.pdf`. Las capturas de cada página están en `images/dashboard_p*.png`.

## Actualización mensual

1. Reemplaza los dos CSV de `data/raw/` por los del mes, con los mismos nombres.
2. Ejecuta `python src/prep.py`.
3. En Power BI presiona Actualizar y compara los KPIs con `data/processed/kpis_referencia.csv`.

## Reglas de negocio

- **Popularidad:** se compara en percentil dentro de cada tipo, porque las escalas de películas y series no se comparan (mediana 10,9 y 36,2). No representa reproducciones.
- **Valoración:** solo se usa con 10 votos o más. Hoy cumple ese mínimo el 63,6% del catálogo: el 88,6% de las películas y el 38,4% de las series.
- **Segmentos:**
  - Joya oculta: valoración ≥ 7 con popularidad bajo el percentil 75 de su tipo.
  - Estrella: valoración ≥ 7 dentro del 25% más popular.
- **Finanzas:** presupuesto e ingresos existen solo para películas, y el 0 significa "no informado". El ROI se calcula con presupuesto de US$1 M o más y no es rentabilidad neta.
- **Año:** `date_added` coincide con el año de estreno, así que no se reporta crecimiento del catálogo.

## Decisiones de integración y calidad

| # | Hallazgo | Decisión |
|---|---|---|
| 1 | `show_id` se repite entre películas y series (397 ids) | Llave `content_id` = `M-<id>` / `S-<id>` |
| 2 | 9 `show_id` duplicados en series | Se conserva la fila con más votos |
| 3 | Taxonomías de géneros distintas | 22 géneros armonizados en español |
| 4 | `genres` y `country` con varios valores | Tablas puente de géneros y países |
| 5 | Escalas de popularidad no comparables | `popularidad_percentil` y `ranking_popularidad_tipo` por tipo |
| 6 | `vote_average` = 0 sin votos; 62% de series con menos de 10 votos | `valoracion_valida` solo con 10 votos o más |
| 7 | `rating` = `vote_average` en todos los registros | Se excluye |
| 8 | `duration` vacía (películas) o constante (series) | Se excluye |
| 9 | 1.000 títulos por año y tipo; `date_added` = año de estreno | No se reporta crecimiento |
| 10 | `budget` y `revenue` en 0 (69,7% y 64,7%) | ROI solo con presupuesto ≥ US$1 M (22% de las películas) |
| 11 | Se necesita priorizar contenidos | Segmentos por percentil 75 y valoración 7 |

## Evaluación crítica (resumen)

- **El hallazgo resiste cambios de umbral.** En 17 de 18 combinaciones de nota, popularidad y votos, más de la mitad de lo bien valorado queda fuera del grupo popular.
- **Hay sesgo de cobertura.** Solo el 11% de las series en chino tiene votos suficientes.
- **La popularidad favorece lo reciente.** El percentil mediano es 32 para los estrenos de 2010 y 70 para los de 2024.
- **Las finanzas tienen sesgo de supervivencia.** Las películas con datos son las más conocidas: percentil 76 frente a 42.
- **Se corrigió el top 10 de la EP2.** Mezclaba películas y series. Ahora se calcula por tipo: 7 de 10 películas y 0 de 10 series tienen nota de 7 o más.

El detalle está en `notebooks/03_evaluacion_critica.ipynb` y en la sección 9 del informe.

## Fuentes

Datasets *Netflix Movies Detailed up to 2025* y *Netflix TV Shows Detailed up to 2025*, entregados con el Caso Semestral StreamView Analytics (ADY1104). No se usaron fuentes externas.
