# Revisión bibliográfica y selección preliminar de modelos

## Pronóstico del almacenamiento total de agua con datos de GRACE

**Proyecto 2 | CC3084 - Data Science**

Universidad del Valle de Guatemala · Facultad de Ingeniería

Semestre II de 2026 · 11 de octubre de 2026

Reto: *A Step Ahead of Drought: Forecasting Global Water Storage Challenge by ITU*

### Resumen

Este documento revisa nueve artículos de revistas indexadas: siete aplicaciones al almacenamiento total de agua y dos fundamentos metodológicos. La literatura incluye perceptrones multicapa, regresión lineal, SARIMAX, bosques aleatorios, árboles con boosting, redes LSTM, variantes bidireccionales con atención y redes convolucionales bayesianas. Se distingue la reconstrucción de observaciones faltantes del pronóstico hacia meses futuros, porque sus resultados no son equivalentes.

Para el proyecto se propone comparar Random Forest y XGBoost como candidatos tabulares principales, una LSTM unidireccional como alternativa secuencial y regresión Ridge como referencia interpretable. Se añadirán líneas base de persistencia y climatología. La elección considera la memoria hidrológica, los meses ausentes, la cobertura espacial y el enmascaramiento de aproximadamente dos tercios del TWS actual en el conjunto de prueba. La evaluación deberá reproducir esa disponibilidad de información y respetar el orden temporal. La selección es preliminar: este informe no presenta modelos entrenados ni resultados experimentales nuevos.

**Palabras clave:** almacenamiento total de agua, GRACE, pronóstico, aprendizaje automático, sequía, validación temporal.

### Organización

Problema y búsqueda bibliográfica (p. 2); antecedentes y síntesis crítica (pp. 3-5); selección y evaluación propuestas (pp. 6-8); referencias APA 7 (pp. 9-10); verificación de indexación (p. 11).

<!-- pagebreak -->

# 1. Problema y alcance de la revisión

### 1.1 Problema específico del proyecto

Se busca estimar `target`, el TWS del mes calendario `t+1`, usando información disponible hasta `t`. El reto se motiva por la latencia de los productos GRACE. Su descripción oficial aclara que, cuando el TWS actual está oculto, el horizonte efectivo desde la última observación de TWS puede ser de 1 a 7 meses. Por ello, el objetivo estadístico sigue siendo `t+1`, pero la antigüedad del estado hídrico observado varía entre muestras (Zindi, s. f.).

El análisis exploratorio local registra 2 154 021 filas de entrenamiento, 15 715 celdas y 138 meses observados entre mayo de 2002 y agosto de 2015. Faltan 22 meses del calendario. Las variables hidrológicas y el objetivo se manejan en la escala adimensional entregada por el reto. Las entradas incluyen TWS actual, SPEI de 1, 3, 6 y 12 meses, humedad del suelo y codificación cíclica del mes (*Proyecto 2: Análisis exploratorio*, 2026).

El mismo análisis reporta una correlación de 0.803 entre TWS actual y objetivo, y RMSE de persistencia de 0.5724. Este último es un resultado descriptivo sobre entrenamiento con TWS observado: no constituye un resultado de validación ni un umbral directamente comparable con muestras enmascaradas. También identifica diferencias regionales y una participación del hemisferio norte de 80.3 %, que exige revisar el desempeño por región.

### 1.2 Estrategia de búsqueda y selección

Se realizó una revisión narrativa dirigida, con consulta hasta el 11 de octubre de 2026. Se buscaron combinaciones de *GRACE*, *terrestrial water storage*, *forecasting*, *reconstruction*, *random forest*, *gradient boosting*, *LSTM* y *Bayesian convolutional neural network*. La búsqueda utilizó páginas editoriales, DOI y repositorios institucionales de los autores; los metadatos se contrastaron con Crossref. No se presenta como revisión sistemática exhaustiva ni como búsqueda ejecutada dentro de Scopus.

Se incluyeron artículos publicados en revistas indexadas que modelan TWS/TWSA de GRACE mediante aprendizaje automático y artículos metodológicos pertinentes para bosques aleatorios y validación. Se excluyeron prepublicaciones sin versión de revista, tesis, notas divulgativas y estudios de precipitación o caudal sin conexión directa con el problema. Se priorizó diversidad de familias, escala global o regional y evidencia de pronóstico. El corpus final contiene nueve artículos, publicados entre 2001 y 2026; la indexación se documenta en el anexo.

