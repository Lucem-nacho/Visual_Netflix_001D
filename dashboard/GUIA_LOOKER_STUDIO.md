# Guía de construcción del dashboard — Looker Studio (EP2)

Esta guía permite construir el dashboard completo a partir de los archivos de `data/processed/`.
Cada decisión está justificada para poder defenderla en la presentación (IE15, IE19, IE20, IE21).

**Valores de control:** todos los KPIs deben coincidir con `data/processed/kpis_referencia.csv`.
Si un número no coincide, el cálculo en Looker está mal (así se detectó el error de "Ingresos promedio" de la EP1).

---

## 0. Antes de empezar

1. Ejecutar `python src/prep.py` (o el notebook `02_integracion_EDA.ipynb`) para regenerar los CSV.
2. Crear un informe nuevo en [lookerstudio.google.com](https://lookerstudio.google.com) → **Informe en blanco**.
3. Tamaño de página: **Archivo → Configuración del informe → 1366 × 1100 px** (cabe en pantalla de proyector).

## 1. Fuentes de datos

Agregar cada archivo con **Añadir datos → Subir archivo (File Upload)**:

| Fuente en Looker | Archivo | Una fila es | Se usa para |
|---|---|---|---|
| `Catálogo` | `catalogo_unificado.csv` | un contenido | KPIs, segmentos, finanzas, popularidad vs valoración, rankings |
| `Géneros` | `catalogo_generos.csv` | un contenido × un género | Todo lo que se agrupa por género |
| `Países` | `catalogo_paises.csv` | un contenido × un país | Mapa y ranking de países |
| `Decisiones` | `decisiones_integracion.csv` | una decisión | Página de metodología |
| `KPIs control` | `kpis_referencia.csv` | un KPI | Verificación (no se muestra) |

> **Por qué tres tablas y no una:** `genres` y `country` son multivaluados ("Drama, Comedia"). Looker no separa listas;
> si se agrupa por el campo original aparecen combinaciones ("Comedia, Drama") y la barra "Otros" domina, que fue el
> principal problema del dashboard de la EP1. Las tablas puente cuentan cada género y país por separado.
> En `Géneros` y `Países` un contenido aparece varias veces, por eso **siempre se cuenta con `COUNT_DISTINCT(content_id)`**.

### 1.1 Tipos de campo (en cada fuente → *Editar conexión* / *Editar campos*)

| Campo | Tipo | Agregación por defecto |
|---|---|---|
| `content_id`, `titulo`, `tipo`, `segmento`, `idioma`, `genero`, `genero_principal`, `periodo`, `resultado_financiero`, `rango_presupuesto` | Texto | Ninguna |
| `anio_estreno` | **Fecha y hora → Año** (para gráficos de líneas) | Ninguna |
| `pais`, `pais_principal` | **Geográfico → País** | Ninguna |
| `popularidad`, `popularidad_percentil`, `votos` | Número | Mediana (popularidad), Suma (votos) |
| `valoracion_valida` | Número | **Promedio** |
| `presupuesto_usd`, `ingresos_usd` | **Moneda → USD** | Promedio |
| `roi` | Número (2 decimales) | **Mediana** |

> Las celdas vacías (por ejemplo `valoracion_valida` cuando hay menos de 10 votos) llegan como nulas y
> `AVG`/`MEDIAN` las ignoran. **No usar el campo `valoracion`** en promedios: incluye ceros de contenidos sin votos.

### 1.2 Campos calculados (fuente `Catálogo` → *Añadir un campo*)

| Nombre | Fórmula | Formato |
|---|---|---|
| Contenidos | `COUNT_DISTINCT(content_id)` | Número |
| Películas | `SUM(CASE WHEN tipo = "Película" THEN 1 ELSE 0 END)` | Número |
| Series | `SUM(CASE WHEN tipo = "Serie" THEN 1 ELSE 0 END)` | Número |
| Valoración promedio | `AVG(valoracion_valida)` | Número, 2 decimales |
| % valoración confiable | `SUM(CASE WHEN valoracion_confiable = "Sí" THEN 1 ELSE 0 END) / COUNT(content_id)` | Porcentaje |
| Joyas ocultas | `SUM(CASE WHEN segmento = "Joya oculta" THEN 1 ELSE 0 END)` | Número |
| Popularidad relativa | `MEDIAN(popularidad_percentil)` | Número, 1 decimal |
| Películas con finanzas | `SUM(CASE WHEN datos_financieros = "Sí" THEN 1 ELSE 0 END)` | Número |
| Cobertura financiera | `SUM(CASE WHEN datos_financieros = "Sí" THEN 1 ELSE 0 END) / SUM(CASE WHEN tipo = "Película" THEN 1 ELSE 0 END)` | Porcentaje |
| ROI mediano | `MEDIAN(roi)` | Número, 2 decimales |
| % recupera inversión | `SUM(CASE WHEN roi >= 1 THEN 1 ELSE 0 END) / SUM(CASE WHEN resultado_financiero != "Sin ROI calculable" THEN 1 ELSE 0 END)` | Porcentaje |

En `Géneros` y `Países` crear también `Contenidos = COUNT_DISTINCT(content_id)` y `Popularidad relativa = MEDIAN(popularidad_percentil)`.

> **Popularidad relativa vs índice TMDB:** la mediana del índice es 10,9 en películas y 36,2 en series; no son comparables
> (Regla de Negocio #2). Cuando un gráfico mezcla tipos se usa el percentil (0–100) calculado dentro de cada tipo.

## 2. Tema y estilo (consistencia gráfica — IE17, IE21)

**Tema y diseño → Personalizar:**

| Elemento | Valor | Motivo |
|---|---|---|
| Fondo | `#FCFCFB` (claro) | Mejor contraste para proyector e impresión que el tema oscuro de la EP1 |
| Texto principal / secundario | `#0B0B0B` / `#52514E` | Contraste AA |
| Fuente | Roboto o Inter | Legible en tamaños chicos |
| Película | `#2A78D6` (azul) | El mismo color en **todos** los gráficos y en el informe |
| Serie | `#EB6834` (naranja) | Par azul/naranja distinguible con daltonismo |
| Contexto / sin dato | `#B7B5AE` (gris) | Lo secundario se ve secundario |
| Segmentos | Estrella `#1BAF7A` · Joya oculta `#6250D6` · Popular valoración media `#EDA100` · Estándar `#D6D4CD` · Sin valoración `#EFEEE9` | Fijos por categoría |

Para fijar los colores por categoría: en cada gráfico → **Estilo → Colores por valor de dimensión**, asignar Película/Serie
una vez; Looker los recuerda para todo el informe.

Reglas para todos los gráficos:
- Título que diga **la conclusión**, no la variable ("Drama es el género más presente pero no el más atractivo", no "genres").
- Etiquetas de negocio, nunca nombres de columna (`popularidad_percentil` → "Popularidad relativa (percentil)").
- Números con separador de miles y moneda abreviada ("US$ 103,8 M").
- Sin 3D, sin degradados, sin gráficos de torta con más de 3 porciones.
- Subtítulo de alcance cuando aplique (Regla #7): "Películas con datos financieros (22% del catálogo de películas)".

## 3. Estructura y navegación (IE20)

Cinco páginas, una por audiencia. **Página → Gestionar páginas**, y en **Tema y diseño → Diseño → Navegación: "Izquierda"**
(menú lateral siempre visible). Además, en la cabecera de cada página poner **botones** (Insertar → Botón → Navegación de
página) hacia las otras páginas, y en la página 1 un botón "Ver detalle" junto a cada bloque.

```
1. Resumen ejecutivo           → Directorio y Gerencia General
2. Catálogo                    → Gerencia de Contenidos y Adquisición
3. Popularidad y valoración    → Marketing
4. Finanzas (películas)        → Directorio / Adquisición
5. Calidad y metodología       → Equipo Data & Analytics
```

**Cabecera común** (copiar y pegar en todas las páginas, mismas coordenadas):
título de la página · subtítulo con la pregunta que responde · fila de filtros · fecha de los datos ("Extracto 2010–2025").

## 4. Filtros e interacción (IE14, IE19)

| Control | Campo | Páginas | Notas |
|---|---|---|---|
| Lista desplegable | `tipo` | Todas (control **a nivel de informe**: clic derecho → *Hacer que sea a nivel de informe*) | Película / Serie |
| Lista desplegable | `periodo` | 1, 2, 3 | 2010–2014 / 2015–2019 / 2020–2025 |
| Lista desplegable con búsqueda | `idioma` | 2, 3 | |
| Lista desplegable con búsqueda | `genero` (fuente `Géneros`) | 2, 3 | |
| Control deslizante | `votos` | 3 | Mínimo de votos para el ranking de joyas ocultas |
| Control deslizante | `presupuesto_usd` | 4 | Rango de presupuesto |
| Botón "Restablecer" | — | Todas | Insertar → Botón → Restablecer filtros |

- **Filtros entre fuentes:** los tres archivos usan los mismos nombres (`tipo`, `periodo`, `idioma`), por lo que un mismo
  control filtra los gráficos de `Catálogo`, `Géneros` y `Países`. Comprobarlo después de crear cada control; si un gráfico
  no responde, revisar que el campo tenga exactamente el mismo nombre en su fuente.
- **Filtro cruzado:** en cada gráfico → *Configuración → Interacciones del gráfico → Filtro cruzado* activado. Hacer clic
  en una barra de género filtra el resto de la página. Es la interacción principal a demostrar en la defensa.
- **Desglose (drill-down):** en el gráfico de géneros activar *Desglose* con jerarquía `genero` → `titulo`;
  en el mapa, `pais` → `idioma`.
- **Tooltips:** al pasar el mouse cada marca muestra el valor exacto (activo por defecto; agregar métricas secundarias
  como `Contenidos` en el campo *Métrica de información sobre herramientas* cuando aplique).
- **Orden en tablas:** las tablas de ranking se ordenan al hacer clic en el encabezado.

## 5. Página por página

### Página 1 — Resumen ejecutivo (Directorio)

**Pregunta:** ¿Cómo está el catálogo y dónde están las oportunidades?

Fila de 6 **cuadros de resultados (scorecards)**, fuente `Catálogo`:

| KPI | Métrica | Valor esperado (sin filtros) |
|---|---|---|
| Contenidos | `Contenidos` | 31.991 |
| Películas / Series | `Películas`, `Series` (dos tarjetas o una con comparación) | 16.000 / 15.991 |
| Valoración promedio (≥ 10 votos) | `Valoración promedio` | 6,63 |
| % con valoración confiable | `% valoración confiable` | 63,6% |
| Joyas ocultas | `Joyas ocultas` | 5.256 |
| Cobertura financiera | `Cobertura financiera` | 22,1% |

Gráficos:
1. **Barras horizontales apiladas 100%** — dimensión `tipo`, desglose `segmento`, métrica `Contenidos`.
   Título: "1 de cada 6 contenidos es una joya oculta: bien evaluada pero poco popular".
   *Por qué:* compara la composición de dos grupos en una sola vista; la longitud es fácil de comparar.
2. **Barras horizontales** — `Géneros`, dimensión `genero`, métrica `Popularidad relativa`, desglose `tipo`, top 10.
   Título: "Presencia no es atractivo: Drama lidera en cantidad pero queda en la mediana de popularidad".
3. **Cuadro de texto** con 3 hallazgos y 3 recomendaciones (ver sección 7).

### Página 2 — Catálogo (Gerencia de Contenidos)

**Pregunta:** ¿Qué compone el catálogo y en qué se diferencian películas y series?

KPIs: Contenidos · Países representados (`COUNT_DISTINCT(pais)` en `Países`, esperado 147) ·
Idiomas (`COUNT_DISTINCT(idioma_codigo)`, esperado 83) · Géneros (`COUNT_DISTINCT(genero)` en `Géneros`, esperado 22).

1. **Barras horizontales agrupadas** — `Géneros`: dimensión `genero`, desglose `tipo`, métrica `Contenidos`, 14 barras,
   orden descendente. *Por qué:* muestra qué géneros existen solo en un tipo (Terror/Suspenso solo películas; Reality solo series).
2. **Mapa de burbujas o mapa geográfico (Google Maps)** — `Países`: dimensión `pais`, métrica `Contenidos`.
   *Por qué:* requerimiento técnico de mapas; permite comparar mercados productores (Problema 4 del caso).
   Acompañarlo con una **tabla con barras** (top 10 países, desglose por `tipo`) porque el mapa no permite comparar con precisión.
3. **Treemap** — `Catálogo`: dimensión `idioma`, métrica `Contenidos`, filtrable por `tipo`.
   *Por qué:* parte-todo con muchas categorías; con el filtro de tipo se ve que las series son 36% chino/japonés/coreano.
4. **Gráfico de áreas** — `Catálogo`: dimensión `anio_estreno`, desglose `tipo`, métrica `Contenidos`, apilado.
   Título honesto: "El extracto tiene 1.000 títulos por año y tipo: no hay tendencia de crecimiento que reportar".
   *Por qué:* responde la pregunta "¿cómo evolucionó el catálogo?" con lo que realmente muestran los datos.

### Página 3 — Popularidad y valoración (Marketing)

**Pregunta:** ¿Qué contenidos conviene promocionar?

KPIs: Popularidad mediana (por tipo, filtrar con el control) · Valoración promedio · Estrellas (2.717) · Joyas ocultas (5.256).

1. **Dispersión** — `Catálogo`: dimensión `content_id` (etiqueta `titulo` en tooltip), X `popularidad` (**escala logarítmica**
   en Estilo → Eje X), Y `valoracion_valida`, color por `segmento`, filtro `valoracion_confiable = Sí`.
   Agregar **líneas de referencia** en Y = 7 y en X = percentil 75 (17,3 películas / 62,2 series; usar la que corresponda al
   filtro de tipo o mostrar dos gráficos, uno por tipo). Límite de puntos: 5.000 en Estilo → *Número de burbujas*.
   *Por qué:* los cuadrantes visualizan los segmentos; la escala log evita que 10 títulos virales aplasten al resto.
2. **Barras horizontales** — `Géneros`: `genero` × `Popularidad relativa`, desglose `tipo`. Línea de referencia en 50.
3. **Tabla** "Joyas ocultas para promover" — `Catálogo`: `titulo`, `tipo`, `genero_principal`, `idioma`, `valoracion_valida`,
   `votos`, `popularidad_percentil`; filtro `segmento = Joya oculta`; orden por `valoracion_valida` desc; control deslizante
   de `votos` (por defecto ≥ 100). Formato condicional: barra en `valoracion_valida`.
4. **Tabla** "Top 10 más populares" por tipo (`popularidad` desc).

### Página 4 — Finanzas (películas)

**Pregunta:** ¿Qué relación hay entre inversión y retorno?

**Filtro de página:** `datos_financieros = Sí` (Página → Configuración actual de la página → Filtros). Esto garantiza que
ningún promedio incluya películas sin datos (Regla #6) y es lo que corrige el error de la EP1.

KPIs: Películas con finanzas (3.540) · Cobertura financiera (22,1%; esta tarjeta **sin** el filtro de página) ·
Presupuesto promedio (US$ 35,6 M) · Ingresos promedio (US$ 103,8 M) · ROI mediano (1,68) · % recupera inversión (63,1%).

1. **Dispersión** presupuesto vs ingresos, **ambos ejes logarítmicos**, color por `resultado_financiero`.
2. **Columnas** — `rango_presupuesto` × `ROI mediano`, con línea de referencia en 1.
   Título: "Las grandes producciones tienen el mayor retorno mediano (2,7x) y la menor tasa de pérdida".
3. **Barras horizontales** — top 10 `titulo` por `roi` (filtro `roi` no nulo).
4. **Nota de alcance** (cuadro de texto, gris): "Incluye solo películas con presupuesto e ingresos informados (3.540 de
   16.000). ROI = ingresos / presupuesto, calculado con presupuesto ≥ US$ 1 M. No representa rentabilidad neta."

### Página 5 — Calidad y metodología (Data & Analytics)

1. **Tabla** — fuente `Decisiones`: `tema`, `hallazgo`, `decision`.
2. **Barras** — % de nulos por variable y fuente (desde `calidad_datos.csv` si se agrega como fuente).
3. Cuadro de texto con las fuentes, fecha del extracto y el enlace al repositorio.

> Esta página responde directamente a IE16 (integración con consistencia y calidad) y le da al evaluador la evidencia sin
> tener que abrir el notebook.

## 6. Verificación antes de entregar (checklist)

- [ ] Todos los KPIs sin filtros coinciden con `kpis_referencia.csv`.
- [ ] Al filtrar `tipo = Serie`, la página 4 muestra "sin datos" o una nota (budget/revenue no aplican a series — Regla #3).
- [ ] Un mismo control (`tipo`) filtra gráficos de las tres fuentes.
- [ ] Ningún título, eje o leyenda muestra un nombre de columna.
- [ ] Película = azul y Serie = naranja en todas las páginas.
- [ ] El menú de páginas y los botones llevan a la página correcta.
- [ ] El informe funciona en modo **Ver** con una cuenta sin permisos de edición (abrir el enlace en ventana de incógnito).

## 7. Textos sugeridos para la página 1

**Hallazgos**
1. El catálogo integrado tiene 31.991 contenidos, pero 62% de las series no tiene votos suficientes para evaluarlas.
2. Presencia no es atractivo: Drama es el género más presente y queda en la mediana de popularidad; Acción y Aventura,
   Ciencia ficción y Animación son los más atractivos en películas.
3. 5.256 contenidos están bien evaluados pero son poco populares (joyas ocultas).

**Recomendaciones**
1. Marketing: priorizar las joyas ocultas en campañas de visibilidad (tabla de la página 3).
2. Adquisición: orientar compras de películas hacia Acción y Aventura, Ciencia ficción y Animación; en series, reforzar
   el contenido asiático, que ya es el núcleo del catálogo.
3. Data & Analytics: incentivar la valoración de series (solo 38% tiene ≥ 10 votos) y completar presupuesto/ingresos.

## 8. Publicación y exportación (IE23, IE24)

- **Compartir → Gestionar el acceso → "Cualquier persona con el enlace puede ver"**; pegar el enlace en el README e informe.
- **Archivo → Descargar → PDF** (todas las páginas, con enlace al informe) → guardar en `dashboard/StreamView_Dashboard_EP2.pdf`.
- Capturas PNG de cada página en `images/dashboard_p1.png` … `p5.png` para el informe y la presentación.
- **Compartir → Programar envío por correo** (opcional): demuestra que el producto es reutilizable por la organización.

## 9. Por qué Looker Studio (para la defensa — IE15)

| Requerimiento del caso | Cómo lo cumple Looker Studio |
|---|---|
| Dashboard interactivo con filtros y navegación | Controles a nivel de informe, filtro cruzado, desglose, páginas y botones |
| Fácil de reutilizar por distintas áreas | Se comparte con un enlace, sin licencias ni instalación; envíos programados |
| Integrar varias fuentes | Varias fuentes por informe y combinaciones (blends) |
| Consistencia gráfica | Tema del informe y colores fijos por valor de dimensión |

**Ventajas frente a las alternativas:** gratuito y en la nube (Power BI Desktop es solo Windows y publicar requiere
licencia Pro); colaboración simultánea del equipo; el equipo ya lo dominaba desde la EP1, lo que permitió invertir el
tiempo en la calidad de los datos y no en aprender una herramienta.

**Limitaciones (y cómo se mitigaron):**
- No separa campos multivaluados ni transforma datos → la preparación se hizo en Python (`src/prep.py`), reproducible.
- No hay versionado del dashboard → se exporta a PDF y se documenta la construcción en esta guía.
- Rendimiento con archivos grandes y límite de 100 MB por archivo subido → se subieron tablas ya agregadas por contenido.
- Menos control de diseño fino que Plotly/Dash → se compensó con un tema propio y reglas de estilo explícitas.
