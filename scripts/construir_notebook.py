"""
Construye el notebook principal del Proyecto 2 a partir de celdas definidas en
este archivo. Se sigue el mismo patrón usado en los laboratorios anteriores del
curso: el notebook es un artefacto generado, de modo que se puede reconstruir y
volver a ejecutar de forma reproducible.

Uso (desde la raíz del proyecto):
    python3 scripts/construir_notebook.py
"""

from pathlib import Path

import nbformat as nbf

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "Proyecto2_Analisis_Exploratorio.ipynb"

celdas = []


def md(texto):
    celdas.append(nbf.v4.new_markdown_cell(texto.strip("\n")))


def code(texto):
    celdas.append(nbf.v4.new_code_cell(texto.strip("\n")))


# =============================================================================
# 1. Introducción
# =============================================================================
md(r"""
# Proyecto 2 — Análisis Exploratorio

**Curso:** CC3084 — Data Science · Universidad del Valle de Guatemala
**Semestre:** II — 2026

**Reto (Tema 3):** *A Step Ahead of Drought: Forecasting Global Water Storage Challenge*
organizado por la **ITU (International Telecommunication Union)** junto con agencias
del Sistema de Naciones Unidas, alojado en la plataforma Zindi.

**Categoría:** Series de tiempo con datos satelitales.

**Integrantes:**

1. ______________________________
2. ______________________________
3. ______________________________
4. ______________________________

---

## 1. Introducción

Este cuaderno desarrolla el análisis exploratorio de datos (EDA) del reto
*A Step Ahead of Drought*. El objetivo de esta etapa **no es construir el modelo
de pronóstico**, sino entender el fenómeno, la estructura del conjunto de datos y
los patrones que después permitirán plantear un modelo con criterio.

El documento está organizado de la siguiente manera. Las secciones 2 a 5 plantean
el problema: el contexto físico y satelital, la situación problemática que da
origen al reto, el problema científico y los objetivos. Las secciones 6 a 11
describen y preparan los datos. Las secciones 12 a 20 constituyen el análisis
exploratorio propiamente dicho, con énfasis en el comportamiento temporal por
tratarse de una serie de tiempo. Las secciones 21 a 23 resumen los hallazgos, las
conclusiones y los siguientes pasos.

### Nota sobre las fuentes

A lo largo del cuaderno se distingue de forma explícita entre dos tipos de
afirmación:

- **Evidencia del conjunto de datos.** Todo lo que se sostiene con una tabla, una
  estadística o una gráfica calculada en este mismo cuaderno.
- **Información externa.** Contexto tomado de la documentación oficial del reto o
  de literatura científica sobre GRACE, TWS y sequías. Aparece siempre con su
  referencia y se recopila en la sección de referencias.

Ninguna conclusión del análisis se apoya únicamente en información externa.
""")

# =============================================================================
# 2. Contexto del problema
# =============================================================================
md(r"""
## 2. Contexto del problema

Esta sección corresponde a la investigación previa solicitada en la guía del
proyecto. Su información proviene de fuentes externas —documentación del reto y
literatura científica— y sirve para saber **qué buscar** durante el análisis
exploratorio.

### 2.1 ¿Qué fenómeno se está estudiando?

Se estudia la variación temporal del **agua almacenada en los continentes** y su
relación con la aparición de condiciones de sequía. No se trata únicamente de la
lluvia: se trata del balance acumulado entre el agua que entra a un territorio y
el agua que sale de él.

### 2.2 ¿Qué significa *Global Water Storage* en este reto?

El reto trabaja con el **Total Water Storage (TWS)**, definido en la propia
descripción de la competencia como *todo el agua almacenada sobre y bajo la
superficie terrestre*, lo que incluye:

| Componente         | Descripción                                          |
| ------------------ | ---------------------------------------------------- |
| Agua subterránea   | Acuíferos                                            |
| Humedad del suelo  | Agua retenida en la zona no saturada                 |
| Agua superficial   | Ríos, lagos, embalses, humedales                     |
| Nieve y hielo      | Acumulación estacional y glaciares                   |

El TWS se mide como una **anomalía**: no es un volumen absoluto, sino la
desviación respecto a una línea base histórica, expresada habitualmente en
centímetros o milímetros de **lámina de agua equivalente**. Un valor negativo
indica que hay menos agua almacenada que en el periodo de referencia.

Esta característica es importante para el análisis: una variable de anomalía está
**centrada alrededor de cero por construcción**, y esa es una expectativa que el
EDA debe verificar en los datos reales en lugar de darla por sentada.

### 2.3 El papel de los datos satelitales

El TWS a escala global se obtiene de las misiones **GRACE** (*Gravity Recovery and
Climate Experiment*, 2002–2017) y **GRACE-FO** (*GRACE Follow-On*, desde 2018).
Estas misiones no observan el agua directamente: miden variaciones muy pequeñas
del **campo gravitatorio terrestre**. Como el agua tiene masa, un cambio en la
cantidad de agua almacenada en una región cambia localmente la gravedad, y de esa
señal se deriva el TWS.

Esto tiene tres consecuencias prácticas que condicionan el análisis:

1. **Resolución espacial gruesa.** El producto es representativo de escalas del
   orden de cientos de kilómetros, no de una parcela o una cuenca pequeña.
2. **Resolución temporal mensual.** La serie es mensual, no diaria.
3. **Es una medida integrada en profundidad.** Suma agua superficial y subterránea,
   por lo que responde con más inercia que la lluvia o la humedad superficial del
   suelo.

### 2.4 ¿Por qué importa anticipar las sequías?

La sequía es un fenómeno de instalación lenta: cuando resulta visible en los
cultivos, en los caudales o en los pozos, el déficit lleva meses acumulándose.
Disponer de una estimación anticipada del almacenamiento de agua permite tomar
decisiones —restricciones de riego, gestión de embalses, alertas tempranas—
mientras todavía tienen efecto.

El TWS es particularmente útil aquí porque, al integrar el agua subterránea,
detecta **sequía hidrológica**, que es la que afecta el abastecimiento y que los
indicadores de respuesta rápida no capturan por sí solos.

### 2.5 ¿Qué se intenta pronosticar y por qué es un problema de series de tiempo?

De acuerdo con la descripción oficial del reto, la tarea consiste en predecir el
**TWS del mes siguiente** (`t+1`) a partir de información disponible en el mes `t`.
La motivación es la **latencia**: los productos derivados de GRACE se publican
con un retraso de aproximadamente 2 a 3 meses, de modo que el estado hídrico
"actual" no se conoce cuando se necesita.

Es un problema de series de tiempo por tres razones:

- La variable objetivo está **indexada en el tiempo** con frecuencia mensual y
  ordenada; el orden de las observaciones tiene significado.
- Existe **dependencia temporal**: el almacenamiento de un mes está fuertemente
  condicionado por el del mes anterior, dado que el agua se acumula y se agota de
  forma gradual.
- Se espera **estacionalidad** ligada al ciclo anual de lluvias, deshielo y
  evapotranspiración.

Formalmente es un problema de **regresión supervisada sobre datos
espacio-temporales**: para cada celda geográfica y cada mes se predice un valor
continuo. La métrica de evaluación del reto es el **RMSE**.

### 2.6 Covariables consideradas en el reto

La documentación del reto indica que, además del propio TWS, el conjunto de datos
incorpora indicadores climáticos con menor latencia que sirven como covariables:

- **SPEI** (*Standardised Precipitation-Evapotranspiration Index*) en varias
  escalas de acumulación (1, 3, 6 y 12 meses). Es un índice estandarizado que
  combina precipitación y evapotranspiración potencial. Los valores negativos
  indican déficit hídrico. Las escalas cortas reflejan sequía meteorológica y
  agrícola; las escalas largas se aproximan más a la sequía hidrológica.
- **Humedad del suelo** cercana a la superficie, que responde con rapidez a la
  lluvia y a la demanda evaporativa.

La expectativa razonable —que el análisis debe **verificar, no asumir**— es que las
escalas largas del SPEI se asocien más al TWS que las escalas cortas, precisamente
por la inercia del almacenamiento subterráneo.

> Las columnas concretas, sus nombres y sus unidades se verifican directamente
> sobre los archivos en la sección 8. En este cuaderno no se describe ninguna
> variable que no se haya observado en los datos.
""")