Para cada estudio se identificaron tarea, datos, modelos, resultados reportados y límites de transferencia. TWSA denota anomalías de almacenamiento respecto de una referencia; es la variable habitualmente modelada en los artículos, aunque el reto denomine TWS a su objetivo estandarizado.

<!-- pagebreak -->

# 2. Antecedentes: modelos tabulares

### 2.1 Perceptrones multicapa para extender registros

Long et al. (2014) emplearon redes neuronales artificiales para extender las anomalías de almacenamiento en la meseta Yun-Gui, en China, y estudiar sequías e inundaciones. Los coeficientes de determinación reportados fueron 0.91 para la meseta y 0.83, 0.76 y 0.57 para tres subregiones. La variación territorial muestra que un modelo útil a escala agregada puede perder precisión local. El trabajo respalda aprender relaciones no lineales entre condiciones hidrológicas y TWS. Su tarea principal es reconstruir el pasado, por lo que esos valores no prueban precisión futura a un mes en una rejilla global.

### 2.2 Redes profundas, regresión lineal y SARIMAX

Z. Sun et al. (2020) compararon una red neuronal profunda, regresión lineal múltiple y SARIMAX para reconstruir GRACE con seis soluciones satelitales, evaluadas también en 60 cuencas. La red profunda superó ligeramente a SARIMAX y de forma más clara a la regresión lineal en la mayoría de las cuencas. El desempeño fue favorable en zonas húmedas con poca intervención humana. Este antecedente justifica conservar una referencia lineal y evaluar memoria temporal y no linealidad. Advierte, además, que el producto satelital y el régimen hidrológico afectan los resultados: la complejidad del algoritmo por sí sola no asegura una mejora generalizable.

### 2.3 Bosques, boosting y comparación de familias

A. Y. Sun et al. (2021) reconstruyeron TWS en Estados Unidos mediante un flujo AutoML que comparó, entre otras familias, modelos lineales, redes profundas, Random Forest, GBM y XGBoost. En prueba, el resumen del artículo reporta NSE medio cercano a 0.85 y RMSE normalizado cercano a 0.09. Ningún algoritmo dominó en todo el territorio. La lección para este proyecto es comparar explícitamente varias familias y examinar diferencias regionales. El flujo AutoML del artículo no se adoptará, pues las reglas del reto lo prohíben; se tomarán como antecedentes los algoritmos evaluados.

Random Forest combina árboles con aleatoriedad en las muestras y en la selección de variables, y agrega sus predicciones; su formulación también cubre regresión (Breiman, 2001). Para este proyecto resulta razonable contrastar ese promedio de árboles con boosting, que construye una secuencia de árboles para mejorar progresivamente la predicción. Ambas familias pueden trabajar con covariables y rezagos expresados como columnas.

### 2.4 Implicación para los datos disponibles

Los modelos tabulares permiten empezar con las variables entregadas y agregar historia solo cuando esté disponible en la fecha de predicción. Una hipótesis del proyecto es que la combinación de SPEI en varias escalas y humedad del suelo retenga parte de la memoria hídrica cuando falte TWS. Esto deberá comprobarse mediante una comparación con y sin esas variables. Las correlaciones exploratorias no demuestran que una relación sea lineal, causal o estable fuera del periodo observado.

<!-- pagebreak -->

# 3. Antecedentes: arquitecturas neuronales

### 3.1 LSTM y BiLSTM con atención

Lu et al. (2024) compararon retropropagación mejorada, LSTM y BiLSTM con atención en seis regiones de China, frente a mínimos cuadrados y Random Forest. Usaron entrenamiento hasta agosto de 2019 y prueba de septiembre de 2019 a mayo de 2023. En dos regiones reportaron RMSE inferior a 2.641 cm y R² de al menos 0.8. Sus series estaban completadas previamente; las diferencias regionales y las unidades físicas limitan transferir estos resultados al reto.

Una LSTM mantiene memoria mediante compuertas; BiLSTM procesa la ventana en ambos sentidos y la atención pondera representaciones. La ventana de pronóstico debe terminar en `t`: recorrer historia en reversa no implica fuga, pero incorporar observaciones posteriores sí.

