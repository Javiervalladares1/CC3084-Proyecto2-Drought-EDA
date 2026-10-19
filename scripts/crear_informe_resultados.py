"""Construye el informe final con cifras leídas de los experimentos ejecutados."""
from __future__ import annotations

import csv
import json
import textwrap
from pathlib import Path

from formato_informe_resultados import export_pdf, export_word

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "outputs/modelado"
FAMILIES = ("random_forest", "xgboost", "lstm")
LABELS = {"random_forest": "Random Forest", "xgboost": "XGBoost", "lstm": "LSTM"}


def read_json(name):
    return json.loads((RESULTS / name).read_text())


def read_csv(name):
    with (RESULTS / name).open() as stream:
        return list(csv.DictReader(stream))


def table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |",
                       *["| " + " | ".join(str(x) for x in row) + " |" for row in rows]])


def image(name, caption):
    return f"![{caption}](../figures/resultados/{name})"


def main():
    audit = read_json("auditoria.json")
    summary = read_json("resumen_resultados.json")
    env = read_json("entorno.json")
    cfg = audit["config"]
    model_metrics = read_csv("metricas_modelos.csv")
    experiments = read_csv("experimentos.csv")
    holdout = {row["family"]: row for row in summary["holdout_results"]}
    confirmation = {row["family"]: row for row in model_metrics if row["stage"] == "confirmation"}
    winner = summary["recommended_family"]
    descriptive = summary["best_holdout_family_descriptive"]
    best = holdout[winner]
    baseline = {row["algorithm"]: row for row in summary["baselines_holdout"]}
    selected = {family: read_json(f"seleccion_{family}.json") for family in FAMILIES}
    region = [row for row in summary["by_region"] if row["family"] == winner]
    worst_region = max(region, key=lambda row: row["rmse"])
    best_region = min(region, key=lambda row: row["rmse"])
    availability = {(row["family"], row["availability"]): row for row in summary["by_availability"]}
    worst_month = next(row for row in summary["worst_months"] if row["family"] == winner) if any(row["family"] == winner for row in summary["worst_months"]) else summary["worst_months"][0]
    pages = []
    def page(title, *parts):
        pages.append("# " + title + "\n\n" + "\n\n".join(textwrap.dedent(part).strip() for part in parts))

    page("Pronóstico del almacenamiento total de agua",
         "## Resultados del Proyecto 2",
         "**Random Forest, XGBoost y redes neuronales LSTM**",
         "Universidad del Valle de Guatemala\n\nFacultad de Ingeniería\n\nDepartamento de Ciencias de la Computación\n\nCC3084 Data Science · Semestre II de 2026",
         "**Integrantes**\n\nJavier Valladares · 23045\n\nIan Cumes · 23236\n\nJavier Cifuentes · 23079",
         "13 de octubre de 2026",
         "Reto: *A Step Ahead of Drought: Forecasting Global Water Storage Challenge by ITU*",
         "[Repositorio del proyecto](https://github.com/Javiervalladares1/CC3084-Proyecto2-Drought-EDA)")

    page("Resumen de resultados",
         f"Se construyeron y ejecutaron tres familias de regresión para pronosticar el almacenamiento total de agua del siguiente mes calendario: Random Forest, XGBoost y LSTM. El conjunto contiene {audit['train_rows']:,} observaciones con etiquetas y {audit['cells']:,} celdas terrestres. La comparación usó una ventana causal de seis meses, la misma información para todos los modelos y faltantes de TWS por bloques temporales.",
         f"Se compararon tres configuraciones manuales por algoritmo. Los parámetros se ajustaron con objetivos de 2011-2012, la selección entre familias se fijó en 2013 y la prueba final reservada comprendió {summary['holdout_rows']:,} observaciones de {summary['holdout_observed_months']} meses observados entre enero de 2014 y septiembre de 2015. La separación se definió por fecha del objetivo y se excluyeron las etiquetas de la construcción de entradas.",
         f"La selección previa a la prueba final fue {LABELS[winner]}. En la prueba reservada obtuvo RMSE de {best['rmse']:.4f}, MAE de {best['mae']:.4f} y R² de {best['r2']:.4f}. Su variación de RMSE frente a persistencia causal equivale a una mejora de {best['improvement_vs_persistence_pct']:.2f} %. El menor RMSE final observado entre las tres familias correspondió a {LABELS[descriptive]}; esta comparación se informa sin volver a ajustar los modelos con la prueba.",
         "La aplicación permite explorar patrones temporales y geográficos, ingresar una observación o un CSV, seleccionar uno o los tres algoritmos y mostrar u ocultar el rendimiento. Para pronósticos nuevos utiliza modelos reajustados con todas las etiquetas de entrenamiento; las métricas que muestra provienen de modelos distintos que conservaron intacta la prueba temporal.",
         "Las predicciones conservan la escala estandarizada del reto. Test.csv carece de etiquetas: se entregan sus pronósticos, pero no se atribuye a ese archivo un RMSE conocido. La evaluación se refiere a futuras fechas en ubicaciones observadas y no demuestra transferencia a regiones completamente nuevas.",
         "**Palabras clave:** GRACE, almacenamiento total de agua, pronóstico, Random Forest, XGBoost, LSTM, validación temporal.")

    page("1 Introducción y objetivos",
         "Los productos GRACE integran información sobre cambios en el agua almacenada sobre y bajo la superficie terrestre. Su latencia limita el monitoreo próximo al tiempo real. El reto de Zindi e ITU plantea estimar el TWS del siguiente mes calendario mediante información disponible hasta el mes de emisión. Cuando el TWS contemporáneo está oculto, aumenta la antigüedad de la última observación hidrológica conocida (Zindi, s. f.).",
         "El problema se formula como regresión supervisada: cada fila contiene una celda, un mes y covariables climáticas; target es una cantidad continua. Por ello se evalúan errores de pronóstico y no exactitud de clasificación. La pregunta central es qué familia proporciona la mejor combinación de precisión temporal, desempeño regional y costo computacional bajo la disponibilidad real de información.",
         "## Objetivo general",
         "Construir, comparar e integrar en una aplicación tres algoritmos de aprendizaje automático para pronosticar el almacenamiento total de agua del siguiente mes, mediante un procedimiento reproducible que respete el calendario y evite usar observaciones futuras.",
         "## Objetivos específicos",
         "1. Caracterizar los datos y preparar entradas causales con indicadores de faltantes y memoria hidrológica.",
         "2. Fundamentar en literatura científica la selección de Random Forest, XGBoost y LSTM, y ajustar configuraciones mediante validación temporal.",
         "3. Comparar error, sesgo, eficiencia y estabilidad regional de los modelos en una prueba reservada y frente a referencias simples.",
         "4. Desarrollar una aplicación que permita explorar datos, emitir pronósticos y consultar u ocultar resultados interactivos.",
         "5. Documentar los experimentos, sus limitaciones y los pasos necesarios para reproducir y utilizar la solución.")

    page("2 Marco teórico del problema",
         "## Almacenamiento total de agua y observación satelital",
         "TWS integra agua superficial, humedad del suelo, agua subterránea y nieve. GRACE y GRACE-FO estiman cambios de masa mediante variaciones del campo gravitatorio. El almacenamiento responde a procesos con distintas velocidades; una lluvia reciente no resume por sí sola la condición de acuíferos o reservas acumuladas (NASA/JPL, s. f.). En los artículos se usa habitualmente TWSA, es decir, anomalías respecto de una referencia.",
         "## SPEI y memoria climática",
         "El SPEI se basa en un balance entre precipitación y demanda evaporativa acumulado a diferentes escalas. Esa característica permite estudiar déficits de corta y larga duración (Vicente-Serrano et al., 2010). Los archivos entregan escalas de 1, 3, 6 y 12 meses, junto con humedad del suelo. Se conservan esas entradas en su escala suministrada; no se imponen categorías físicas de sequía sobre valores transformados sin conocer su correspondencia original.",
         "## Pronóstico y reconstrucción",
         "Reconstruir observaciones pasadas puede utilizar forzantes conocidos retrospectivamente. Pronosticar exige que cada entrada exista al emitir la predicción. Un buen resultado al completar el intervalo entre misiones no equivale automáticamente a precisión operativa hacia el futuro. En este proyecto, t+1 significa el próximo mes calendario y no el siguiente registro disponible. Las ventanas se reindexan para representar explícitamente meses ausentes.",
         "## Dependencia entre observaciones",
         "Las filas comparten fechas, celdas y condiciones regionales. Millones de filas no equivalen a millones de periodos independientes. Mezclar filas aleatoriamente entre entrenamiento y prueba puede favorecer una evaluación excesivamente optimista. La separación temporal y los diagnósticos regionales responden a este problema (Roberts et al., 2017).")

    page("3 Marco teórico de los algoritmos",
         "## Random Forest",
         "Random Forest agrega árboles entrenados con muestras bootstrap y selección aleatoria de variables. En regresión, el promedio reduce la variabilidad de árboles individuales y representa relaciones no lineales e interacciones (Breiman, 2001). La profundidad y el mínimo de muestras por hoja controlan complejidad. Su predicción depende de patrones observados y tiene capacidad limitada para extrapolar tendencias fuera de los valores aprendidos.",
         "## XGBoost",
         "XGBoost construye árboles de manera secuencial para corregir errores de las predicciones anteriores. La función objetivo combina error de ajuste y penalizaciones de complejidad. La tasa de aprendizaje regula el aporte de cada árbol, mientras subsample y colsample_bytree introducen muestreo de observaciones y variables. El método por histogramas facilita trabajar con matrices extensas. Se utilizó parada temprana en validación para determinar el número de iteraciones (XGBoost Developers, s. f.).",
         "## Redes neuronales LSTM",
         "Una LSTM mantiene un estado de memoria regulado por compuertas, lo que permite aprender dependencias en secuencias (Hochreiter & Schmidhuber, 1997). La implementación utiliza torch.nn.LSTM (PyTorch Contributors, s. f.), recibe seis pasos mensuales en orden cronológico y combina su representación final con información de contexto. Una capa densa produce una corrección continua. La regularización, el recorte de gradiente y la parada temprana ayudan a controlar inestabilidad y sobreajuste.",
         "## Predicción de una corrección",
         "Las tres familias modelan la misma cantidad residual: diferencia entre el objetivo y el último TWS observable. La salida final suma esa observación a la corrección aprendida. Si no hay historia, se usa cero acompañado de un indicador de ausencia. Esta formulación aprovecha la persistencia sin utilizar una etiqueta oculta como entrada. La historia se obtiene únicamente de TWS_t permitido y nunca de target de otra fila.")

    page("4 Revisión bibliográfica de modelos tabulares",
         "La revisión narrativa dirigida incorporó nueve antecedentes científicos, más dos fundamentos sobre memoria neuronal y SPEI. Se consultaron páginas editoriales, DOI y registros institucionales. Se contrastaron metadatos con Crossref y se distinguieron tareas, escala, entradas y validación. No se presenta como una revisión sistemática ni como una búsqueda realizada dentro de Scopus.",
         "Long et al. (2014) utilizaron redes neuronales artificiales para extender GRACE y estudiar sequías e inundaciones en la meseta Yun-Gui. Reportaron R² de 0.91 para la meseta y valores menores en subregiones. El trabajo respalda relaciones no lineales y evaluación territorial; su reconstrucción histórica no prueba precisión futura en una rejilla global.",
         "Z. Sun et al. (2020) compararon DNN, regresión lineal múltiple y SARIMAX con seis productos GRACE y 60 cuencas. La DNN superó ligeramente a SARIMAX y más claramente al modelo lineal en la mayoría de las cuencas. El desempeño dependió del régimen hidrológico y de la intervención humana. La lección es comparar complejidad y memoria bajo condiciones comunes.",
         "A. Y. Sun et al. (2021) evaluaron familias lineales, Random Forest, GBM, XGBoost y redes profundas para reconstrucción en Estados Unidos. El resumen reporta NSE medio de prueba cercano a 0.85 y RMSE normalizado cercano a 0.09. Ninguna familia dominó en todo el territorio. Su flujo AutoML no se adopta porque las reglas del reto lo prohíben; se utilizan como antecedentes los algoritmos individuales.",
         "Breiman (2001) aporta el fundamento de Random Forest. Su inclusión permite contrastar un promedio de árboles con el ajuste secuencial de XGBoost. Las métricas de los artículos se conservan en sus contextos y no se comparan directamente con el RMSE estandarizado de este proyecto.")

    page("5 Revisión de arquitecturas neuronales y pronóstico",
         "Lu et al. (2024) compararon LSTM, BiLSTM con atención y retropropagación mejorada en seis regiones de China, con prueba temporal de septiembre de 2019 a mayo de 2023. En dos regiones reportaron RMSE inferior a 2.641 cm y R² de al menos 0.8. Las series estaban completadas previamente y la escala es regional: esos resultados no fijan un error esperado para el reto.",
         "Palazzoli et al. (2025) presentaron GRAiCE, reconstrucciones globales de TWSA de 1984-2021 con LSTM y BiLSTM, con y sin información de vegetación. La correlación de 0.97 destacada para un promedio global incluye entrenamiento y prueba. Es evidencia de reconstrucción a escala agregada, no una precisión independiente por celda.",
         "Mo et al. (2022) propusieron una CNN bayesiana con conexiones residuales y atención para completar el intervalo entre GRACE y GRACE-FO. El uso de estructura espacial e incertidumbre es pertinente, pero requiere convertir las filas en mapas y justificar un costo adicional. Se reserva para una ampliación.",
         "Li y Kusche (2026) abordaron directamente el pronóstico global con resolución de 1° y horizontes de hasta 12 meses. Separaron tendencia y estacionalidad de una componente no estacional modelada con LSTM y predictores rezagados. Evaluaron retrospectivamente 2010-2024 y reportaron mejoras frente a SEAS5 de ECMWF. Es el antecedente más cercano por emisión futura y escala espacial.",
         "La revisión conduce a las tres familias seleccionadas: Random Forest como referencia no lineal tabular, XGBoost por su capacidad de combinar señales e interacciones y LSTM por la memoria temporal. Se conserva una LSTM unidireccional pequeña frente a variantes bidireccionales, atención y convoluciones más complejas. La selección final depende de la evaluación del proyecto.")

    page("6 Datos originales y auditoría",
         f"Train.csv contiene {audit['train_rows']:,} filas y 13 columnas, con entradas de mayo de 2002 a agosto de 2015. Test.csv contiene {audit['test_rows']:,} filas y 13 columnas, correspondientes a 18 meses observados entre septiembre de 2015 y diciembre de 2018. El entrenamiento cubre {audit['train_observed_months']} de 160 meses calendario y presenta 22 huecos estructurales.",
         table(["Grupo", "Variables", "Tratamiento"], [
             ["Identificación", "sample_id / ID", "Trazabilidad; se excluyen de los predictores"],
             ["Fecha y espacio", "time, lat, lon", "Calendario, celda y contexto geográfico"],
             ["Estado hídrico", "TWS_t", "Disponible u oculto; nunca se rellena con target"],
             ["Clima", "SPEI_01_t, SPEI_03_t, SPEI_06_t, SPEI_12_t", "Cinco covariables al incluir humedad del suelo"],
             ["Suelo", "SOIL_MOISTURE_t", "Entrada contemporánea y secuencia histórica"],
             ["Estacionalidad", "month_sin, month_cos", "Se recalculan desde el mes para nuevas entradas"],
             ["Objetivo", "target", "Etiqueta continua del mes calendario siguiente"],
             ["Disponibilidad", "TWS_t_masked en Test", "Los valores True se mantienen como ausentes"]]),
         f"No se detectaron duplicados de identificador ni de celda-mes. El entrenamiento no presenta nulos en las columnas originales. Test contiene {audit['test_nulls']['TWS_t']:,} TWS ocultos, equivalentes a {audit['test_mask_rate']:.2%}; coinciden exactamente con el indicador de enmascaramiento. Las otras covariables están completas.",
         f"Se verificó el significado de target enlazándolo con el TWS del siguiente mes cuando ambos registros existen: {audit['target_linked_rows']:,} correspondencias, con diferencia absoluta máxima de {audit['target_link_max_absolute_difference']:.2g}. Esta comprobación se utilizó para auditar el objetivo y no para reconstruir predictores.")

    page("7 Análisis exploratorio temporal",
         image("00_cobertura_calendario.png", "Figura 1. Meses observados y ausentes en entrenamiento. Elaboración propia con Train.csv."),
         "La ausencia de filas en algunos meses exige distinguir un calendario incompleto de una columna con nulos. Desplazar una fila por celda puede saltar varios meses. Por ello cada rezago representa un mes calendario exacto y conserva un indicador cuando ese registro no existe.",
         image("01_eda_temporal_estacional.png", "Figura 2. Evolución global y perfiles mensuales regionales calculados con todos los registros disponibles."),
         "El promedio global combina regiones con ciclos distintos. Los perfiles regionales muestran por qué una señal estacional puede reducirse al agregar hemisferios. Se incorporó la codificación cíclica del mes y se evaluó el error por región, sin asumir que una media global represente la precisión en cada celda.")

    page("8 Análisis exploratorio espacial y calidad",
         image("02_eda_espacial.png", "Figura 3. Rejilla terrestre de 1° y promedio del objetivo por celda. Los tonos indican valores estandarizados, no volumen físico."),
         f"La rejilla contiene {audit['cells']:,} celdas. El hemisferio norte reúne el {audit['north_fraction']:.2%} de las filas, de modo que el error agrupado tiene mayor representación de esas ubicaciones. La evaluación regional complementa el criterio global del reto.",
         "El análisis previo encontró persistencia entre TWS actual y objetivo, junto con asociaciones relevantes de las escalas largas de SPEI. La correlación descriptiva no demuestra causalidad ni establece por sí sola qué algoritmo será mejor. El RMSE previo de persistencia de 0.5724 corresponde a entrenamiento con TWS observable; se recalcularon referencias bajo las nuevas máscaras y fechas para obtener comparaciones válidas.",
         "Se conservaron los valores extremos porque pueden representar condiciones hidrológicas importantes. No se eliminaron observaciones por reglas IQR automáticas. El código valida fechas, rangos geográficos, duplicados, números finitos y covariables necesarias; los errores de entrada se informan antes de predecir. Los archivos crudos permanecen sin modificaciones.",
         "La amplitud temporal y la cobertura espacial difieren entre Train y Test. En particular, Test tiene muchas fechas ausentes. Los indicadores de registro permiten representar ese caso, pero la evaluación histórica no elimina por completo el riesgo de cambio de distribución en años posteriores.")

    page("9 Preparación causal de las entradas",
         "Se construyó una ventana de seis meses que termina en la fecha de emisión. Cada paso contiene los cuatro SPEI, humedad del suelo, TWS observable y dos indicadores: disponibilidad de TWS y existencia de registro. Los huecos del calendario y el enmascaramiento deliberado quedan diferenciados. Los valores ausentes se representan con cero y sus indicadores; ese cero no se interpreta como una observación de agua.",
         table(["Componente", "Cantidad", "Información"], [
             ["Secuencia mensual", "6 pasos × 8 canales = 48", "Covariables, TWS e indicadores de disponibilidad"],
             ["Estacionalidad", "2", "Seno y coseno del mes"],
             ["Último TWS e historia", "3", "Valor conocido, antigüedad e indicador de historia"],
             ["Ubicación", "3", "Latitud normalizada y seno/coseno de longitud"],
             ["Tiempo transcurrido", "1", "Meses desde mayo de 2002 divididos entre 120"],
             ["Total", "57", "Misma información para las tres familias"]]),
         "Los árboles reciben la ventana aplanada; la LSTM recibe los mismos 48 valores como seis pasos y agrega las nueve variables de contexto a su representación final. El uso de coordenadas permite describir heterogeneidad en la rejilla conocida. No se utilizaron ID ni códigos de celda como predictores, y no se afirma generalización a celdas geográficas no observadas.",
         "La antigüedad de TWS se calcula en meses calendario y se limita a 24 solo en su representación numérica de entrada. La antigüedad real se conserva para diagnóstico. No se interpolan datos futuros ni se reconstruye TWS_t mediante target(t-1). El escalador de la LSTM se ajusta únicamente con las entradas de entrenamiento de cada etapa.",
         "La prueba unitaria cambia valores futuros y etiquetas y comprueba que las entradas pasadas permanezcan idénticas. Otras pruebas verifican calendarios con huecos, máscaras explícitas, orden de filas y equivalencia entre preparación individual y por lotes.")

    p = audit["partitions"]
    page("10 Diseño de validación y enmascaramiento",
         "Las particiones se definieron antes del ajuste según target_time = time + un mes. Así, la última etiqueta de entrenamiento precede a la primera etiqueta de evaluación. La parada temprana de XGBoost y LSTM se aplicó únicamente a validación de ajuste; la prueba final no se pasó a fit_model ni a una selección posterior de parámetros.",
         table(["Etapa", "Entrenamiento", "Evaluación", "Filas evaluadas"], [
             ["Ajuste", "Hasta 2010-12", "2011-01 a 2012-10, meses presentes", f"{p['ajuste_validacion']['rows']:,}"],
             ["Confirmación", "Hasta 2012-10", "2013-01 a 2013-12, meses presentes", f"{p['confirmacion_validacion']['rows']:,}"],
             ["Prueba reservada", "Hasta 2013-12", "2014-01 a 2015-09, meses presentes", f"{p['prueba_reservada']['rows']:,}"],
             ["Producción", "Todo Train.csv", "Test.csv, sin etiquetas", f"{audit['test_rows']:,}"]]),
         f"El enmascaramiento sintético usa una semilla independiente y bloques mensuales comunes entre celdas, con escasas excepciones de disponibilidad individual. Oculta el {audit['synthetic_mask_rate']:.2%} del TWS en el conjunto preparado. Las proporciones son {p['ajuste_validacion']['masked_rate']:.2%} en validación de ajuste, {p['confirmacion_validacion']['masked_rate']:.2%} en confirmación y {p['prueba_reservada']['masked_rate']:.2%} en prueba reservada. Las variaciones reflejan los bloques y los huecos de cada periodo; no se presenta una coincidencia exacta con el {audit['test_mask_rate']:.2%} de Test.",
         "Los modelos comparten las mismas filas y máscaras. La última observación conocida se obtiene únicamente de TWS permitido hasta la fecha. Para inferir Test se utiliza la historia observable de Train junto con las entradas de Test disponibles hasta cada emisión. Las etiquetas de validación y prueba nunca se usan para llenar historia.",
         "La recomendación se fijó con el menor RMSE de confirmación de 2013 y se registró junto con una huella de la configuración antes de abrir la prueba final. La prueba temporal mide nuevas fechas en celdas ya conocidas; constituye una evaluación diferente de reservar ubicaciones completas (Roberts et al., 2017).")

    page("11 Métricas y referencias de comparación",
         "La métrica principal es RMSE: raíz del promedio del error al cuadrado. Se calcula sobre todas las filas evaluadas en la escala del objetivo. Penaliza con mayor intensidad errores grandes. MAE resume el error absoluto medio; R² compara con la variabilidad del objetivo; el sesgo es el promedio de predicho menos observado. Un sesgo positivo indica sobreestimación promedio y uno negativo indica subestimación.",
         "El RMSE agrupado se obtiene de los errores individuales, no promediando RMSE de regiones o meses. La comparación regional y por disponibilidad utiliza las mismas observaciones para las tres familias. Los extremos se definen con los percentiles 10 y 90 del entrenamiento anterior a 2014, sin ajustar esos cortes con la prueba.",
         "La persistencia causal predice el último TWS observable; si nunca existió una observación, utiliza cero con ausencia de historia identificada. La climatología mensual utiliza el promedio del objetivo por celda y mes objetivo, calculado solo con entrenamiento. Ante una combinación no observada recurre al promedio mensual global y, si fuera necesario, al promedio general del entrenamiento.",
         "Se registraron tiempo de ajuste y predicción, tamaño del modelo guardado y memoria residente máxima del proceso durante el ajuste. La latencia de inferencia se expresa por 1 000 filas a partir de la mediana de tres mediciones del mismo lote de hasta 10 000 observaciones, después de un calentamiento. Son mediciones locales; no constituyen un tiempo garantizado en cualquier equipo.",
         "Para diferencias pequeñas se realizó remuestreo circular de bloques de tres meses observados. Las celdas del mismo mes se conservan juntas y los errores de los algoritmos se comparan de forma pareada. Los intervalos reflejan sensibilidad a esos bloques temporales, no garantizan independencia total ni sustituyen validación en años futuros.")

    rf, xgb, lstm = [selected[family] for family in FAMILIES]
    page("12 Construcción de Random Forest y XGBoost",
         "## Random Forest",
         "Se compararon bosques de 180, 260 y 300 árboles, profundidades máximas de 18, 24 y 28, y mínimos de 30, 12 y 6 muestras por hoja. Cada árbol usa bootstrap con límites de 250 000, 350 000 o 400 000 muestras. El conjunto de entrenamiento completo está disponible para el muestreo de cada árbol; el límite controla costo y memoria como parte del algoritmo.",
         f"La configuración elegida fue {rf['configuration']['name']}: {rf['configuration']['n_estimators']} árboles, profundidad {rf['configuration']['max_depth']}, mínimo {rf['configuration']['min_samples_leaf']} por hoja y hasta {rf['configuration']['max_samples']:,} muestras bootstrap por árbol. Su RMSE de ajuste fue {rf['tuning']['validation']['rmse']:.4f}. La decisión se basó en validación y no en el error de entrenamiento.",
         "## XGBoost",
         "Se compararon profundidades 4, 6 y 8, tasas de aprendizaje 0.06, 0.04 y 0.035, muestreo de filas y columnas de 0.85, y regularización L2 creciente. Se fijaron límites de 1 400, 1 600 y 1 800 iteraciones. La parada temprana tolera 70 iteraciones sin mejora de RMSE en validación de ajuste.",
         f"La configuración elegida fue {xgb['configuration']['name']}, con profundidad {xgb['configuration']['max_depth']} y tasa {xgb['configuration']['learning_rate']}. Se conservaron {xgb['tuning']['best_iterations']} iteraciones. Ese número se fijó para confirmación, prueba y producción, sin usar sus etiquetas para detener el entrenamiento.",
         "Las dos familias utilizan bibliotecas abiertas; el bosque se implementa con RandomForestRegressor (scikit-learn Developers, s. f.). La búsqueda comprende configuraciones manuales documentadas y no un sistema AutoML. Los modelos guardados se recargaron y sus predicciones se contrastaron con las obtenidas antes de guardar.")

    page("13 Construcción de la red neuronal LSTM",
         "La red utiliza una LSTM unidireccional de una capa. Su último estado oculto se concatena con nueve variables de contexto y pasa a una capa densa con ReLU, dropout y una salida lineal. Una red compartida entre celdas permite aprovechar todos los registros sin ajustar miles de redes independientes.",
         table(["Configuración", "Memoria LSTM", "Capa densa", "Dropout", "Tasa"], [[p['name'], p['hidden_size'], p['head_size'], p['dropout'], p['learning_rate']] for p in cfg['lstm']]),
         "El ajuste utiliza AdamW, pérdida de error cuadrático, lotes de 2 048 observaciones, recorte de la norma del gradiente a 5 y semillas fijas. Los límites de entrenamiento fueron 35, 40 y 45 épocas, con paciencias de 6, 7 y 7. Se recuperó el estado de menor RMSE de validación en cada configuración.",
         f"La red seleccionada fue {lstm['configuration']['name']}, con {lstm['configuration']['hidden_size']} unidades LSTM, {lstm['configuration']['head_size']} unidades densas y dropout {lstm['configuration']['dropout']}. El número de épocas para los reajustes posteriores se fijó en {lstm['tuning']['best_epochs']}. Tiene {lstm['tuning']['parameter_count']:,} parámetros entrenables. El escalado se volvió a ajustar únicamente con el entrenamiento correspondiente.",
         image("11_aprendizaje_lstm.png", "Figura 4. RMSE de validación por época. Los marcadores identifican la mejor época de cada configuración."),
         "La curva permite revisar si aumentar épocas sigue mejorando validación. Se evalúa la red por su capacidad de pronóstico, sin asumir que una arquitectura más compleja deba superar a los árboles.")

    page("14 Ajuste y confirmación temporal",
         "**Tabla 1. Configuraciones evaluadas en 2011-2012**",
         table(["Algoritmo", "Configuración", "RMSE", "MAE", "Ajuste en min"], [[row['algorithm'], row['configuration'], f"{float(row['rmse']):.4f}", f"{float(row['mae']):.4f}", f"{float(row['fit_seconds'])/60:.2f}"] for row in sorted(experiments, key=lambda r: (FAMILIES.index(r['family']), r['configuration']))]),
         "Los nueve experimentos se midieron sobre las mismas 249 667 filas de validación. Se eligió el menor RMSE de cada familia. Las diferencias de error y tiempo permiten valorar si una configuración más costosa aporta una mejora útil.",
         "**Tabla 2. Confirmación independiente del ajuste de configuraciones en 2013**",
         table(["Algoritmo", "Configuración", "RMSE", "MAE"], [[LABELS[family], confirmation[family]['configuration'], f"{float(confirmation[family]['rmse']):.4f}", f"{float(confirmation[family]['mae']):.4f}"] for family in FAMILIES]),
         f"Después de ampliar entrenamiento hasta el último objetivo presente de 2012, se evaluaron 109 287 filas de 2013. {LABELS[winner]} obtuvo el menor RMSE de confirmación y quedó registrado como modelo recomendado antes de la prueba final. La confirmación pertenece al desarrollo del modelo; la evidencia de generalización final se informa por separado.")

    page("15 Resultados de la prueba final reservada",
         f"La evaluación final incluyó {summary['holdout_rows']:,} observaciones y {summary['holdout_observed_months']} meses objetivo presentes. Los modelos se entrenaron con 1 888 574 etiquetas anteriores a enero de 2014. La máscara de prueba permaneció igual para todos.",
         "**Tabla 3. Error fuera de muestra y referencias**",
         table(["Modelo o referencia", "RMSE", "MAE", "R²", "Sesgo"],
               [[LABELS[f], f"{holdout[f]['rmse']:.4f}", f"{holdout[f]['mae']:.4f}", f"{holdout[f]['r2']:.4f}", f"{holdout[f]['bias']:.4f}"] for f in FAMILIES] +
               [[name, f"{row['rmse']:.4f}", f"{row['mae']:.4f}", f"{row['r2']:.4f}", f"{row['bias']:.4f}"] for name, row in baseline.items()]),
         image("03_comparacion_rmse.png", "Figura 5. Comparación de RMSE de los tres algoritmos y las dos referencias causales en la prueba reservada."),
         f"El RMSE de persistencia causal fue {baseline['Persistencia causal']['rmse']:.4f}. Las mejoras relativas de Random Forest, XGBoost y LSTM fueron {holdout['random_forest']['improvement_vs_persistence_pct']:.2f} %, {holdout['xgboost']['improvement_vs_persistence_pct']:.2f} % y {holdout['lstm']['improvement_vs_persistence_pct']:.2f} %, respectivamente. Un porcentaje negativo representaría deterioro frente a esa referencia.",
         f"La recomendación fijada en validación fue {LABELS[winner]} y el menor error final descriptivo fue de {LABELS[descriptive]}. Se conservan ambas observaciones para distinguir la decisión previa de la comparación final. No se reajustó la búsqueda después de conocer estos resultados.")

    page("16 Eficiencia y recursos computacionales",
         "Los experimentos se ejecutaron en un Apple M1 Pro, con ocho núcleos lógicos y 16 GB de memoria compartida. Se usaron seis hilos y CPU para las tres familias. El número de filas, la ventana de entrada y la escala del objetivo se mantuvieron comparables.",
         table(["Algoritmo", "Ajuste min", "ms por 1 000 filas", "Modelo MB", "RSS máximo MB"], [[LABELS[f], f"{holdout[f]['fit_seconds']/60:.2f}", f"{holdout[f]['inference_ms_per_1000']:.2f}", f"{holdout[f]['model_size_mb']:.2f}", f"{holdout[f]['peak_rss_mb']:.0f}"] for f in FAMILIES]),
         image("04_eficiencia.png", "Figura 6. Tiempo de ajuste e inferencia medidos localmente para los modelos de la prueba reservada."),
         "El RSS corresponde al proceso durante el ajuste e incluye matrices y estructuras auxiliares; no es una medición aislada del tamaño de los pesos. El tamaño guardado permite valorar distribución y carga. Las diferencias de biblioteca, equipo y lote pueden modificar la latencia.",
         "La solución guarda resultados al terminar cada experimento. Si se interrumpe la ejecución, reutiliza experimentos completos y continúa con los pendientes. Los límites bootstrap del bosque, histogramas de XGBoost y lotes de la LSTM permiten trabajar con el conjunto completo sin requerir una copia separada de cada secuencia en memoria.")

    page("17 Comportamiento temporal y regional",
         image("05_error_temporal.png", "Figura 7. RMSE por mes objetivo; solo se muestran fechas presentes en la prueba temporal."),
         "Las diferencias entre meses permiten identificar periodos difíciles y cambios en el orden de los algoritmos. Los huecos del calendario no se confunden con meses de error cero. El error global integra las observaciones individuales y puede ocultar periodos con desempeño menos favorable.",
         image("06_error_regional.png", "Figura 8. RMSE por banda de latitud, con las mismas filas de evaluación para las tres familias."),
         f"Para {LABELS[winner]}, la región con mayor RMSE fue {worst_region['region']} ({worst_region['rmse']:.4f}) y la menor fue {best_region['region']} ({best_region['rmse']:.4f}). Es una comparación predictiva dentro de la rejilla disponible. La cobertura desigual y las condiciones locales limitan interpretar un promedio global como una garantía territorial.")

    page("18 Disponibilidad e historia de TWS",
         image("07_error_disponibilidad.png", "Figura 9. Comparación del error cuando TWS contemporáneo está observado u oculto."),
         f"Con {LABELS[winner]}, el RMSE fue {availability[(winner,'Observado')]['rmse']:.4f} en TWS observado y {availability[(winner,'Oculto')]['rmse']:.4f} en TWS oculto. Estos grupos difieren también en sus fechas y condiciones hidrológicas; su diferencia de error no se interpreta como un efecto causal aislado del enmascaramiento.",
         image("08_error_antiguedad.png", "Figura 10. RMSE según meses desde la última observación de TWS. La antigüedad cero corresponde a observación actual disponible."),
         "La última observación conocida y su antigüedad aportan contexto cuando faltan registros recientes. El comportamiento por antigüedad debe leerse junto con el tamaño y las fechas de cada grupo. Los casos sin historia o con antigüedad superior a la habitual pueden tener distinta representación y requieren mayor cautela al transferir la solución.")

    page("19 Errores y valores extremos",
         image("09_observado_predicho.png", "Figura 11. Observado frente a predicho para la misma muestra de la prueba. La diagonal indica predicción perfecta; los ejes muestran el rango central para facilitar lectura."),
         image("10_residuos.png", "Figura 12. Distribución de predicho menos observado, en el intervalo mostrado. Las métricas se calculan con todos los errores, incluidos los que quedan fuera del gráfico."),
         f"Los extremos se definieron con cortes del entrenamiento: percentil 10 = {summary['extreme_thresholds_training']['p10']:.4f} y percentil 90 = {summary['extreme_thresholds_training']['p90']:.4f}. La tabla completa de errores y sesgo por extremos se conserva en metricas_extremos.csv. Esta evaluación permite detectar si una mejora media convive con atenuación de valores bajos o altos.",
         f"El sesgo medio de {LABELS[winner]} fue {best['bias']:.4f}. Un sesgo global cercano a cero puede coexistir con errores regionales o de extremos que se compensan. Se mantiene la evaluación desglosada para no confundir calibración promedio con precisión uniforme.")

    intervals = summary['uncertainty']['intervals']
    pairwise = summary['uncertainty']['paired_differences']
    page("20 Incertidumbre de la comparación e interpretación",
         f"Se realizaron {summary['uncertainty']['repetitions']:,} remuestreos de bloques de tres meses observados, manteniendo juntas las celdas de cada fecha. La prueba contiene {summary['holdout_observed_months']} meses observados, una cantidad mucho menor que su número de filas. Los intervalos representan la variación de RMSE al remuestrear esos bloques.",
         table(["Algoritmo", "RMSE observado", "Límite 2.5 %", "Límite 97.5 %"], [[LABELS[r['family']], f"{holdout[r['family']]['rmse']:.4f}", f"{r['rmse_low']:.4f}", f"{r['rmse_high']:.4f}"] for r in intervals]),
         table(["Diferencia de RMSE", "Límite inferior", "Límite superior", "Incluye cero"], [[f"{LABELS[r['first']]} menos {LABELS[r['second']]}", f"{r['ci_low']:.4f}", f"{r['ci_high']:.4f}", "Sí" if r['includes_zero'] else "No"] for r in pairwise]),
         "Si el intervalo de una diferencia incluye cero, esta prueba no aporta evidencia temporal suficiente para sostener un orden estable entre esas dos familias. Si lo excluye, la conclusión sigue condicionada al calendario, a las máscaras y al esquema de bloques utilizados. No se interpreta como garantía para todos los años futuros.",
         image("12_importancias.png", "Figura 13. Importancias internas de árboles agrupadas por dominio. Random Forest usa reducción de impureza y XGBoost su importancia de ganancia; las escalas no son una explicación causal ni se comparan directamente entre familias."))

    page("21 Aplicación para explorar los datos",
         "La aplicación se construyó con Streamlit y Plotly, utilizando sus componentes interactivos y herramientas de prueba (Streamlit, s. f.; Plotly, s. f.). Organiza el recorrido en tres pestañas: Explorar datos, Pronosticar y Evaluar modelos. La barra lateral permite elegir Todos, Random Forest, XGBoost o LSTM. El usuario puede ocultar las gráficas y métricas de rendimiento sin perder el resto de funciones.",
         image("app_explorar.jpg", "Figura 14. Captura de la aplicación ejecutada: exploración de variables, regiones y fechas."),
         "La exploración incluye filtros de región y periodo, distribución de una variable seleccionable, evolución temporal regional, distribución espacial y descripción de columnas. La distribución utiliza una muestra reproducible de 40 000 filas para facilitar navegación; las series y el mapa resumen todos los datos de entrenamiento. Esa reducción visual no se utiliza para calcular métricas.",
         "La paleta de la aplicación utiliza fondo claro, texto oscuro y acentos azul verdosos relacionados con el agua. Los algoritmos mantienen colores consistentes en las gráficas. Los rótulos, leyendas y controles complementan el color para que la interpretación no dependa exclusivamente de distinguir tonalidades.")

    page("22 Aplicación para pronosticar nuevas observaciones",
         "El formulario solicita mes, coordenadas, SPEI en cuatro escalas y humedad del suelo. Un control permite indicar si se conoce el TWS actual. También se puede cargar un ejemplo real de Test. La aplicación identifica historia observable para esa celda y prepara automáticamente las mismas 57 entradas que utiliza el entrenamiento.",
         image("app_pronosticar.jpg", "Figura 15. Captura de una predicción real con los modelos guardados y reajustados para producción."),
         "La alternativa CSV acepta hasta 300 000 observaciones y permite descargar una plantilla. TWS_t es opcional y las otras covariables son necesarias. Las filas anteriores del archivo pueden aportar historia, siempre respetando su fecha. Se rechazan fechas inválidas, duplicados de celda-mes, coordenadas fuera de rango, valores infinitos y covariables no numéricas.",
         "El resultado muestra el mes objetivo y la predicción de cada algoritmo elegido, conserva la escala estandarizada y permite descargar las filas completas. Para un registro individual también informa la última observación de TWS y su antigüedad, cuando existe. El sistema pronostica una cantidad de agua estandarizada; no convierte ese número automáticamente en una categoría de sequía.")

    page("23 Aplicación para evaluar los algoritmos",
         "La pestaña de evaluación muestra RMSE, MAE, R², sesgo y tiempos de cada modelo seleccionado. Las gráficas interactivas comparan error global, evolución mensual, regiones, disponibilidad de TWS, dispersión y promedio global observado frente a pronosticado. Se puede inspeccionar un algoritmo o ver los tres.",
         image("app_evaluar.jpg", "Figura 16. Captura de la evaluación interactiva sobre la prueba temporal reservada."),
         "Las métricas provienen de predicciones fuera de muestra guardadas antes del reajuste de producción. Esa separación evita mostrar como prueba el ajuste de un modelo que ya vio esas etiquetas. El archivo Test oficial se utiliza únicamente para emitir pronósticos sin atribuirle precisión no verificable.",
         "Se probó el recorrido de formulario y carga CSV, la selección de uno y todos los modelos, el manejo de TWS ausente, entradas inválidas, descargas y el control para ocultar rendimiento. Las pruebas de integración verifican que las predicciones sean finitas y que guardar y recargar los modelos conserve sus salidas.")

    page("24 Discusión y conclusiones",
         f"El objetivo de construir y comparar tres familias se cumplió con nueve configuraciones de ajuste, confirmación temporal y prueba reservada. {LABELS[winner]} quedó seleccionado con validación de 2013; su RMSE final fue {best['rmse']:.4f}. El resultado se compara con persistencia causal bajo las mismas filas y máscaras, y no con el valor descriptivo de la etapa exploratoria.",
         f"La LSTM obtuvo el menor RMSE descriptivo final ({holdout['lstm']['rmse']:.4f}), frente a {best['rmse']:.4f} de XGBoost. Sin embargo, el intervalo de la diferencia XGBoost menos LSTM fue de -0.0060 a 0.0163 e incluye cero. Esa diferencia no demuestra una superioridad temporal estable; se mantiene la recomendación fijada antes de la prueba.",
         "La preparación incorporó calendario, faltantes e historia sin usar observaciones futuras. Los resultados desglosados muestran que una decisión basada solo en error global resulta incompleta: las condiciones de disponibilidad, región y extremos forman parte del desempeño práctico. Los intervalos por bloques añaden una lectura de incertidumbre acorde con la dependencia temporal.",
         "La aplicación integra exploración y pronóstico con el mismo preprocesamiento del entrenamiento. Permite trabajar con TWS oculto y comparar modelos sin requerir que el usuario construya rezagos o ajuste escaladores. Las gráficas pueden ocultarse y las predicciones se descargan para continuar el análisis.",
         "La evaluación tiene límites concretos. La prueba reservada cubre un número reducido de meses observados y la máscara es una simulación aproximada. La composición espacial favorece el hemisferio norte. Test abarca años posteriores y un calendario más discontinuo. Los modelos no se validaron reservando regiones enteras y no se dispone de etiquetas de Test para verificar precisión en ese periodo.",
         "Las importancias de árboles describen asociaciones predictivas internas. Los valores estandarizados no proporcionan volumen físico ni un umbral universal de sequía. Las predicciones no incluyen intervalos de incertidumbre por observación; los intervalos presentados corresponden a la comparación agregada de errores.",
         "La siguiente evaluación útil consiste en incorporar nuevos meses etiquetados, contrastar varias máscaras temporales y reservar regiones completas antes de ampliar el uso geográfico. Esas ampliaciones deben conservar el corte temporal y compararse con las mismas referencias. El resultado actual entrega una solución ejecutada, documentada y reutilizable, con sus condiciones de validez explícitas.")

    versions = env['versions']
    page("25 Herramientas y reproducción",
         f"Se utilizó Python {env['python']}, NumPy {versions['numpy']}, pandas {versions['pandas']}, scikit-learn {versions['scikit-learn']}, XGBoost {versions['xgboost']} y PyTorch {versions['torch']}. La aplicación utiliza Streamlit {versions['streamlit']} y Plotly {versions['plotly']}. Las versiones exactas, semillas, parámetros y huellas SHA-256 están guardadas en los manifiestos de la entrega.",
         "Los datos originales se descargan desde Zindi y se colocan en data/raw/. Los productos preparados se guardan en data/processed/modelado/, los pesos en models/, los resultados en outputs/modelado/ y las figuras en figures/resultados/. El notebook de resultados permite inspeccionar los experimentos ya ejecutados y volver a generar el análisis.",
         "## Ejecución desde la raíz del repositorio",
         "```text\npython -m pip install -r requirements-modelado.lock.txt\npython scripts/entrenar_modelos.py --stage all --family all\npython scripts/analizar_resultados.py\npython scripts/generar_notebook_resultados.py\npython -m streamlit run app.py\n```",
         "El entrenamiento respeta el orden Random Forest, XGBoost y LSTM. Guarda checkpoints por experimento y puede reanudarse. El proceso genera predicciones con las columnas ID y Target para todas las filas de Test, además de un archivo correspondiente a la familia recomendada. No realiza una entrega automática a la plataforma.",
         "El código del proyecto utiliza bibliotecas abiertas. La carpeta de entrega incluye la aplicación, instrucciones, modelos entrenados, métricas, figuras, notebook e informe editable. La presentación conserva tablas y gráficas de resultados editables.",
         "[Repositorio usado para versionar el código](https://github.com/Javiervalladares1/CC3084-Proyecto2-Drought-EDA)")

    old = (ROOT / "docs/Revision_Bibliografica_TWS.md").read_text()
    refs_block = old.split("# 8. Referencias", 1)[1].split("### Fuentes del problema", 1)[0]
    references = [line.strip() for line in refs_block.splitlines() if re_reference(line)]
    references.append("Hochreiter, S., & Schmidhuber, J. (1997). Long short-term memory. *Neural Computation, 9*(8), 1735-1780. [https://doi.org/10.1162/neco.1997.9.8.1735](https://doi.org/10.1162/neco.1997.9.8.1735)")
    references.append("Vicente-Serrano, S. M., Beguería, S., & López-Moreno, J. I. (2010). A multiscalar drought index sensitive to global warming: The standardized precipitation evapotranspiration index. *Journal of Climate, 23*(7), 1696-1718. [https://doi.org/10.1175/2009JCLI2909.1](https://doi.org/10.1175/2009JCLI2909.1)")
    references.sort(key=str.casefold)
    assert len(references) == 11, len(references)
    page("Referencias científicas", "## APA séptima edición", *references[:5])
    page("Referencias científicas continuación", *references[5:])
    page("Fuentes de documentación y del proyecto",
         "NASA/JPL. (s. f.). *Measuring water storage in the Amazon*. GRACE Tellus. [https://grace.jpl.nasa.gov/resources/8/measuring-water-storage-in-the-amazon/](https://grace.jpl.nasa.gov/resources/8/measuring-water-storage-in-the-amazon/)",
         "*Proyecto 2: Análisis exploratorio*. (2026). [Informe de curso no publicado]. Universidad del Valle de Guatemala. [Repositorio del proyecto](https://github.com/Javiervalladares1/CC3084-Proyecto2-Drought-EDA)",
         "Plotly. (s. f.). *Open source Python graphing and data visualization library*. [https://plotly.com/python/](https://plotly.com/python/)",
         "PyTorch Contributors. (s. f.). *LSTM*. PyTorch documentation. [https://docs.pytorch.org/docs/stable/generated/torch.nn.LSTM.html](https://docs.pytorch.org/docs/stable/generated/torch.nn.LSTM.html)",
         "scikit-learn Developers. (s. f.). *RandomForestRegressor*. scikit-learn documentation. [https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html)",
         "Streamlit. (s. f.). *App testing*. Streamlit documentation. [https://docs.streamlit.io/develop/api-reference/app-testing](https://docs.streamlit.io/develop/api-reference/app-testing)",
         "Universidad del Valle de Guatemala. (2026). *Guía del Proyecto 2: Resultados*. [Material del curso CC3084 Data Science]. Facultad de Ingeniería.",
         "XGBoost Developers. (s. f.). *Python API reference*. XGBoost documentation. [https://xgboost.readthedocs.io/en/stable/python/python_api.html](https://xgboost.readthedocs.io/en/stable/python/python_api.html)",
         "Zindi. (s. f.). *A step ahead of drought: Forecasting global water storage challenge by ITU*. Recuperado el 13 de octubre de 2026, de [https://zindi.world/competitions/one-step-ahead-of-drought-forecasting-global-water-storage-challenge](https://zindi.world/competitions/one-step-ahead-of-drought-forecasting-global-water-storage-challenge)")

    appendix = old.split("**Tabla 2. Evidencia pública de indexación**", 1)[1].split("*Nota.* SCIE", 1)[0].strip()
    page("Anexo de procedencia bibliográfica",
         "Los antecedentes aplicados se publicaron en revistas indexadas. La siguiente evidencia pública documenta las siete revistas del corpus inicial. Se informa cobertura editorial sin asignar cuartiles ni factores de impacto. Las fuentes técnicas y los materiales del curso se distinguen de los artículos científicos.",
         appendix,
         "Neural Computation, que publica el fundamento de LSTM, documenta Scopus, Science Citation Index Expanded y Web of Science en su [lista editorial de indexación](https://direct.mit.edu/neco/pages/abstracting-indexing). La referencia original de SPEI se verificó en la [página editorial de Journal of Climate](https://journals.ametsoc.org/view/journals/clim/23/7/2009jcli2909.1.xml).",
         "Los títulos, autores, años, volúmenes, páginas o localizadores y DOI de los antecedentes se contrastaron con páginas editoriales, Crossref o registros institucionales. Para obras de acceso limitado se consultó el resumen disponible sin atribuir métodos no accesibles. Las cifras propias se generan mediante los scripts y se conservan en tablas de resultados.")

    source = ROOT / "docs/Informe_Final_Parte2_TWS.md"
    source.write_text("\n\n<!-- pagebreak -->\n\n".join(pages) + "\n", encoding="utf-8")
    export_word(source, ROOT / "output/word/Informe_Final_Parte2_TWS.docx")
    export_pdf(source, ROOT / "output/pdf/Informe_Final_Parte2_TWS.pdf")
    print(f"Informe generado desde {len(pages)} bloques de página.")


def re_reference(line):
    return line.strip().startswith(("Breiman,", "Li, F.,", "Long, D.,", "Lu, S.,", "Mo, S.,", "Palazzoli,", "Roberts,", "Sun, A. Y.,", "Sun, Z.,"))


if __name__ == "__main__":
    main()