# =============================================================================
# 3. Situación problemática
# =============================================================================
md(r"""
## 3. Situación problemática

El agua dulce disponible para los ecosistemas y para la actividad humana no está
distribuida de manera uniforme ni es constante en el tiempo. Su disponibilidad
depende del balance entre lo que se recibe por precipitación y lo que se pierde por
evapotranspiración y escorrentía, y ese balance se acumula durante meses o años en
el suelo, en los cuerpos de agua superficiales y en los acuíferos. Cuando el
balance permanece negativo durante un periodo prolongado, el resultado es una
**sequía hidrológica**: una reducción sostenida del agua efectivamente almacenada
en un territorio.

El problema práctico es que esta reducción **no se observa con facilidad**. La
lluvia se mide bien, pero la lluvia por sí sola no describe el estado del sistema:
una región puede recibir precipitación normal y seguir agotándose si la demanda
evaporativa es alta o si la extracción de agua subterránea excede la recarga.
Medir directamente el agua almacenada requeriría una red de observación
—piezómetros, aforos, sensores de humedad— que a escala global no existe con
cobertura ni homogeneidad suficientes.

Aquí es donde los **datos satelitales** cambian el planteamiento. Las misiones
GRACE y GRACE-FO permiten estimar el almacenamiento total de agua de forma
indirecta, a partir de las variaciones del campo gravitatorio terrestre, con
cobertura global y de manera consistente en el tiempo. Por primera vez se dispone
de una variable comparable entre regiones que integra agua superficial y
subterránea, y que resulta adecuada para caracterizar el estado hídrico de grandes
territorios.

Sin embargo, esta solución trae consigo una limitación operativa. Según la
descripción del reto, los productos derivados de GRACE se publican con un
**retraso de aproximadamente 2 a 3 meses**. Ese desfase es determinante: para
monitoreo y alerta temprana se necesita conocer el estado actual del sistema, y lo
que está disponible es el estado de hace un trimestre. La información existe, pero
llega tarde para sostener una decisión.

De ahí surge la dificultad que motiva el reto. Anticipar el almacenamiento futuro
de agua no es trivial por varias razones que el análisis exploratorio debe
examinar:

- El comportamiento del agua almacenada **no es homogéneo en el espacio**. Una
  región tropical, una zona árida, una cuenca dominada por deshielo y una región
  con fuerte extracción de agua subterránea responden de maneras distintas, de
  modo que un patrón global promedio puede ocultar dinámicas opuestas.
- La señal combina al menos tres componentes —**tendencia de largo plazo,
  estacionalidad anual y variabilidad interanual**— que se superponen y que
  conviene separar antes de modelar.
- Las covariables disponibles con baja latencia, como el SPEI y la humedad del
  suelo, describen sobre todo la parte superficial y de respuesta rápida del ciclo
  hidrológico, mientras que el TWS incluye componentes de respuesta lenta. Su
  capacidad de anticipar el TWS es, por tanto, una **pregunta empírica**.
- Los registros satelitales presentan **interrupciones y valores faltantes**. En
  particular, entre el fin de la misión GRACE y el inicio de GRACE-FO existe un
  hueco en la serie, y su presencia debe verificarse en los datos del reto porque
  condiciona qué se puede modelar y con qué evidencia.

El análisis exploratorio busca precisamente caracterizar estos elementos con
evidencia, en lugar de darlos por conocidos.
""")

# =============================================================================
# 4. Problema científico
# =============================================================================
md(r"""
## 4. Problema científico

> **¿Qué patrones temporales, estacionales y espaciales presenta la anomalía de
> almacenamiento total de agua (TWS) en el conjunto de datos del reto, y qué
> variables satelitales y climáticas disponibles en el mes actual muestran mayor
> asociación con el TWS del mes siguiente, de manera que puedan sustentar la
> construcción de un modelo de pronóstico a un mes de horizonte?**

La pregunta se puede responder con los datos disponibles porque cada uno de sus
componentes se traduce en un análisis concreto y verificable:

| Componente de la pregunta       | Cómo se responde                                                        |
| ------------------------------- | ----------------------------------------------------------------------- |
| Patrones temporales             | Serie agregada, medias móviles y comparación entre periodos (sección 16) |
| Patrones estacionales           | Perfil mensual, boxplots por mes y descomposición temporal (sección 17)  |
| Patrones espaciales             | Agregación por latitud y por región, y mapas de la rejilla (sección 18)  |
| Asociación entre variables      | Matriz de correlación y gráficos de dispersión (secciones 19 y 20)       |
| Utilidad para el pronóstico     | Asociación de la variable objetivo con el TWS actual y sus rezagos       |

Se trata de una pregunta **descriptiva y asociativa**, no causal. A lo largo del
cuaderno se habla de asociación o de correlación observada, nunca de causa: que
dos variables se muevan juntas no demuestra que una determine a la otra.
""")

# =============================================================================
# 5. Objetivos
# =============================================================================
md(r"""
## 5. Objetivos

### 5.1 Objetivo general

Caracterizar, mediante un análisis exploratorio reproducible, el comportamiento
temporal, estacional y espacial de la anomalía de almacenamiento total de agua
(TWS) y de sus covariables en el conjunto de datos del reto
*A Step Ahead of Drought*, con el fin de identificar los patrones y las variables
que sustenten la construcción posterior de un modelo de pronóstico a un mes de
horizonte.

### 5.2 Objetivos específicos

1. **Describir** la estructura del conjunto de datos: número de observaciones y de
   variables, tipo de cada una, cobertura temporal y cobertura espacial,
   documentando la clasificación de las variables en identificadores, temporales,
   geográficas, satelitales y objetivo.

2. **Evaluar** la calidad de los datos cuantificando valores faltantes,
   observaciones duplicadas y valores extremos, y determinando si su presencia
   responde a patrones temporales o espaciales antes de tomar cualquier decisión
   de tratamiento.

3. **Analizar** el comportamiento temporal de la variable objetivo mediante
   estadística descriptiva, medias móviles y descomposición de la serie, para
   determinar la existencia de tendencia, estacionalidad y periodos anómalos.

4. **Comparar** el comportamiento del almacenamiento de agua entre distintas
   ubicaciones geográficas, para determinar si el patrón temporal global es
   representativo o si oculta dinámicas regionales diferentes.

5. **Determinar** el grado de asociación entre la variable objetivo, el
   almacenamiento del mes actual y las covariables climáticas disponibles,
   utilizando matrices de correlación y gráficos de dispersión.

6. **Identificar** las variables, transformaciones y estructuras temporales
   candidatas a ser utilizadas en la etapa posterior de modelado, con base en la
   evidencia obtenida en los objetivos anteriores.

Los seis objetivos son medibles: cada uno se cierra con una tabla, una gráfica o
un estadístico concreto dentro del cuaderno, y en la sección 22 se retoma cada uno
para verificar que fue cumplido.
""")

# =============================================================================
# 6. Importación de librerías
# =============================================================================
md(r"""
## 6. Importación de librerías

Se utilizan las mismas librerías empleadas en los ejemplos y laboratorios del
curso: `pandas` y `numpy` para el manejo de datos, `matplotlib` y `seaborn` para
las visualizaciones, y `statsmodels` para la descomposición de la serie de tiempo
y la prueba de Dickey-Fuller, tal como se hizo en el ejemplo de series de tiempo
visto en clase. No se incorporan librerías adicionales que no aporten al análisis.
""")