### 3.2 Reconstrucción global con redes recurrentes

Palazzoli et al. (2025) presentaron GRAiCE: cuatro reconstrucciones mensuales globales de TWSA, de 1984 a 2021, con rejilla de 0.5°. Compararon LSTM y BiLSTM con cinco predictores meteorológicos, con y sin fluorescencia inducida por el Sol como indicador de vegetación. El diseño permite estudiar arquitectura y conjunto de entradas por separado. La correlación global de 0.97 reportada para BiLSTM incluye entrenamiento y prueba, y corresponde al promedio espacial; no debe interpretarse como precisión independiente por celda. El estudio apoya secuencias de covariables como alternativa cuando no existe una observación contemporánea de TWS.

### 3.3 Convoluciones bayesianas para faltantes espaciales

Mo et al. (2022) propusieron una CNN bayesiana para completar el intervalo entre GRACE y GRACE-FO a escala global. La arquitectura incorpora conexiones residuales y atención espacial y por canales; el enfoque bayesiano estima incertidumbre predictiva. Reportaron mejoras frente a productos de reconstrucción previos, especialmente en regiones relativamente áridas. Su aporte es explotar campos espaciales completos. Para trasladarlo al proyecto habría que reorganizar las filas en mapas, tratar la máscara terrestre y demostrar una mejora que compense el costo. Completar un periodo con forzantes disponibles retrospectivamente difiere de emitir un pronóstico operativo.

### 3.4 Lectura para la selección preliminar

Se prioriza una LSTM pequeña como primera prueba secuencial. Las variantes bidireccionales, con atención y convolucionales se reservan para una ampliación: con solo 138 fechas observadas, las millones de filas no representan millones de periodos independientes. Incrementar parámetros requiere evidencia adicional de generalización.

<!-- pagebreak -->

# 4. Evidencia de pronóstico y síntesis crítica

### 4.1 Pronóstico global con información pasada

Li y Kusche (2026) desarrollaron pronósticos globales de cambios de TWS con resolución de 1° y horizontes de hasta 12 meses. Separaron tendencia y estacionalidad de la componente no estacional, modelada mediante LSTM y predictores hidrometeorológicos rezagados. Evaluaron retrospectivamente el periodo 2010-2024 y reportaron mejoras frente a SEAS5 de ECMWF. Es el antecedente más próximo al objetivo del proyecto por su escala, rejilla y emisión hacia el futuro. Suponían continuidad de tendencia y ciclos; esos supuestos deben comprobarse aquí. La descomposición es una opción a contrastar, siempre estimada exclusivamente con el tramo de entrenamiento.

### 4.2 Comparación de los siete antecedentes aplicados

**Tabla 1. Tareas y aportes transferibles al proyecto**

| Estudio | Tarea y alcance | Modelos estudiados | Aporte a la propuesta |
| --- | --- | --- | --- |
| Long et al. (2014) | Reconstrucción regional | ANN/MLP | Referencia no lineal y evaluación territorial. |
| Z. Sun et al. (2020) | Reconstrucción global y por cuencas | DNN, MLR, SARIMAX | Comparar complejidad y memoria temporal. |
| A. Y. Sun et al. (2021) | Reconstrucción en Estados Unidos | RF, GBM, XGBoost, DNN, modelos lineales | Comparar familias sin asumir un ganador universal. |
| Mo et al. (2022) | Completar el intervalo entre misiones | CNN bayesiana y atención | Alternativa espacial con incertidumbre. |
| Lu et al. (2024) | Predicción regional de series TWSA | BP, LSTM, BiLSTM-atención; RF | Contrastar arquitecturas con una partición temporal. |
| Palazzoli et al. (2025) | Reconstrucción global | LSTM/BiLSTM con y sin vegetación | Separar el efecto de arquitectura y entradas. |
| Li y Kusche (2026) | Pronóstico global de 1 a 12 meses | Descomposición y LSTM | Referente directo para emisión futura. |

*Nota.* ANN: red neuronal artificial; MLP: perceptrón multicapa; DNN: red neuronal profunda; MLR: regresión lineal múltiple; RF: Random Forest; GBM: gradient boosting machine; BP: retropropagación. Elaboración propia a partir de los estudios citados.

### 4.3 Qué se puede concluir

