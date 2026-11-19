# Dashboard StreamView en Power BI

El dashboard está guardado como proyecto de Power BI (`StreamView.pbip`). Es un formato de texto, así que se puede versionar en GitHub y ver qué cambió entre commits. Los datos se leen desde los CSV de `data/processed/`, generados por `src/prep.py`.

## Abrirlo por primera vez

1. Instala o actualiza Power BI Desktop (versión 2025 o posterior).
2. Si el archivo no abre, ve a Archivo > Opciones y configuración > Opciones > Características en versión preliminar y activa estas tres opciones:
   - "Opción de guardar proyecto de Power BI (.pbip)"
   - "Almacenar el modelo semántico con formato TMDL"
   - "Almacenar informes con formato de metadatos mejorado (PBIR)"

   Después reinicia Power BI.
3. Abre `dashboard/powerbi/StreamView.pbip`. Los gráficos aparecen vacíos porque el proyecto todavía no tiene datos cargados.
4. Ve a Inicio > Transformar datos > Editar parámetros y cambia `CarpetaDatos` por la ruta completa de la carpeta `data/processed` del repositorio. Termínala con una barra invertida, por ejemplo `C:\Users\ignacio\Visual_Netflix_001D\data\processed\`.
5. Presiona Aplicar cambios o Actualizar. Se cargan cinco tablas: Catalogo, Generos, Paises, CalidadDatos y Decisiones.
6. Guarda. Para entregar una copia en un solo archivo, usa Archivo > Guardar como > `StreamView.pbix`.

## Actualización mensual

1. Reemplaza los dos CSV de `data/raw/` por los del nuevo mes, con los mismos nombres de archivo.
2. Ejecuta `python src/prep.py`.
3. En Power BI presiona Actualizar.

Las reglas de calidad, como el mínimo de 10 votos, la llave `content_id` y el percentil de popularidad, se aplican en `prep.py`, así que no se repiten a mano cada mes.

## Páginas

| Página | Público | Pregunta |
|---|---|---|
| Resumen ejecutivo | Directorio | ¿Cómo está el catálogo y dónde están las oportunidades? |
| Catálogo | Contenidos y Adquisición | ¿Qué tenemos y de dónde viene? |
| Popularidad y valoración | Marketing | ¿Qué está bien valorado pero recibe poca atención? |
| Finanzas | Dirección y Adquisición | ¿Qué relación hay entre presupuesto e ingresos? |
| Calidad y metodología | Data y Analytics | ¿Qué problemas tenían los datos y qué se decidió? |
| Detalle de títulos | Analistas | ¿Qué títulos cumplen una combinación de criterios? |

## Obtención de detalles (opcional, 1 minuto)

Para ir desde cualquier gráfico al listado de títulos:

1. Abre la página Detalle de títulos.
2. En el panel Visualizaciones > Obtención de detalles, arrastra `Catalogo[genero_principal]` y `Catalogo[idioma]`.
3. Desde ese momento, al hacer clic derecho sobre un género o idioma en otra página aparece "Obtener detalles > Detalle de títulos".
