# Datos crudos del reto

Los archivos de este reto **no se versionan en el repositorio** porque `Train.csv`
pesa aproximadamente 276 MB. Cada integrante debe descargarlos una sola vez.

## Origen oficial

Reto: *A Step Ahead of Drought: Forecasting Global Water Storage Challenge*
Organizador: ITU (International Telecommunication Union) junto con agencias de Naciones Unidas.
Plataforma: Zindi.

<https://zindi.world/competitions/one-step-ahead-of-drought-forecasting-global-water-storage-challenge>

## Cómo descargarlos

1. Crear una cuenta en Zindi (o iniciar sesión).
2. Entrar a la página del reto y **aceptar las reglas de la competencia**.
   Zindi no permite descargar los archivos hasta que se aceptan.
3. Ir a la pestaña **Data** y descargar los archivos.
4. Colocarlos en esta carpeta (`data/raw/`), sin renombrarlos y sin descomprimir
   nada adicional.

## Archivos esperados

| Archivo                        | Tamaño aprox. | Filas       | Contenido                                          |
| ------------------------------ | ------------: | ----------: | -------------------------------------------------- |
| `Train.csv`                    |      275.7 MB |   2 154 021 | Covariables y variable objetivo para entrenamiento  |
| `Test.csv`                     |       32.8 MB |     280 961 | Covariables para el conjunto de evaluación          |
| `StarterNotebook.ipynb`        |        1.2 MB |           — | Notebook de referencia de la organización           |
| `SampleSubmission.csv`         |        5.8 MB |           — | Formato de entrega (`ID`, `Target`) — opcional      |
| `Trustworthiness_Evaluation.pdf` |     92.2 KB |         — | Guía de evaluación de confiabilidad de la IA — opcional |

Para el análisis exploratorio bastan `Train.csv` y `Test.csv`. El notebook los
exige y trata los demás como opcionales, porque `SampleSubmission.csv` solo
define el formato de entrega y no interviene en el EDA.

## Columnas reales verificadas

Ambos archivos vienen en formato plano: **una fila por combinación de mes y celda**
de una rejilla global de 1°.

| Columna                                        | Presente en   | Descripción                                                     |
| ---------------------------------------------- | ------------- | --------------------------------------------------------------- |
| `sample_id` (train) / `ID` (test)              | ambos         | Identificador con formato `AAAAMMDD_lat_lon`                     |
| `time`                                         | ambos         | Primer día del mes de observación                                |
| `lat`, `lon`                                   | ambos         | Centro de la celda, en grados                                    |
| `TWS_t`                                        | ambos         | Almacenamiento total de agua del mes `t`                         |
| `SPEI_01_t`, `SPEI_03_t`, `SPEI_06_t`, `SPEI_12_t` | ambos     | SPEI acumulado a 1, 3, 6 y 12 meses                              |
| `SOIL_MOISTURE_t`                              | ambos         | Humedad del suelo cercana a la superficie en el mes `t`          |
| `month_sin`, `month_cos`                       | ambos         | Codificación cíclica del mes, ya incluida por la organización    |
| `target`                                       | solo train    | Variable objetivo: TWS del mes calendario `t+1`                  |
| `TWS_t_masked`                                 | solo test     | Indicador booleano: `True` donde `TWS_t` fue enmascarado a propósito |

Todas las variables numéricas vienen **estandarizadas y son adimensionales**: no
están en centímetros de lámina de agua. Esto se verifica en el notebook.

## Verificación rápida

Una vez colocados los archivos, desde la raíz del proyecto:

```bash
python3 scripts/inspeccionar_datos.py
```

El script confirma que los archivos existen, reporta su tamaño y muestra las
columnas reales detectadas. **No modifica los archivos originales.**

## Regla importante

Estos archivos son de **solo lectura**. Todo producto derivado (muestras,
agregados, tablas) se escribe en `data/processed/`, nunca aquí.