La evidencia respalda una comparación que abarque modelos tabulares y recurrentes. No permite ordenar todos los algoritmos por precisión: cambian regiones, entradas, fechas, objetivos y métricas. El RMSE normalizado, el RMSE en centímetros y la correlación de un promedio global responden a evaluaciones distintas. Para el reto, todos los candidatos deberán medirse sobre las mismas filas, en la escala del objetivo y bajo idénticas máscaras de disponibilidad.

<!-- pagebreak -->

# 5. Selección preliminar de algoritmos

### 5.1 Random Forest: candidato tabular de comparación

Se considera por su capacidad para modelar interacciones entre SPEI, humedad y estacionalidad, con una preparación de datos relativamente sencilla. La evidencia aplicada de A. Y. Sun et al. (2021) y su fundamento en Breiman (2001) sustentan su inclusión. Se propone comenzar con 300 árboles, profundidad máxima de 12 o 20 y mínimos de 20 o 100 muestras por hoja; son configuraciones iniciales del proyecto, no óptimos tomados de los artículos. Se controlará memoria y tiempo. La extrapolación de tendencias y la atenuación de extremos son limitaciones que se revisarán.

### 5.2 XGBoost: candidato tabular prioritario

Se selecciona como implementación de árboles con boosting, con antecedente directo en TWS en A. Y. Sun et al. (2021). La hipótesis es que mejore la combinación de señales débiles y relaciones no lineales cuando falte TWS. Se propone profundidad de 4 o 6, tasa de aprendizaje de 0.03 o 0.1, regularización y hasta 1 000 iteraciones, con parada temprana en un bloque cronológico interno. Se comparará un modelo sin TWS con otro que utilice TWS solo cuando esté disponible. Su elección final dependerá del RMSE y de la estabilidad entre periodos.

### 5.3 LSTM unidireccional: alternativa temporal

Se considera por su capacidad de representar historia hidrológica, apoyada por los estudios recurrentes revisados y el pronóstico de Li y Kusche (2026). Se propone una red compartida entre celdas, con una capa de 32 o 64 unidades, una salida lineal y ventanas de 6 o 12 meses calendario. Recibirá covariables, indicadores de faltantes y antigüedad del último TWS observado. Se usarán regularización y parada temprana. Compartir parámetros es una decisión del proyecto para aprovechar datos de múltiples celdas; no replica exactamente los modelos por celda de algunos artículos.

### 5.4 Ridge y líneas base: referencias necesarias

La regresión lineal de Z. Sun et al. (2020) motiva una referencia interpretable. Se propone Ridge para reducir inestabilidad ante SPEI correlacionados, con penalizaciones 0.1, 1 y 10. La regularización es una adaptación propia. Se incluirán persistencia, último TWS observado con su antigüedad y climatología mensual estimada con entrenamiento. Donde no exista historia utilizable se recurrirá a una climatología global mensual. Así se evaluará cuánto añade cada modelo a reglas simples bajo la misma disponibilidad.

### 5.5 Modelos pospuestos y orden de trabajo

MLP/DNN quedan como ampliación porque añaden una segunda alternativa neuronal sin priorizar memoria explícita. SARIMAX se reserva para unas pocas series regionales por su costo de ajuste y necesidad de preparar calendarios completos. BiLSTM, atención y CNN bayesiana se posponen por complejidad. El orden inicial será: referencias, Ridge, Random Forest, XGBoost y LSTM. Se avanzará a arquitecturas adicionales si persiste un error que puedan resolver.

<!-- pagebreak -->

# 6. Preparación y manejo del enmascaramiento

### 6.1 Entradas comunes y memoria temporal

La primera comparación usará SPEI a cuatro escalas, humedad del suelo y seno/coseno mensual. Las coordenadas servirán inicialmente para identificar celdas, ordenar historias y desglosar errores. No se convertirán los identificadores en predictores. El uso directo de ubicación se estudiará posteriormente mediante una comparación controlada, porque puede mejorar el ajuste local sin demostrar transferencia espacial.

Los rezagos se construirán por la clave `(celda, mes calendario)`, con historia de 1, 3, 6 y 12 meses cuando exista. Un desplazamiento de filas no garantiza un rezago mensual si faltan fechas. Se reindexará el calendario y se distinguirán ausencia de registro y TWS deliberadamente oculto. Las medias móviles usarán solamente valores conocidos hasta `t`. La imputación y cualquier transformación adicional se ajustarán dentro del entrenamiento de cada partición.