code(r"""
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller

from IPython.display import display, Markdown

warnings.filterwarnings("ignore", category=FutureWarning)

# Opciones de despliegue: tablas legibles sin truncar columnas relevantes.
pd.set_option("display.max_columns", 40)
pd.set_option("display.width", 160)
pd.set_option("display.float_format", lambda x: f"{x:,.4f}")

# Estilo de gráficos consistente en todo el cuaderno.
plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams["figure.figsize"] = (13, 5)
plt.rcParams["figure.dpi"] = 110
plt.rcParams["savefig.dpi"] = 160
plt.rcParams["axes.titleweight"] = "bold"
plt.rcParams["axes.spines.top"] = False
plt.rcParams["axes.spines.right"] = False

# Semilla para que cualquier muestreo sea reproducible.
SEMILLA = 42
rng = np.random.default_rng(SEMILLA)

print(f"pandas      {pd.__version__}")
print(f"numpy       {np.__version__}")
print(f"matplotlib  {plt.matplotlib.__version__}")
print(f"seaborn     {sns.__version__}")
""")

code(r"""
# Rutas relativas al proyecto: el cuaderno se ejecuta desde la raíz del repositorio.
RAIZ = Path.cwd()
CRUDOS = RAIZ / "data" / "raw"
PROCESADOS = RAIZ / "data" / "processed"
FIGURAS = RAIZ / "figures"
TABLAS = RAIZ / "outputs" / "tablas"

for carpeta in (PROCESADOS, FIGURAS, TABLAS):
    carpeta.mkdir(parents=True, exist_ok=True)

print(f"Raíz del proyecto : {RAIZ}")
print(f"Datos crudos      : {CRUDOS.relative_to(RAIZ)}")
print(f"Figuras           : {FIGURAS.relative_to(RAIZ)}")


def guardar_figura(nombre):
    'Guarda la figura activa en figures/ para reutilizarla en informe y presentación.'
    plt.savefig(FIGURAS / f"{nombre}.png", bbox_inches="tight")
""")

# =============================================================================
# 7. Carga de datos
# =============================================================================
md(r"""
## 7. Carga de datos

Los archivos del reto se leen desde `data/raw/`. Son archivos grandes
—`Train.csv` pesa alrededor de 276 MB— por lo que antes de cargarlos se revisa
su tamaño y, una vez cargados, se reporta la memoria que ocupan. Si la huella de
memoria resulta excesiva se convierten las columnas de punto flotante a
`float32`, que para variables geofísicas conserva precisión más que suficiente y
reduce el consumo a la mitad.

Los archivos originales **no se modifican en ningún momento**: se leen y todo
producto derivado se guarda en `data/processed/`.
""")

code(r"""
ARCHIVOS = {
    "Train": CRUDOS / "Train.csv",
    "Test": CRUDOS / "Test.csv",
    "SampleSubmission": CRUDOS / "SampleSubmission.csv",
}

faltantes = [n for n, ruta in ARCHIVOS.items() if not ruta.exists()]
if faltantes:
    raise FileNotFoundError(
        "No se encontraron los archivos del reto: " + ", ".join(faltantes) + ".\n"
        "Descárguelos desde Zindi y colóquelos en data/raw/ "
        "siguiendo las instrucciones de data/raw/README.md."
    )

for nombre, ruta in ARCHIVOS.items():
    print(f"{nombre:18} {ruta.stat().st_size / 1024**2:8.1f} MB")
""")

code(r"""
# Lectura completa. Se mide el tiempo porque Train.csv es grande.
train = pd.read_csv(ARCHIVOS["Train"])
test = pd.read_csv(ARCHIVOS["Test"])
muestra_envio = pd.read_csv(ARCHIVOS["SampleSubmission"])

print(f"train             {train.shape[0]:>10,} filas x {train.shape[1]:>2} columnas")
print(f"test              {test.shape[0]:>10,} filas x {test.shape[1]:>2} columnas")
print(f"muestra_envio     {muestra_envio.shape[0]:>10,} filas x {muestra_envio.shape[1]:>2} columnas")
""")

code(r"""
# Huella de memoria antes de optimizar tipos.
def memoria_mb(df):
    return df.memory_usage(deep=True).sum() / 1024**2

print(f"Memoria train : {memoria_mb(train):8.1f} MB")
print(f"Memoria test  : {memoria_mb(test):8.1f} MB")

# Las variables geofísicas no requieren la precisión de float64.
columnas_float = train.select_dtypes("float64").columns
train[columnas_float] = train[columnas_float].astype("float32")
columnas_float_test = test.select_dtypes("float64").columns
test[columnas_float_test] = test[columnas_float_test].astype("float32")

print(f"\nDespués de convertir a float32:")
print(f"Memoria train : {memoria_mb(train):8.1f} MB")
print(f"Memoria test  : {memoria_mb(test):8.1f} MB")
""")

# =============================================================================
# 8. Descripción de los datasets
# =============================================================================
md(r"""
## 8. Descripción de los datasets

Esta sección documenta la estructura real de los archivos. Todo lo que se afirma
a partir de aquí proviene de los datos, no de la documentación del reto.
""")

code(r"""
print("Columnas de train:")
print(list(train.columns))
print("\nColumnas de test:")
print(list(test.columns))
print("\nColumnas de SampleSubmission:")
print(list(muestra_envio.columns))

# Diferencia de columnas: identifica cuál es la variable objetivo.
solo_en_train = [c for c in train.columns if c not in test.columns]
print(f"\nColumnas presentes en train pero no en test: {solo_en_train}")
""")

code(r"""
print("Primeras observaciones de train:")
display(train.head())

print("Últimas observaciones de train:")
display(train.tail())

print("Primeras observaciones de test:")
display(test.head())

print("Formato de entrega esperado:")
display(muestra_envio.head())
""")

code(r"""
print("Información general de train:")
train.info(memory_usage="deep")
""")

# =============================================================================
# 9. Identificación y clasificación de variables
# =============================================================================
md(r"""
## 9. Identificación y clasificación de variables

Antes de analizar es necesario decidir qué papel cumple cada columna. La
clasificación se hace sobre los nombres reales detectados en el archivo, no sobre
una lista escrita de antemano, de modo que si el reto publica una versión con
columnas distintas el cuaderno lo refleje en lugar de fallar en silencio.
""")

code(r"""
def clasificar_columnas(df):
    'Clasifica las columnas del dataset por su papel en el análisis.'
    roles = {
        "identificador": [],
        "fecha": [],
        "geografica": [],
        "objetivo": [],
        "satelital_tws": [],
        "climatica_spei": [],
        "climatica_suelo": [],
        "otra": [],
    }
    for col in df.columns:
        c = col.lower()
        if c in ("id",) or c.endswith("_id"):
            roles["identificador"].append(col)
        elif "date" in c or "fecha" in c or c in ("time", "month"):
            roles["fecha"].append(col)
        elif c.startswith("lat") or c.startswith("lon"):
            roles["geografica"].append(col)
        elif c == "target":
            roles["objetivo"].append(col)
        elif "tws" in c:
            roles["satelital_tws"].append(col)
        elif "spei" in c:
            roles["climatica_spei"].append(col)
        elif "soil" in c or "moisture" in c:
            roles["climatica_suelo"].append(col)
        else:
            roles["otra"].append(col)
    return roles


roles = clasificar_columnas(train)
for rol, columnas in roles.items():
    if columnas:
        print(f"{rol:18} -> {columnas}")

# Nombres canónicos que usa el resto del cuaderno.
COL_ID = roles["identificador"][0] if roles["identificador"] else None
COL_FECHA = roles["fecha"][0] if roles["fecha"] else None
COL_LAT = next((c for c in roles["geografica"] if c.lower().startswith("lat")), None)
COL_LON = next((c for c in roles["geografica"] if c.lower().startswith("lon")), None)
COL_OBJETIVO = roles["objetivo"][0] if roles["objetivo"] else solo_en_train[-1]
COL_TWS = roles["satelital_tws"][0] if roles["satelital_tws"] else None
COLS_SPEI = roles["climatica_spei"]
COL_SUELO = roles["climatica_suelo"][0] if roles["climatica_suelo"] else None

# Variables numéricas que se analizan estadísticamente.
COLS_NUMERICAS = [
    c for c in ([COL_TWS] + COLS_SPEI + [COL_SUELO, COL_OBJETIVO]) if c is not None
]

print(f"\nVariable objetivo    : {COL_OBJETIVO}")
print(f"Variables numéricas  : {COLS_NUMERICAS}")
""")

