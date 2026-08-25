# Proyecto 2 – Análisis Exploratorio

## Tema

**A Step Ahead of Drought: Forecasting Global Water Storage Challenge by ITU**
Series de tiempo con datos satelitales.

Reto organizado por la *International Telecommunication Union* (ITU) junto con
agencias del Sistema de Naciones Unidas, alojado en Zindi:
<https://zindi.world/competitions/one-step-ahead-of-drought-forecasting-global-water-storage-challenge>

## Curso

CC3084 – Data Science
Universidad del Valle de Guatemala · Facultad de Ingeniería
Departamento de Ciencias de la Computación · Semestre II – 2026

## Descripción

El reto busca anticipar el **Total Water Storage (TWS)**, es decir, el agua total
almacenada sobre y bajo la superficie terrestre —agua subterránea, humedad del
suelo, agua superficial, nieve y hielo—. El TWS se estima a escala global a partir
de las misiones satelitales **GRACE** y **GRACE-FO**, que lo derivan de las
variaciones del campo gravitatorio terrestre.

El problema operativo es la **latencia**: según la descripción del reto, los
productos derivados de GRACE se publican con un retraso aproximado de 2 a 3 meses,
lo que limita su uso para monitoreo de sequía casi en tiempo real. La tarea
consiste en predecir el TWS del mes siguiente (`t+1`) a partir de la información
disponible en el mes `t`. La métrica de evaluación del reto es el **RMSE**.

Este repositorio contiene el **análisis exploratorio** de ese conjunto de datos.
El objetivo de esta etapa no es construir el modelo final, sino entender el
fenómeno, la estructura de los datos y los patrones que después permitan plantear
un modelo con criterio.

## Objetivos

### Objetivo general

Caracterizar, mediante un análisis exploratorio reproducible, el comportamiento
temporal, estacional y espacial de la anomalía de almacenamiento total de agua
(TWS) y de sus covariables, con el fin de identificar los patrones y las variables
que sustenten la construcción posterior de un modelo de pronóstico a un mes de
horizonte.

### Objetivos específicos

1. Describir la estructura del conjunto de datos: observaciones, variables, tipos
   y cobertura temporal y espacial.
2. Evaluar la calidad de los datos: valores faltantes, duplicados y valores
   extremos, determinando si responden a patrones temporales o espaciales.
3. Analizar el comportamiento temporal de la variable objetivo: tendencia,
   estacionalidad y periodos anómalos.
4. Comparar el comportamiento del almacenamiento de agua entre ubicaciones
   geográficas.
5. Determinar el grado de asociación entre la variable objetivo, el almacenamiento
   del mes actual y las covariables climáticas.
6. Identificar las variables y transformaciones candidatas para la etapa posterior
   de modelado.

## Datos

Los archivos del reto **no se versionan** en este repositorio por su tamaño
(`Train.csv` pesa cerca de 276 MB). Deben descargarse desde Zindi y colocarse en
`data/raw/`.

| Archivo                | Tamaño aprox. | Filas       |
| ---------------------- | ------------: | ----------: |
| `Train.csv`            |      275.7 MB |   2 154 021 |
| `Test.csv`             |       32.8 MB |     280 961 |
| `SampleSubmission.csv` |        5.8 MB |           — |

Las instrucciones detalladas de descarga están en
[`data/raw/README.md`](data/raw/README.md).

Los archivos crudos son de **solo lectura**: nunca se modifican. Todo producto
derivado se escribe en `data/processed/`.

## Estructura del repositorio

```text
Proyecto2/
├── README.md
├── requirements.txt
├── Proyecto2_Analisis_Exploratorio.ipynb   Notebook principal del EDA
├── data/
│   ├── raw/                Datos del reto (no versionados) + instrucciones
│   └── processed/          Productos derivados del análisis
├── figures/                Gráficos exportados para el informe y la presentación
├── outputs/
│   └── tablas/             Tablas exportadas del análisis
├── scripts/
│   ├── inspeccionar_datos.py    Auditoría inicial de los archivos crudos
│   ├── construir_notebook.py    Genera el notebook principal
│   └── ejecutar_notebook.py     Ejecuta el notebook y verifica reproducibilidad
├── docs/                   Informe y material de la presentación
└── *.ipynb                 Ejemplos de clase (referencia metodológica, sin modificar)
```

Los notebooks `EjemploGIS_Sentinel2.ipynb`, `Practica01_Incendios.ipynb`,
`Ejemplo series de tiempo LSTM.ipynb` y `Ejemplo CNN gatos y perros.ipynb` son
material del curso y se conservan **sin modificaciones** como referencia
metodológica.

## Cómo ejecutar el proyecto

```bash
python3 -m pip install -r requirements.txt
```

Descargar los datos y colocarlos en `data/raw/` (ver
[`data/raw/README.md`](data/raw/README.md)). Luego verificar que los archivos se
leen correctamente:

```bash
python3 scripts/inspeccionar_datos.py
```

Finalmente, abrir el notebook y ejecutarlo completo (*Run All*), o bien ejecutarlo
desde la línea de comandos:

```bash
python3 scripts/ejecutar_notebook.py
```

El notebook usa **rutas relativas** a la raíz del repositorio y debe ejecutarse
desde ahí.

## Principales análisis realizados

- Descripción de variables y observaciones, y clasificación por tipo
  (identificadores, temporales, geográficas, satelitales, objetivo).
- Evaluación de calidad: valores faltantes, duplicados y su distribución temporal
  y espacial.
- Estadística descriptiva de las variables cuantitativas.
- Distribuciones e histogramas de la variable objetivo y de las covariables.
- Detección y análisis de valores atípicos mediante IQR y diagramas de caja, con
  criterio de no eliminarlos automáticamente por tratarse de datos climáticos.
- Análisis temporal: evolución de la variable objetivo, medias móviles y
  comparación entre periodos.
- Estacionalidad: perfil mensual, boxplots por mes y descomposición de la serie.
- Análisis espacial: comportamiento por latitud y por región de la rejilla global.
- Correlaciones entre variables y gráficos de dispersión de las relaciones más
  relevantes.
- Hallazgos, conclusiones y próximos pasos hacia la etapa de modelado.

> El estado de avance de cada sección está indicado dentro del propio notebook.

## Integrantes

<!-- Completar con los nombres y carnés de los cuatro integrantes del grupo. -->

1. ______________________________
2. ______________________________
3. ______________________________
4. ______________________________

## Referencias

- Zindi / ITU. *A Step Ahead of Drought: Forecasting Global Water Storage
  Challenge.*
  <https://zindi.world/competitions/one-step-ahead-of-drought-forecasting-global-water-storage-challenge>
- Copernicus European Drought Observatory. *GRACE Total Water Storage (TWS)
  Anomaly — Factsheet.*
  <https://drought.emergency.copernicus.eu/data/factsheets/factsheet_grace_tws_anomaly.pdf>
- Vicente-Serrano, S. M., Beguería, S. y López-Moreno, J. I. *SPEI: The
  Standardised Precipitation-Evapotranspiration Index.*
  <https://spei.csic.es/home.html>
- Universidad del Valle de Guatemala. *Guía del Proyecto 2 — Análisis
  Exploratorio, CC3084 Data Science*, Semestre II 2026.