### 6.2 Dos escenarios de disponibilidad

**Escenario A: TWS actual disponible.** Se evaluará predicción directa de `target` y, como variante, predicción del cambio `target - TWS_t`, sumándolo después al TWS actual. Esta segunda opción aprovecha la persistencia, pero solo puede utilizarse si TWS es observable. La transformación es una hipótesis experimental, no una mejora ya demostrada.

**Escenario B: TWS actual oculto.** Se entrenará un modelo que prescinda de TWS contemporáneo y dependa de covariables e historia permitida. Se podrá agregar el último TWS observado y los meses transcurridos desde esa observación, con indicador de ausencia cuando no exista. Una primera solución combinará los modelos A y B según disponibilidad. Se contrastará con un único modelo entrenado con enmascaramiento sintético. Ambos producirán predicciones para todas las filas.

### 6.3 Simulación fiel de la prueba

Se reproducirá aproximadamente la proporción observada de enmascaramiento, incluyendo intervalos consecutivos y antigüedades compatibles con horizontes efectivos de 1 a 7 meses. Las mismas máscaras se usarán en todos los candidatos y se documentarán sus semillas. Una máscara aleatoria por fila puede ser insuficiente: se compararán también escenarios agrupados por mes y celda. El modelo no recibirá un indicador siempre constante durante entrenamiento y variable únicamente durante prueba.

Al construir historia, se ocultarán también las copias equivalentes del valor enmascarado. En particular, `target(t-1)` puede revelar `TWS_t`: no se usará como entrada ni como medio de imputación cuando ese TWS deba estar oculto. Tampoco se emplearán valores futuros de TWS, interpolación con puntos posteriores ni objetivos de validación. Una estimación auxiliar de TWS, si se ensaya, será causal y se entrenará sin acceder a esos valores ocultos.

### 6.4 Pruebas de aporte de variables

Se contrastarán entradas contemporáneas frente a entradas con rezagos, SPEI de todas las escalas frente a escalas largas, y predicción directa frente a cambio residual donde proceda. La historia de prueba se actualizará únicamente con covariables u observaciones permitidas en cada fecha, nunca con sus etiquetas reales ocultas.

<!-- pagebreak -->

# 7. Evaluación y criterio de selección final

### 7.1 Particiones cronológicas

Roberts et al. (2017) muestran por qué la validación debe considerar dependencias temporales y espaciales. Una partición aleatoria de estas filas mezclaría fechas y ubicaciones estrechamente relacionadas. Se propone entrenamiento expansivo: hasta diciembre de 2010 y validación en 2011; hasta diciembre de 2011 y validación en 2012; hasta diciembre de 2012 y validación en 2013. Solo se usarán meses realmente presentes, reportando su cobertura. Enero de 2014-agosto de 2015 se reservará para evaluación final.

Las particiones se asignarán según el mes del objetivo, `time + 1 mes`, para que las etiquetas de entrenamiento terminen antes del primer mes objetivo de validación. Si un rezago de TWS revela el objetivo de otra fila evaluada, se excluirá mediante la máscara común. La selección de hiperparámetros y la parada temprana usarán un tramo final interno del entrenamiento; el bloque externo servirá para comparar candidatos. El periodo final permanecerá cerrado hasta fijar modelo y preparación.

### 7.2 Métricas y diagnósticos

La métrica principal será `RMSE = raíz[promedio((observado - predicho)²)]`, calculada con todas las predicciones fuera de muestra y en la escala original del reto. Se reportarán además MAE y sesgo medio. El RMSE global agrupado se calculará sobre los errores individuales, sin confundirlo con el promedio simple de RMSE por partición.

Se desglosará el error por año, banda de latitud, TWS observado/oculto y antigüedad del último TWS. Se incluirá un resumen con igual peso por región como diagnóstico complementario; la clasificación principal conservará el RMSE del reto. Los extremos de TWS se definirán con umbrales fijados en entrenamiento. Los valores de SPEI ya transformados se usarán en su escala entregada, sin asumir que umbrales físicos del índice se conservan tras la estandarización.