code(r"""
# Tabla resumen de variables solicitada en la guía del proyecto.
descripciones = {
    COL_ID: "Identificador único del registro (combina fecha y coordenadas).",
    COL_FECHA: "Mes de observación (variable temporal del registro).",
    COL_LAT: "Latitud del centro de la celda de la rejilla, en grados.",
    COL_LON: "Longitud del centro de la celda de la rejilla, en grados.",
    COL_TWS: "Almacenamiento total de agua del mes t (anomalía derivada de GRACE/GRACE-FO).",
    COL_SUELO: "Humedad del suelo cercana a la superficie en el mes t.",
    COL_OBJETIVO: "Variable objetivo: almacenamiento total de agua del mes t+1.",
}
for c in COLS_SPEI:
    descripciones[c] = "Índice SPEI (precipitación menos evapotranspiración potencial estandarizado)."

resumen_variables = pd.DataFrame({
    "Tipo": train.dtypes.astype(str),
    "Valores faltantes": train.isna().sum(),
    "% faltantes": (train.isna().mean() * 100).round(2),
    "Valores únicos": train.nunique(dropna=True),
})
resumen_variables["Descripción"] = [
    descripciones.get(c, "Variable presente en el archivo; su significado se documenta con evidencia del análisis.")
    for c in resumen_variables.index
]
resumen_variables.index.name = "Variable"
display(resumen_variables)

resumen_variables.to_csv(TABLAS / "resumen_variables.csv")
""")

# =============================================================================
# 10. Calidad de datos
# =============================================================================
md(r"""
## 10. Calidad de datos

Se cuantifican valores faltantes y duplicados **antes** de tomar cualquier
decisión. En datos satelitales un faltante rara vez es aleatorio: suele
corresponder a un periodo sin observación —como el hueco entre las misiones
GRACE y GRACE-FO— o a una región donde el producto no está definido. Por eso
interesa no solo cuánto falta, sino **dónde y cuándo** falta.
""")

code(r"""
calidad = pd.DataFrame({
    "faltantes": train.isna().sum(),
    "faltantes_%": (train.isna().mean() * 100).round(3),
    "n_unicos": train.nunique(dropna=True),
})
display(calidad)

print(f"Duplicados exactos en train : {train.duplicated().sum():,}")
if COL_ID is not None:
    print(f"Identificadores repetidos   : {train[COL_ID].duplicated().sum():,}")
claves = [c for c in (COL_FECHA, COL_LAT, COL_LON) if c is not None]
if claves:
    print(f"Duplicados por {claves}: {train.duplicated(subset=claves).sum():,}")
""")

# =============================================================================
# 11. Limpieza y preprocesamiento
# =============================================================================
md(r"""
## 11. Limpieza y preprocesamiento

La limpieza es **conservadora**. Se corrigen tipos y se construyen variables
derivadas de la fecha, pero no se eliminan observaciones ni se imputan valores
sin justificación. En datos climáticos, un valor extremo puede ser exactamente el
evento que interesa detectar.
""")

code(r"""
# Copia de trabajo: el DataFrame cargado del archivo original no se modifica.
df = train.copy()

# 1) Conversión de la fecha. El identificador tiene formato fecha_lat_lon,
#    por lo que la fecha puede reconstruirse desde ahí si hiciera falta.
if COL_FECHA is not None:
    df[COL_FECHA] = pd.to_datetime(df[COL_FECHA], errors="coerce")
elif COL_ID is not None:
    df["fecha"] = pd.to_datetime(df[COL_ID].str.split("_").str[0], format="%Y%m%d", errors="coerce")
    COL_FECHA = "fecha"

print(f"Columna de fecha: {COL_FECHA}")
print(f"Fechas no interpretables: {df[COL_FECHA].isna().sum():,}")
print(f"Rango temporal: {df[COL_FECHA].min().date()} a {df[COL_FECHA].max().date()}")
print(f"Meses únicos  : {df[COL_FECHA].nunique():,}")
""")

code(r"""
# 2) Variables derivadas del tiempo. Se crean solo las que el análisis usa.
df["anio"] = df[COL_FECHA].dt.year
df["mes"] = df[COL_FECHA].dt.month
df["trimestre"] = df[COL_FECHA].dt.quarter

# 3) Hemisferio: el ciclo estacional es opuesto al norte y al sur del ecuador,
#    de modo que promediar el planeta entero puede cancelar la estacionalidad.
df["hemisferio"] = np.where(df[COL_LAT] >= 0, "Norte", "Sur")

# 4) Banda de latitud: variable categórica para comparar regiones climáticas.
cortes = [-90, -60, -35, -23.5, 0, 23.5, 35, 60, 90]
etiquetas = ["Polar sur", "Templada sur", "Subtropical sur", "Tropical sur",
             "Tropical norte", "Subtropical norte", "Templada norte", "Polar norte"]
df["banda_latitud"] = pd.cut(df[COL_LAT], bins=cortes, labels=etiquetas, include_lowest=True)

# 5) Orden cronológico, indispensable en una serie de tiempo.
df = df.sort_values([COL_FECHA] + [c for c in (COL_LAT, COL_LON) if c]).reset_index(drop=True)

display(df[[COL_FECHA, "anio", "mes", "trimestre", "hemisferio", "banda_latitud"]].head())
""")

code(r"""
# Cobertura de la rejilla: cuántas celdas hay y con qué resolución.
n_celdas = df.groupby([COL_LAT, COL_LON], observed=True).ngroups
lats = np.sort(df[COL_LAT].unique())
lons = np.sort(df[COL_LON].unique())
paso_lat = np.diff(lats).min() if len(lats) > 1 else np.nan
paso_lon = np.diff(lons).min() if len(lons) > 1 else np.nan

print(f"Celdas únicas de la rejilla : {n_celdas:,}")
print(f"Latitudes únicas            : {len(lats):,}  (de {lats.min()} a {lats.max()})")
print(f"Longitudes únicas           : {len(lons):,}  (de {lons.min()} a {lons.max()})")
print(f"Paso mínimo en latitud      : {paso_lat}")
print(f"Paso mínimo en longitud     : {paso_lon}")

meses = df[COL_FECHA].nunique()
print(f"\nMeses en la serie           : {meses}")
print(f"Filas esperadas si la rejilla estuviera completa: {n_celdas * meses:,}")
print(f"Filas observadas                                : {len(df):,}")
""")

# =============================================================================
# 12. Estadística descriptiva
# =============================================================================
md(r"""
## 12. Estadística descriptiva

Se resumen las variables cuantitativas y se complementa `describe()` con el rango
y el rango intercuartílico, que la función no reporta por defecto. La comparación
entre media y mediana es especialmente informativa: una diferencia grande indica
asimetría.
""")

code(r"""
descriptivas = df[COLS_NUMERICAS].describe().T
descriptivas["mediana"] = df[COLS_NUMERICAS].median()
descriptivas["rango"] = descriptivas["max"] - descriptivas["min"]
descriptivas["IQR"] = descriptivas["75%"] - descriptivas["25%"]
descriptivas["asimetria"] = df[COLS_NUMERICAS].skew()
descriptivas = descriptivas[
    ["count", "mean", "mediana", "std", "min", "25%", "50%", "75%", "max", "rango", "IQR", "asimetria"]
]
display(descriptivas)

descriptivas.to_csv(TABLAS / "estadistica_descriptiva.csv")
""")

