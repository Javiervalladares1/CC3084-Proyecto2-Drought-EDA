# Guía de uso y reproducción de la parte 2

## Contenido y lectura

Abra `output/word/Informe_Final_Parte2_TWS.docx` para editar y `output/pdf/Informe_Final_Parte2_TWS.pdf` para entregar. La presentación se encuentra en `output/presentacion/Proyecto2_Resultados_TWS_Final.pptx`. El notebook `Proyecto2_Resultados.ipynb` conserva las salidas de la ejecución real. `config/modelado.json` contiene semillas y las nueve configuraciones manuales.

El texto y los enlaces del informe son negros. Las gráficas científicas usan escalas de gris. Las capturas conservan la interfaz original de la aplicación.

## Ejecutar la aplicación

Use Python 3.12.14 y un entorno virtual. Instale `requirements-modelado.lock.txt`, sitúese en la raíz del paquete y ejecute `python -m streamlit run app.py`. Visite http://127.0.0.1:8501/. El tiempo de inicio incluye leer los modelos y preparar la historia; la latencia de la tabla corresponde al modelo ya cargado.

1. En Explorar datos, cambie regiones, periodo y variable. La distribución utiliza una muestra fija; las series y el mapa resumen todos los registros.
2. En Pronosticar, pulse Cargar ejemplo real de Test, elija uno o todos los algoritmos y pulse Predecir. La predicción corresponde al mes calendario siguiente.
3. En Archivo CSV, cargue `outputs/modelado/ejemplo_nuevos_datos.csv` y pulse Predecir archivo. TWS_t es opcional; los cuatro SPEI y humedad del suelo deben estar presentes y en la escala del reto.
4. Descargue los resultados. En Evaluar modelos puede filtrar algoritmos y ocultar el rendimiento desde la barra lateral.

Los pesos de producción utilizan todas las etiquetas de Train hasta septiembre de 2015. Las métricas históricas provienen de modelos separados que no se entrenaron con la prueba reservada. No se presentan como precisión sobre Test.csv.

## Reproducir entrenamiento y análisis

Los archivos originales se obtienen del reto Zindi y se colocan en `data/raw/`. No se redistribuyen en el paquete. Sus huellas SHA-256 están en `outputs/modelado/auditoria.json`.

```bash
python scripts/entrenar_modelos.py --stage all --family all
python scripts/analizar_resultados.py
python scripts/preparar_datos_aplicacion.py
python scripts/generar_notebook_resultados.py
python -m pytest -q
```

Se ejecutan Random Forest, XGBoost y LSTM en procesos separados. El ajuste usa objetivos de 2011-2012, la selección entre familias se fija en 2013 y la prueba final usa 2014-2015. Las máscaras y particiones se comparten entre modelos. Se conservan los checkpoints para reanudar. Para una ejecución nueva con otros parámetros, use una copia de trabajo y retire allí los checkpoints y cachés anteriores; no mezcle manifiestos de configuraciones distintas.

El paquete incluye pesos de confirmación, prueba y producción, así como los metadatos de las nueve configuraciones. Los pesos grandes de configuraciones descartadas se conservan localmente en el proyecto original y pueden reproducirse; no se duplican en el ZIP.

Para volver a ejecutar el notebook, abra Jupyter con el mismo entorno y ejecute todas las celdas. Consulta resultados guardados y recalcula las métricas, sin volver a entrenar. El script `generar_notebook_resultados.py` reconstruye su fuente.

## Regenerar los documentos

Instale también `requirements-documentos.txt` y ejecute `python scripts/crear_informe_resultados.py`. Las capturas utilizadas están en `figures/resultados/`. Word y PDF proceden de una única fuente Markdown. El exportador utiliza Arial si está disponible y Helvetica para PDF como alternativa.

La fuente de la presentación está en `scripts/crear_presentacion_resultados.mjs`. Su generación usa `@oai/artifact-tool` y validadores del entorno Codex; el archivo PPTX entregado es independiente de esas herramientas y se puede editar directamente en PowerPoint. Las gráficas contienen libros de datos incrustados.

## Archivos para la plataforma del reto

`outputs/modelado/submission_random_forest.csv`, `submission_xgboost.csv` y `submission_lstm.csv` tienen 280 961 filas con columnas ID y Target. `submission_recomendado.csv` corresponde a XGBoost. No se hizo una entrega automática a Zindi.

## Enlaces de entrega

Repositorio: https://github.com/Javiervalladares1/CC3084-Proyecto2-Drought-EDA

La guía de curso solicita el enlace de Google Drive donde el grupo trabajó el informe. Debe colocarse el enlace real del grupo al subir o importar el Word; el paquete no inventa ese enlace ni el historial de colaboración.
