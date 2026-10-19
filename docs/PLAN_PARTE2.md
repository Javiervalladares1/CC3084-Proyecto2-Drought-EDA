# Plan de trabajo de la parte 2

Fecha de preparación: 12 de octubre de 2026.

## Alcance y entregables

Completar la etapa de resultados de CC3084 para el reto de pronóstico global de almacenamiento total de agua. Se entrenarán exactamente las tres familias solicitadas, en este orden: Random Forest, XGBoost y redes neuronales mediante una LSTM unidireccional. Persistencia y climatología serán reglas de referencia, no familias adicionales en competencia.

La entrega incluirá código reproducible, notebook de resultados, modelos guardados, tablas de experimentos, predicciones, al menos tres figuras estáticas, aplicación interactiva probada, informe final en Word y PDF y presentación. Se conservarán los archivos originales y el trabajo previo del grupo.

## 1 Preparación y auditoría

- Verificar tamaños, columnas, identificadores, duplicados, nulos, calendario, cobertura geográfica y escala de las variables.
- Registrar huellas SHA-256 de los archivos crudos y versiones de las dependencias.
- Generar un panel mensual por celda sin interpolar con observaciones futuras.
- Construir una ventana causal de seis meses con las cinco covariables climáticas, TWS observable e indicadores de disponibilidad.
- Agregar estacionalidad, última observación conocida de TWS y su antigüedad, ubicación y tiempo transcurrido. Los identificadores no serán predictores.
- Reproducir faltantes por bloques temporales compartidos entre celdas, cercanos al 66.5 % observado en Test.csv. No utilizar target para rellenar TWS.

## 2 Protocolo de evaluación fijado antes del ajuste

Las particiones se definirán por el mes del objetivo, un mes calendario después de time.

| Etapa | Entrenamiento | Evaluación | Uso |
| --- | --- | --- | --- |
| Ajuste de configuraciones | Objetivos hasta diciembre de 2010 | Objetivos de 2011 y 2012 | Elegir parámetros y duración de entrenamiento |
| Confirmación temporal | Objetivos hasta diciembre de 2012 | Objetivos de 2013 | Elegir la familia recomendada |
| Prueba final reservada | Objetivos hasta diciembre de 2013 | Objetivos de 2014 hasta septiembre de 2015 | Comparación final sin reajuste posterior |
| Producción | Todas las etiquetas de Train.csv | Test.csv sin etiquetas | Generar predicciones y alimentar la aplicación |

Se evaluarán las mismas filas y máscaras para los tres algoritmos. Todos recibirán la misma información histórica; los árboles utilizarán la ventana aplanada y la LSTM la ventana secuencial. Se modelará la corrección respecto del último TWS realmente observable. En ausencia de historia, esa referencia será cero con un indicador explícito de ausencia. El escalado de la red se ajustará exclusivamente con entrenamiento.

Las métricas serán RMSE principal, MAE, R² y sesgo. Se registrarán tiempos de entrenamiento e inferencia y tamaño de los modelos. Los resultados se desglosarán por periodo, región, disponibilidad de TWS y antigüedad de la última observación. Test.csv no se utilizará para afirmar precisión porque no contiene etiquetas.

## 3 Entrenamiento y ajuste

1. Random Forest: comparar tres configuraciones manuales de profundidad, tamaño del bosque y regularización por hoja. El bootstrap por árbol tendrá un límite explícito de muestras para controlar memoria.
2. XGBoost: comparar tres configuraciones manuales de profundidad y tasa de aprendizaje, con árboles por histogramas y parada temprana sobre validación.
3. LSTM: comparar tres configuraciones manuales de unidades, regularización y tasa de aprendizaje. Utilizar lotes, semillas fijas, recorte de gradiente y parada temprana. Guardar las curvas de aprendizaje.

Se guardarán los resultados de cada experimento al terminar, de forma que el trabajo pueda continuar sin repetir ajustes completos. Los recursos disponibles son un Apple M1 Pro con ocho núcleos y 16 GB de memoria compartida. Se reservará parte de la capacidad para mantener utilizable el equipo.

## 4 Resultados y discusión

Se prepararán comparaciones de error global, tiempo de ajuste, comportamiento temporal, errores por región y disponibilidad, dispersión observado frente a predicho y curvas de aprendizaje. Se explicarán las mejoras frente a las referencias, los desacuerdos entre validación y prueba final, los extremos y los límites de generalización. Se conservará la revisión bibliográfica y sus referencias APA de revistas indexadas.

## 5 Aplicación

La aplicación en Streamlit incluirá exploración del conjunto limpio, mapas y series interactivas, formulario para nuevas observaciones, carga CSV, selección de un algoritmo o los tres, descarga de predicciones y una opción para mostrar u ocultar las métricas y gráficas de rendimiento. El preprocesamiento será compartido con el entrenamiento y automático. Las gráficas de evaluación corresponderán a modelos evaluados fuera de muestra; la predicción de nuevos datos utilizará los modelos reajustados para producción.

## 6 Verificación y entrega

- Probar causalidad, calendarios con huecos, máscaras, validación de entradas y consistencia de predicciones al guardar y cargar modelos.
- Recalcular las métricas a partir de las predicciones reservadas y verificar que las fechas de entrenamiento precedan a las de evaluación.
- Probar la aplicación con datos completos, TWS oculto, un modelo, los tres, entradas inválidas y controles de visualización.
- Revisar visualmente todas las páginas del informe y todas las diapositivas.
- Organizar una carpeta de entrega con instrucciones y un manifiesto de cumplimiento de la guía.
- Versionar únicamente el trabajo producido en esta etapa, sin atribuir contribuciones individuales inventadas. Conservar el enlace del repositorio existente. El enlace de Drive se incorporará si el grupo lo proporciona; el Word quedará listo para cargarlo.