code(r"""
# Lectura automática de los rasgos principales, para no depender de la vista manual.
lineas = []
for col in COLS_NUMERICAS:
    media, mediana = df[col].mean(), df[col].median()
    sesgo = df[col].skew()
    forma = "simétrica" if abs(sesgo) < 0.5 else ("sesgada a la derecha" if sesgo > 0 else "sesgada a la izquierda")
    lineas.append(
        f"- **{col}**: media {media:,.3f}, mediana {mediana:,.3f}, "
        f"desviación {df[col].std():,.3f}, asimetría {sesgo:,.2f} → distribución {forma}."
    )

display(Markdown("**Resumen calculado sobre los datos:**\n\n" + "\n".join(lineas)))
""")

# =============================================================================
# 13. Análisis de variables categóricas
# =============================================================================
md(r"""
## 13. Análisis de variables categóricas

El conjunto de datos es esencialmente numérico: no incluye columnas de texto ni
categorías nominales. Sin embargo, el análisis exploratorio sí requiere variables
categóricas, y en este problema hay tres que son sustantivas y no artificiales:

1. **Mes y hemisferio**, que estructuran el ciclo estacional.
2. **Banda de latitud**, que agrupa las celdas en regímenes climáticos.
3. **Categoría de sequía según el SPEI**, que es la clasificación estándar del
   propio indicador y convierte una variable continua en una escala ordinal
   interpretable.

Para cada una se calculan tablas de frecuencia y de proporciones, y gráficos de
barras, tal como exige la rúbrica.
""")

code(r"""
# Frecuencias y proporciones por banda de latitud.
frec_banda = df["banda_latitud"].value_counts().sort_index()
prop_banda = df["banda_latitud"].value_counts(normalize=True).sort_index() * 100
tabla_banda = pd.DataFrame({"frecuencia": frec_banda, "proporción_%": prop_banda.round(2)})
display(tabla_banda)

fig, ax = plt.subplots(figsize=(12, 5))
ax.bar(tabla_banda.index.astype(str), tabla_banda["frecuencia"])
ax.set(title="Observaciones por banda de latitud",
       xlabel="Banda de latitud", ylabel="Número de observaciones")
ax.tick_params(axis="x", rotation=30)
guardar_figura("13_frecuencia_banda_latitud")
plt.show()
""")

code(r"""
# Frecuencias y proporciones por hemisferio.
tabla_hemisferio = pd.DataFrame({
    "frecuencia": df["hemisferio"].value_counts(),
    "proporción_%": (df["hemisferio"].value_counts(normalize=True) * 100).round(2),
})
display(tabla_hemisferio)

# Observaciones por año: verifica si la cobertura temporal es homogénea.
tabla_anio = pd.DataFrame({
    "frecuencia": df["anio"].value_counts().sort_index(),
    "proporción_%": (df["anio"].value_counts(normalize=True).sort_index() * 100).round(2),
})
display(tabla_anio)

fig, ax = plt.subplots(figsize=(13, 4))
ax.bar(tabla_anio.index.astype(str), tabla_anio["frecuencia"])
ax.set(title="Observaciones por año", xlabel="Año", ylabel="Número de observaciones")
guardar_figura("13_frecuencia_por_anio")
plt.show()
""")

code(r"""
# Categoría de sequía según la escala estándar del SPEI.
# Referencia: Vicente-Serrano et al., https://spei.csic.es
def categoria_spei(valor):
    if pd.isna(valor):
        return "Sin dato"
    if valor <= -2.0:
        return "Sequía extrema"
    if valor <= -1.5:
        return "Sequía severa"
    if valor <= -1.0:
        return "Sequía moderada"
    if valor < 1.0:
        return "Normal"
    if valor < 1.5:
        return "Húmedo moderado"
    if valor < 2.0:
        return "Húmedo severo"
    return "Húmedo extremo"


orden_categorias = ["Sequía extrema", "Sequía severa", "Sequía moderada", "Normal",
                    "Húmedo moderado", "Húmedo severo", "Húmedo extremo", "Sin dato"]

if COLS_SPEI:
    col_spei_ref = COLS_SPEI[0]
    df["categoria_sequia"] = df[col_spei_ref].map(categoria_spei)
    df["categoria_sequia"] = pd.Categorical(df["categoria_sequia"], categories=orden_categorias, ordered=True)

    tabla_sequia = pd.DataFrame({
        "frecuencia": df["categoria_sequia"].value_counts().reindex(orden_categorias),
        "proporción_%": (df["categoria_sequia"].value_counts(normalize=True).reindex(orden_categorias) * 100).round(2),
    }).dropna(how="all")
    display(tabla_sequia)

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(tabla_sequia.index.astype(str), tabla_sequia["frecuencia"])
    ax.set(title=f"Clasificación de condiciones según {col_spei_ref}",
           xlabel="Categoría", ylabel="Número de observaciones")
    ax.tick_params(axis="x", rotation=25)
    guardar_figura("13_categorias_sequia_spei")
    plt.show()
""")

# =============================================================================
# 14. Distribuciones
# =============================================================================
md(r"""
## 14. Distribuciones

Se examina la forma de cada variable numérica: dónde se concentra, qué tan
dispersa está, si es simétrica y si hay indicios de más de una población.
""")

code(r"""
n = len(COLS_NUMERICAS)
filas = int(np.ceil(n / 3))
fig, axes = plt.subplots(filas, 3, figsize=(16, 4 * filas))
axes = np.atleast_1d(axes).ravel()

for ax, col in zip(axes, COLS_NUMERICAS):
    datos = df[col].dropna()
    ax.hist(datos, bins=80)
    ax.axvline(datos.mean(), color="red", linestyle="--", linewidth=1.2, label=f"media {datos.mean():.2f}")
    ax.axvline(datos.median(), color="black", linestyle=":", linewidth=1.2, label=f"mediana {datos.median():.2f}")
    ax.set(title=f"Distribución de {col}", xlabel=col, ylabel="Frecuencia")
    ax.legend(fontsize=8)

for ax in axes[n:]:
    ax.axis("off")

plt.tight_layout()
guardar_figura("14_histogramas_variables")
plt.show()
""")

# =============================================================================
# 15. Detección y análisis de outliers
# =============================================================================
md(r"""
## 15. Detección y análisis de valores atípicos

Se identifican los valores extremos con el criterio del rango intercuartílico
(IQR), el mismo utilizado en los laboratorios del curso: se marca como atípico
todo valor fuera del intervalo $[Q_1 - 1.5\,IQR,\; Q_3 + 1.5\,IQR]$.

**Criterio adoptado: no se elimina ningún valor atípico.** En una variable que
mide anomalías de almacenamiento de agua, los valores extremos son precisamente
las sequías e inundaciones severas, es decir, el fenómeno que el modelo debe
aprender a anticipar. Eliminarlos destruiría la señal de interés. Los atípicos se
cuantifican, se localizan en el tiempo y en el espacio, y se documentan.
""")

code(r"""
resumen_atipicos = []
for col in COLS_NUMERICAS:
    q1, q3 = df[col].quantile([0.25, 0.75])
    iqr = q3 - q1
    inferior, superior = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    marca = (df[col] < inferior) | (df[col] > superior)
    resumen_atipicos.append({
        "variable": col,
        "Q1": q1, "Q3": q3, "IQR": iqr,
        "límite_inferior": inferior, "límite_superior": superior,
        "n_atípicos": int(marca.sum()),
        "%_atípicos": round(marca.mean() * 100, 2),
    })

tabla_atipicos = pd.DataFrame(resumen_atipicos).set_index("variable")
display(tabla_atipicos)
tabla_atipicos.to_csv(TABLAS / "outliers_iqr.csv")
""")

code(r"""
fig, ax = plt.subplots(figsize=(13, 5))
datos_box = [df[c].dropna().values for c in COLS_NUMERICAS]
ax.boxplot(datos_box, tick_labels=COLS_NUMERICAS, showfliers=True, flierprops={"markersize": 1, "alpha": 0.3})
ax.set(title="Diagramas de caja de las variables numéricas",
       xlabel="Variable", ylabel="Valor")
ax.tick_params(axis="x", rotation=20)
guardar_figura("15_boxplots_variables")
plt.show()
""")