Se registrarán tiempo de ajuste, memoria y variación entre semillas. Para valorar diferencias pequeñas se podrán calcular intervalos mediante remuestreo de bloques temporales de errores emparejados; remuestrear filas como independientes exageraría la cantidad de evidencia. Las importancias de variables se estudiarán fuera de muestra mediante permutaciones que respeten la estructura temporal, interpretándolas como asociaciones predictivas.

### 7.3 Decisión y conclusión

Se elegirá el modelo que reduzca el RMSE fuera de muestra frente a las referencias recalculadas con las mismas máscaras y filas. La mejora deberá ser consistente entre particiones, útil en TWS oculto y razonable en regiones y extremos. Si los errores son similares dentro de la variabilidad observada, se preferirá menor costo y mayor facilidad de explicación.

La revisión justifica comenzar con Random Forest y XGBoost para el formato tabular y contrastarlos con una LSTM que represente memoria temporal. Ridge y las reglas simples permitirán cuantificar el beneficio de esa complejidad. La principal condición de validez es evaluar con la información realmente disponible al pronosticar. La literatura orienta estos candidatos, pero la evidencia del proyecto determinará cuál conservar; todavía no se afirma que alguno haya superado las líneas base.

<!-- pagebreak -->

# 8. Referencias

### Artículos científicos (APA, 7.ª edición)