code(r"""
# ¿Los valores extremos de la variable objetivo se concentran en algún periodo o región?
q1, q3 = df[COL_OBJETIVO].quantile([0.25, 0.75])
iqr = q3 - q1
extremos = df[(df[COL_OBJETIVO] < q1 - 1.5 * iqr) | (df[COL_OBJETIVO] > q3 + 1.5 * iqr)]

print(f"Observaciones atípicas en {COL_OBJETIVO}: {len(extremos):,} ({len(extremos)/len(df)*100:.2f}%)")

fig, axes = plt.subplots(1, 2, figsize=(16, 4.5))
por_anio = extremos["anio"].value_counts().sort_index()
axes[0].bar(por_anio.index.astype(str), por_anio.values)
axes[0].set(title="Valores atípicos por año", xlabel="Año", ylabel="Número de atípicos")

por_banda = extremos["banda_latitud"].value_counts().sort_index()
axes[1].bar(por_banda.index.astype(str), por_banda.values)
axes[1].set(title="Valores atípicos por banda de latitud", xlabel="Banda", ylabel="Número de atípicos")
axes[1].tick_params(axis="x", rotation=30)
plt.tight_layout()
guardar_figura("15_atipicos_tiempo_espacio")
plt.show()
""")

# =============================================================================
# 16. Análisis temporal
# =============================================================================
md(r"""
## 16. Análisis temporal

Esta es la sección central del análisis, por tratarse de un problema de series de
tiempo. Se construye una serie mensual agregando todas las celdas de la rejilla y
se estudia su tendencia, su variabilidad y sus periodos anómalos, siguiendo el
procedimiento del ejemplo de series de tiempo visto en clase.

Una advertencia metodológica: promediar el planeta completo mezcla el hemisferio
norte y el sur, cuyos ciclos estacionales están desfasados seis meses. Por eso,
además de la serie global, se construyen series por hemisferio.
""")

code(r"""
# Serie mensual global. Se compara el promedio simple con el promedio ponderado
# por el coseno de la latitud, que corrige el hecho de que las celdas cercanas a
# los polos representan menos área que las cercanas al ecuador.
serie_global = df.groupby(COL_FECHA)[COL_OBJETIVO].mean()

peso = np.cos(np.deg2rad(df[COL_LAT]))
serie_ponderada = (
    df.assign(_num=df[COL_OBJETIVO] * peso, _den=peso.where(df[COL_OBJETIVO].notna()))
      .groupby(COL_FECHA)[["_num", "_den"]].sum()
      .pipe(lambda t: t["_num"] / t["_den"])
)

fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(serie_global.index, serie_global.values, label="Promedio simple", linewidth=1.6)
ax.plot(serie_ponderada.index, serie_ponderada.values, label="Promedio ponderado por área", linewidth=1.2, alpha=0.8)
ax.set(title=f"Evolución mensual de {COL_OBJETIVO} (promedio global)",
       xlabel="Fecha", ylabel=COL_OBJETIVO)
ax.legend()
guardar_figura("16_serie_global")
plt.show()

print(f"Correlación entre ambas agregaciones: {serie_global.corr(serie_ponderada):.4f}")
""")

code(r"""
# Media y desviación móviles de 12 meses. La ventana es de 12 porque los datos
# son mensuales y el ciclo dominante esperado es anual: así la media móvil
# elimina la estacionalidad y deja ver la tendencia.
media_movil = serie_global.rolling(window=12, center=True).mean()
desv_movil = serie_global.rolling(window=12, center=True).std()

fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(serie_global.index, serie_global.values, color="steelblue", alpha=0.55, label="Serie observada")
ax.plot(media_movil.index, media_movil.values, color="firebrick", linewidth=2, label="Media móvil (12 meses)")
ax.plot(desv_movil.index, desv_movil.values, color="black", linewidth=1.2, linestyle="--",
        label="Desviación estándar móvil (12 meses)")
ax.set(title=f"{COL_OBJETIVO}: serie, media móvil y desviación móvil",
       xlabel="Fecha", ylabel=COL_OBJETIVO)
ax.legend()
guardar_figura("16_media_movil")
plt.show()
""")

code(r"""
# Series por hemisferio y promedio anual.
serie_hemisferio = df.pivot_table(index=COL_FECHA, columns="hemisferio", values=COL_OBJETIVO, aggfunc="mean")

fig, axes = plt.subplots(2, 1, figsize=(14, 9))
for columna in serie_hemisferio.columns:
    axes[0].plot(serie_hemisferio.index, serie_hemisferio[columna], label=f"Hemisferio {columna}")
axes[0].set(title=f"{COL_OBJETIVO} por hemisferio", xlabel="Fecha", ylabel=COL_OBJETIVO)
axes[0].legend()

promedio_anual = df.groupby("anio")[COL_OBJETIVO].mean()
axes[1].bar(promedio_anual.index.astype(str), promedio_anual.values)
axes[1].axhline(0, color="black", linewidth=0.8)
axes[1].set(title=f"Promedio anual de {COL_OBJETIVO}", xlabel="Año", ylabel=COL_OBJETIVO)

plt.tight_layout()
guardar_figura("16_hemisferios_y_anual")
plt.show()

display(promedio_anual.to_frame("promedio_anual"))
""")

# =============================================================================
# 17. Estacionalidad
# =============================================================================
md(r"""
## 17. Estacionalidad

Se investiga si la variable objetivo presenta un ciclo anual. Se usan tres
herramientas complementarias: el perfil mensual promedio, los diagramas de caja
por mes y la descomposición de la serie, esta última con la misma función
`seasonal_decompose` empleada en el ejemplo de clase.

En una descomposición aditiva la serie se separa en tres componentes:

- **Tendencia**: el movimiento de fondo, de largo plazo.
- **Estacionalidad**: el patrón que se repite con periodo fijo, aquí de 12 meses.
- **Residuo**: lo que no explican las dos anteriores; ahí quedan los eventos
  anómalos.
""")

code(r"""
nombres_mes = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
               "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

perfil_mensual = df.groupby(["hemisferio", "mes"])[COL_OBJETIVO].mean().unstack("hemisferio")

fig, axes = plt.subplots(1, 2, figsize=(16, 5))
for columna in perfil_mensual.columns:
    axes[0].plot(perfil_mensual.index, perfil_mensual[columna], marker="o", label=f"Hemisferio {columna}")
axes[0].plot(df.groupby("mes")[COL_OBJETIVO].mean(), marker="s", linestyle="--", color="gray", label="Global")
axes[0].set(title=f"Perfil estacional de {COL_OBJETIVO}", xlabel="Mes", ylabel=f"{COL_OBJETIVO} promedio")
axes[0].set_xticks(range(1, 13), nombres_mes)
axes[0].axhline(0, color="black", linewidth=0.8)
axes[0].legend()

datos_mes = [df.loc[df["mes"] == m, COL_OBJETIVO].dropna().values for m in range(1, 13)]
axes[1].boxplot(datos_mes, tick_labels=nombres_mes, showfliers=False)
axes[1].set(title=f"Distribución mensual de {COL_OBJETIVO}", xlabel="Mes", ylabel=COL_OBJETIVO)

plt.tight_layout()
guardar_figura("17_perfil_estacional")
plt.show()

display(perfil_mensual.round(4))
""")

code(r"""
# Descomposición de la serie global. Requiere una serie sin huecos y con
# frecuencia declarada.
serie_ts = serie_global.asfreq("MS")
print(f"Meses en la serie: {len(serie_ts)}   Faltantes: {serie_ts.isna().sum()}")

if serie_ts.isna().any():
    serie_ts = serie_ts.interpolate(method="time")
    print("Se interpolaron los meses faltantes únicamente para poder descomponer la serie.")

descomposicion = seasonal_decompose(serie_ts, model="additive", period=12)
fig = descomposicion.plot()
fig.set_size_inches(14, 9)
fig.suptitle(f"Descomposición aditiva de {COL_OBJETIVO} (periodo = 12 meses)", y=1.01)
plt.tight_layout()
guardar_figura("17_descomposicion")
plt.show()

# Magnitud relativa de cada componente.
var_total = serie_ts.var()
print(f"\nVarianza de la serie      : {var_total:.4f}")
print(f"Varianza de la tendencia  : {descomposicion.trend.var():.4f}")
print(f"Varianza estacional       : {descomposicion.seasonal.var():.4f}")
print(f"Varianza del residuo      : {descomposicion.resid.var():.4f}")
""")

code(r"""
# Prueba de Dickey-Fuller aumentada, igual que en el ejemplo de clase.
print("Resultados del Test de Dickey-Fuller para la serie global")
prueba = adfuller(serie_ts.dropna(), autolag="AIC")
salida = pd.Series(prueba[0:4],
                   index=["Estadístico de prueba", "p-value",
                          "# de retardos usados", "# de observaciones usadas"])
for clave, valor in prueba[4].items():
    salida[f"Valor crítico ({clave})"] = valor
display(salida.to_frame("valor"))

p_valor = prueba[1]
if p_valor < 0.05:
    veredicto = ("El p-value es menor a 0.05, por lo que se rechaza la hipótesis nula de raíz "
                 "unitaria: no hay evidencia de que la serie sea no estacionaria en media.")
else:
    veredicto = ("El p-value es mayor a 0.05, por lo que no se puede rechazar la hipótesis nula "
                 "de raíz unitaria: la serie no parece estacionaria en media.")
display(Markdown(f"**Interpretación.** {veredicto}"))
""")

# =============================================================================
# 18. Análisis espacial
# =============================================================================
md(r"""
## 18. Análisis espacial

El conjunto de datos es una rejilla global, de modo que cada observación tiene
coordenadas. Esto permite responder una pregunta que el promedio global no puede:
¿el comportamiento temporal es parecido en todas partes, o hay regiones que se
mueven en sentido contrario?

Se construyen mapas sencillos reorganizando la rejilla con `pivot_table` y
dibujándola con `imshow`, el mismo recurso usado en los ejemplos de datos
satelitales del curso.
""")

code(r"""
def mapa(valores, titulo, etiqueta, cmap="BrBG", simetrico=True):
    'Dibuja una rejilla lat-lon como mapa. valores: DataFrame indexado por lat y lon.'
    rejilla = valores.pivot_table(index=COL_LAT, columns=COL_LON, values=valores.columns[-1])
    fig, ax = plt.subplots(figsize=(15, 7))
    limite = np.nanpercentile(np.abs(rejilla.values), 98) if simetrico else None
    im = ax.imshow(
        rejilla.values,
        extent=[rejilla.columns.min(), rejilla.columns.max(),
                rejilla.index.min(), rejilla.index.max()],
        origin="lower", aspect="auto", cmap=cmap,
        vmin=-limite if simetrico else None,
        vmax=limite if simetrico else None,
    )
    ax.set(title=titulo, xlabel="Longitud (grados)", ylabel="Latitud (grados)")
    fig.colorbar(im, ax=ax, label=etiqueta)
    return fig, ax


promedio_celda = (
    df.groupby([COL_LAT, COL_LON], observed=True)[COL_OBJETIVO]
      .mean().reset_index()
)
mapa(promedio_celda, f"Promedio de {COL_OBJETIVO} por celda de la rejilla", COL_OBJETIVO)
guardar_figura("18_mapa_promedio")
plt.show()
""")

code(r"""
# Variabilidad: dónde el almacenamiento oscila más a lo largo del periodo.
desviacion_celda = (
    df.groupby([COL_LAT, COL_LON], observed=True)[COL_OBJETIVO]
      .std().reset_index()
)
mapa(desviacion_celda, f"Desviación estándar de {COL_OBJETIVO} por celda",
     "Desviación estándar", cmap="viridis", simetrico=False)
guardar_figura("18_mapa_variabilidad")
plt.show()
""")

code(r"""
# Cobertura: qué fracción de meses tiene dato en cada celda.
cobertura_celda = (
    df.groupby([COL_LAT, COL_LON], observed=True)[COL_OBJETIVO]
      .apply(lambda s: s.notna().mean() * 100).reset_index()
)
mapa(cobertura_celda, "Porcentaje de meses con dato disponible por celda",
     "% de meses con dato", cmap="viridis", simetrico=False)
guardar_figura("18_mapa_cobertura")
plt.show()
""")

code(r"""
# Comparación de la evolución temporal entre bandas de latitud.
series_banda = df.pivot_table(index=COL_FECHA, columns="banda_latitud",
                              values=COL_OBJETIVO, aggfunc="mean", observed=True)

fig, ax = plt.subplots(figsize=(14, 6))
for columna in series_banda.columns:
    ax.plot(series_banda.index, series_banda[columna], label=str(columna), linewidth=1.3)
ax.axhline(0, color="black", linewidth=0.8)
ax.set(title=f"Evolución de {COL_OBJETIVO} por banda de latitud",
       xlabel="Fecha", ylabel=f"{COL_OBJETIVO} promedio")
ax.legend(ncol=3, fontsize=9)
guardar_figura("18_series_por_banda")
plt.show()

resumen_banda = df.groupby("banda_latitud", observed=True)[COL_OBJETIVO].agg(
    observaciones="count", media="mean", mediana="median", desviacion="std",
    minimo="min", maximo="max"
)
display(resumen_banda)
resumen_banda.to_csv(TABLAS / "resumen_por_banda_latitud.csv")
""")

# =============================================================================
# 19. Correlaciones
# =============================================================================
md(r"""
## 19. Correlaciones

Se calcula la matriz de correlación de **Pearson**, apropiada porque las
variables son continuas y el interés está en relaciones lineales. Se acompaña con
la correlación de **Spearman**, que al basarse en rangos detecta relaciones
monótonas aunque no sean lineales; la comparación entre ambas indica si alguna
relación importante es no lineal.

> A lo largo de esta sección se habla de **asociación**, nunca de causa. Que dos
> variables se muevan juntas no demuestra que una determine a la otra.
""")

code(r"""
correlacion_pearson = df[COLS_NUMERICAS].corr(method="pearson")

fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(correlacion_pearson, annot=True, fmt=".2f", cmap="RdBu_r",
            vmin=-1, vmax=1, center=0, square=True,
            cbar_kws={"label": "Correlación de Pearson"}, ax=ax)
ax.set(title="Matriz de correlación de Pearson")
guardar_figura("19_matriz_correlacion")
plt.show()

correlacion_pearson.to_csv(TABLAS / "correlacion_pearson.csv")
""")

code(r"""
# Muestra para Spearman: sobre 2 millones de filas el cálculo por rangos es lento
# y una muestra aleatoria grande da una estimación equivalente.
muestra = df.sample(n=min(200_000, len(df)), random_state=SEMILLA)
correlacion_spearman = muestra[COLS_NUMERICAS].corr(method="spearman")

comparacion = pd.DataFrame({
    "Pearson": correlacion_pearson[COL_OBJETIVO],
    "Spearman": correlacion_spearman[COL_OBJETIVO],
}).drop(index=COL_OBJETIVO)
comparacion["diferencia"] = (comparacion["Spearman"] - comparacion["Pearson"]).round(3)
comparacion = comparacion.reindex(comparacion["Pearson"].abs().sort_values(ascending=False).index)
display(comparacion.round(4))

display(Markdown(
    "**Lectura.** La columna `diferencia` señala qué relaciones cambian al pasar de "
    "Pearson a Spearman: una diferencia grande sugiere que la asociación existe pero "
    "no es lineal."
))
""")