Breiman, L. (2001). Random forests. *Machine Learning, 45*(1), 5-32. [https://doi.org/10.1023/A:1010933404324](https://doi.org/10.1023/A:1010933404324)

Li, F., & Kusche, J. (2026). Observation-driven forecast of global terrestrial water storage and evaluation for 2010-2024. *Water Resources Research, 62*(2), e2025WR041710. [https://doi.org/10.1029/2025WR041710](https://doi.org/10.1029/2025WR041710)

Long, D., Shen, Y., Sun, A., Hong, Y., Longuevergne, L., Yang, Y., Li, B., & Chen, L. (2014). Drought and flood monitoring for a large karst plateau in Southwest China using extended GRACE data. *Remote Sensing of Environment, 155*, 145-160. [https://doi.org/10.1016/j.rse.2014.08.006](https://doi.org/10.1016/j.rse.2014.08.006)

Lu, S., Li, W., Yao, G., Zhong, Y., Bao, L., Wang, Z., Bi, J., Zhu, C., & Guo, Q. (2024). The changes prediction on terrestrial water storage in typical regions of China based on neural networks and satellite gravity data. *Scientific Reports, 14*, Artículo 16855. [https://doi.org/10.1038/s41598-024-67611-8](https://doi.org/10.1038/s41598-024-67611-8)

Mo, S., Zhong, Y., Forootan, E., Mehrnegar, N., Yin, X., Wu, J., Feng, W., & Shi, X. (2022). Bayesian convolutional neural networks for predicting the terrestrial water storage anomalies during GRACE and GRACE-FO gap. *Journal of Hydrology, 604*, Artículo 127244. [https://doi.org/10.1016/j.jhydrol.2021.127244](https://doi.org/10.1016/j.jhydrol.2021.127244)

<!-- pagebreak -->

# Referencias (continuación)

Palazzoli, I., Ceola, S., & Gentine, P. (2025). GRAiCE: Reconstructing terrestrial water storage anomalies with recurrent neural networks. *Scientific Data, 12*, Artículo 146. [https://doi.org/10.1038/s41597-025-04403-3](https://doi.org/10.1038/s41597-025-04403-3)

Roberts, D. R., Bahn, V., Ciuti, S., Boyce, M. S., Elith, J., Guillera-Arroita, G., Hauenstein, S., Lahoz-Monfort, J. J., Schröder, B., Thuiller, W., Warton, D. I., Wintle, B. A., Hartig, F., & Dormann, C. F. (2017). Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. *Ecography, 40*(8), 913-929. [https://doi.org/10.1111/ecog.02881](https://doi.org/10.1111/ecog.02881)

Sun, A. Y., Scanlon, B. R., Save, H., & Rateb, A. (2021). Reconstruction of GRACE total water storage through automated machine learning. *Water Resources Research, 57*(2), e2020WR028666. [https://doi.org/10.1029/2020WR028666](https://doi.org/10.1029/2020WR028666)

Sun, Z., Long, D., Yang, W., Li, X., & Pan, Y. (2020). Reconstruction of GRACE data on changes in total water storage over the global land surface and 60 basins. *Water Resources Research, 56*(4), e2019WR026250. [https://doi.org/10.1029/2019WR026250](https://doi.org/10.1029/2019WR026250)

### Fuentes del problema y de los datos

*Proyecto 2: Análisis exploratorio*. (2026). [Informe de curso no publicado]. Universidad del Valle de Guatemala. [Repositorio del proyecto](https://github.com/Javiervalladares1/CC3084-Proyecto2-Drought-EDA)

Zindi. (s. f.). *A step ahead of drought: Forecasting global water storage challenge by ITU*. Recuperado el 11 de octubre de 2026, de [https://zindi.world/competitions/one-step-ahead-of-drought-forecasting-global-water-storage-challenge](https://zindi.world/competitions/one-step-ahead-of-drought-forecasting-global-water-storage-challenge)

*Nota bibliográfica.* El año de cada artículo corresponde al volumen publicado, aunque el DOI o la primera publicación en línea contengan un año anterior. Se distinguen Z. Sun y A. Y. Sun en las citas porque son autores diferentes. Los DOI enlazan las versiones de revista; la documentación del reto y el informe local contextualizan el proyecto y no se cuentan entre los nueve artículos científicos.

<!-- pagebreak -->

# Anexo. Verificación de revistas y fuentes

### A.1 Indexación del corpus consultado

La tabla identifica las siete revistas del corpus y un registro público consultado que documenta su presencia en Scopus o Web of Science. La indexación se utiliza como criterio de procedencia editorial, no como garantía de que un modelo funcionará en este proyecto. Consulta: 11 de octubre de 2026.

**Tabla 2. Evidencia pública de indexación**

| Revista | Artículos incluidos | Índice documentado | Fuente de verificación |
| --- | --- | --- | --- |
| Remote Sensing of Environment | Long et al. (2014) | Scopus | [Registro institucional de los autores, con enlace al artículo en Scopus](https://researchnow.flinders.edu.au/en/publications/drought-and-flood-monitoring-for-a-large-karst-plateau-in-southwe/) |
| Water Resources Research | Z. Sun et al. (2020); A. Y. Sun et al. (2021); Li y Kusche (2026) | Scopus y SCIE | [AGU/Wiley: alcance e indexación](https://agupubs.onlinelibrary.wiley.com/hub/journal/19447973/aims-and-scope/read-full-aims-and-scope) |
| Journal of Hydrology | Mo et al. (2022) | Scopus y Web of Science | [Centro Internacional del ISSN: 0022-1694](https://portal.issn.org/custom-search/print/0022-1694/public) |
| Scientific Reports | Lu et al. (2024) | Scopus y Web of Science | [Nature Portfolio: información de la revista](https://www.nature.com/srep/about) |
| Scientific Data | Palazzoli et al. (2025) | Scopus y Web of Science | [Centro Internacional del ISSN: 2052-4463](https://portal.issn.org/resource/ISSN/2052-4463) |
| Machine Learning | Breiman (2001) | Scopus y SCIE | [Springer Nature: abstracting and indexing](https://link.springer.com/journal/10994) |
| Ecography | Roberts et al. (2017) | Scopus y Web of Science | [Centro Internacional del ISSN: 1600-0587](https://portal.issn.org/resource/ISSN/1600-0587) |

*Nota.* SCIE: Science Citation Index Expanded, de Web of Science. Se informa únicamente la cobertura documentada, sin asignar cuartiles ni factores de impacto.

### A.2 Trazabilidad y alcance de la consulta

Se verificaron títulos, autores, años, revistas, volúmenes, localizadores y DOI mediante páginas editoriales, Crossref y registros institucionales. Para los artículos con acceso limitado se utilizó el resumen editorial o la ficha institucional de los autores; se evitó atribuir detalles no disponibles. Los enlaces de esta tabla sirven para comprobar la indexación y no se cuentan como estudios adicionales.

Las cifras del conjunto local proceden del informe exploratorio y de las tablas del proyecto. Las condiciones de emisión, el horizonte efectivo y la prohibición de AutoML se contrastaron con la página oficial del reto. La selección propuesta adapta la evidencia a los datos actuales; no supone reproducir íntegramente los estudios ni importar sus resultados como rendimiento esperado.