code(r"""
# Asociación de la variable objetivo con el almacenamiento del mes actual.
# Es la relación más importante del problema: mide cuánta inercia tiene la serie.
if COL_TWS is not None:
    correlacion_persistencia = df[[COL_TWS, COL_OBJETIVO]].corr().iloc[0, 1]
    print(f"Correlación entre {COL_TWS} (mes t) y {COL_OBJETIVO} (mes t+1): {correlacion_persistencia:.4f}")

    # La misma relación calculada dentro de cada banda de latitud.
    por_banda = (
        df.groupby("banda_latitud", observed=True)[[COL_TWS, COL_OBJETIVO]]
          .corr().iloc[0::2, 1].reset_index(level=1, drop=True)
          .rename(f"corr({COL_TWS}, {COL_OBJETIVO})")
    )
    display(por_banda.to_frame().round(4))
""")

# =============================================================================
# 20. Cruces de variables
# =============================================================================
md(r"""
## 20. Cruces de variables

Se seleccionan los cruces que responden preguntas concretas del problema, en
lugar de generar todas las combinaciones posibles. Como el conjunto tiene más de
dos millones de filas, los gráficos de dispersión se construyen sobre una muestra
aleatoria con semilla fija, que preserva la forma de la relación y mantiene la
figura legible.
""")

code(r"""
muestra_grafica = df.sample(n=min(30_000, len(df)), random_state=SEMILLA)

pares = []
if COL_TWS is not None:
    pares.append((COL_TWS, COL_OBJETIVO, "Persistencia: almacenamiento en t frente a t+1"))
if COL_SUELO is not None:
    pares.append((COL_SUELO, COL_OBJETIVO, "Humedad del suelo frente al almacenamiento en t+1"))
for c in COLS_SPEI[:2]:
    pares.append((c, COL_OBJETIVO, f"{c} frente al almacenamiento en t+1"))

filas = int(np.ceil(len(pares) / 2))
fig, axes = plt.subplots(filas, 2, figsize=(15, 5.5 * filas))
axes = np.atleast_1d(axes).ravel()

for ax, (x, y, titulo) in zip(axes, pares):
    ax.scatter(muestra_grafica[x], muestra_grafica[y], s=3, alpha=0.15)
    r = df[[x, y]].corr().iloc[0, 1]
    ax.set(title=f"{titulo}\n(r de Pearson = {r:.3f})", xlabel=x, ylabel=y)

for ax in axes[len(pares):]:
    ax.axis("off")

plt.tight_layout()
guardar_figura("20_dispersion_objetivo")
plt.show()
""")

code(r"""
# Cruce mes x banda de latitud: dónde y cuándo el almacenamiento es más bajo.
tabla_cruce = df.pivot_table(index="banda_latitud", columns="mes",
                             values=COL_OBJETIVO, aggfunc="mean", observed=True)
tabla_cruce.columns = nombres_mes[:len(tabla_cruce.columns)]

fig, ax = plt.subplots(figsize=(13, 5))
limite = np.nanpercentile(np.abs(tabla_cruce.values), 98)
sns.heatmap(tabla_cruce, annot=True, fmt=".2f", cmap="BrBG", center=0,
            vmin=-limite, vmax=limite, cbar_kws={"label": COL_OBJETIVO}, ax=ax)
ax.set(title=f"{COL_OBJETIVO} promedio por banda de latitud y mes",
       xlabel="Mes", ylabel="Banda de latitud")
guardar_figura("20_cruce_banda_mes")
plt.show()

display(tabla_cruce.round(3))
""")

code(r"""
# Relación entre categoría de sequía del SPEI y el almacenamiento del mes siguiente.
if COLS_SPEI:
    resumen_categoria = (
        df.groupby("categoria_sequia", observed=True)[COL_OBJETIVO]
          .agg(observaciones="count", media="mean", mediana="median", desviacion="std")
          .reindex(orden_categorias).dropna(how="all")
    )
    display(resumen_categoria)

    fig, ax = plt.subplots(figsize=(13, 5))
    categorias_presentes = [c for c in orden_categorias if c in df["categoria_sequia"].unique()]
    datos_cat = [df.loc[df["categoria_sequia"] == c, COL_OBJETIVO].dropna().values
                 for c in categorias_presentes]
    ax.boxplot(datos_cat, tick_labels=categorias_presentes, showfliers=False)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set(title=f"{COL_OBJETIVO} según la categoría de sequía del mes actual ({col_spei_ref})",
           xlabel="Categoría de sequía", ylabel=COL_OBJETIVO)
    ax.tick_params(axis="x", rotation=25)
    guardar_figura("20_objetivo_por_categoria_sequia")
    plt.show()
""")

# =============================================================================
# 21. Hallazgos principales
# =============================================================================
md(r"""
## 21. Hallazgos principales

Cada hallazgo de esta sección remite a la tabla, la estadística o la figura que lo
respalda. La celda siguiente recopila las cifras clave calculadas en el cuaderno
para que el resumen escrito se apoye en valores verificables.
""")

code(r"""
resumen_final = {
    "Observaciones en train": f"{len(train):,}",
    "Observaciones en test": f"{len(test):,}",
    "Variables en train": train.shape[1],
    "Rango temporal": f"{df[COL_FECHA].min().date()} a {df[COL_FECHA].max().date()}",
    "Meses cubiertos": df[COL_FECHA].nunique(),
    "Celdas de la rejilla": f"{n_celdas:,}",
    "Faltantes en la variable objetivo": f"{df[COL_OBJETIVO].isna().mean()*100:.2f}%",
    "Duplicados exactos": f"{train.duplicated().sum():,}",
    f"Media de {COL_OBJETIVO}": f"{df[COL_OBJETIVO].mean():.4f}",
    f"Desviación de {COL_OBJETIVO}": f"{df[COL_OBJETIVO].std():.4f}",
    "Atípicos por IQR en la objetivo": f"{tabla_atipicos.loc[COL_OBJETIVO, '%_atípicos']:.2f}%",
    "p-value Dickey-Fuller": f"{p_valor:.5f}",
}
if COL_TWS is not None:
    resumen_final[f"corr({COL_TWS}, {COL_OBJETIVO})"] = f"{correlacion_persistencia:.4f}"

tabla_resumen = pd.DataFrame.from_dict(resumen_final, orient="index", columns=["Valor"])
tabla_resumen.index.name = "Indicador"
display(tabla_resumen)
tabla_resumen.to_csv(TABLAS / "resumen_hallazgos.csv")
""")

# =============================================================================
# 22. Conclusiones y 23. Próximos pasos
# =============================================================================
md(r"""
## 22. Conclusiones

*(Esta sección se redacta a partir de los resultados obtenidos al ejecutar el
cuaderno con los datos reales; cada conclusión se conecta con el objetivo
específico correspondiente de la sección 5.2.)*

## 23. Próximos pasos

*(Se completa junto con las conclusiones.)*

## Referencias

- Zindi / ITU. *A Step Ahead of Drought: Forecasting Global Water Storage Challenge.*
  <https://zindi.world/competitions/one-step-ahead-of-drought-forecasting-global-water-storage-challenge>
- Copernicus European Drought Observatory. *GRACE Total Water Storage (TWS) Anomaly — Factsheet.*
  <https://drought.emergency.copernicus.eu/data/factsheets/factsheet_grace_tws_anomaly.pdf>
- Vicente-Serrano, S. M., Beguería, S. y López-Moreno, J. I. *SPEI: The Standardised
  Precipitation-Evapotranspiration Index.* <https://spei.csic.es/home.html>
- Material del curso CC3084: *Ejemplo series de tiempo LSTM*, *Practica01 Incendios*
  y *EjemploGIS Sentinel2*.
""")

# =============================================================================
# Ensamblado
# =============================================================================
nb = nbf.v4.new_notebook()
nb["cells"] = celdas
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
}

nbf.write(nb, DESTINO)
print(f"Notebook escrito: {DESTINO.name}  ({len(celdas)} celdas)")
