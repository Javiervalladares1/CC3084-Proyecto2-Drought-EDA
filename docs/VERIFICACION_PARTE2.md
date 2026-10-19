# Verificación de la parte 2

Fecha de verificación: 13 de octubre de 2026.

| Requisito | Evidencia entregada |
|---|---|
| Plan antes de ejecutar | docs/PLAN_PARTE2.md y registro de trabajo |
| Revisión y referencias APA | Informe, secciones 2 a 5 y bibliografía; 11 referencias científicas |
| Tres familias en el orden solicitado | Random Forest, XGBoost y LSTM; config/modelado.json |
| Preparación de datos | src/tws/data.py; 57 entradas compartidas, meses calendario e indicadores |
| Ajuste de varios modelos | 9 configuraciones; outputs/modelado/experimentos.csv |
| Selección anterior a prueba | outputs/modelado/seleccion_fijada.json; validación de 2013 |
| Prueba temporal y comparación | 265 447 filas de 17 meses; metricas_modelos.csv y predicciones guardadas |
| Tres gráficas estáticas como mínimo | 13 figuras científicas en figures/resultados/ |
| Exploración interactiva | Pestaña Explorar datos; regiones, fechas, distribución, serie y mapa |
| Nuevos datos y selección de modelos | Formulario y CSV; uno o tres modelos, resultados y descarga |
| Rendimiento que puede ocultarse | Barra lateral y pestaña Evaluar modelos |
| Informe final | Word editable y PDF de 31 páginas con texto negro |
| Código y notebook | app.py, src/tws, scripts y notebook con todas las celdas ejecutadas |
| Presentación | 16 diapositivas, notas y 6 gráficas con libros de datos incrustados |
| Repositorio | URL real en README e informe; rama codex/proyecto2-resultados |
| Enlace de Drive del trabajo grupal | Pendiente de incorporar el enlace real del grupo al documento subido |

## Comprobaciones ejecutadas

- Las 14 pruebas unitarias de preparación e ingreso pasaron.
- Las 4 pruebas de integración pasaron: equivalencia con predicciones guardadas, uno frente a todos los modelos, recorrido de la interfaz y completitud de los archivos de Test. Una ruta de AppTest se corrigió para usar la ubicación absoluta de la aplicación y se volvió a ejecutar con éxito.
- La aplicación se probó en navegador: formulario con ejemplo real, los tres pronósticos, carga CSV y predicción, selección de XGBoost, ocultar y restaurar rendimiento, descarga CSV. El archivo descargado contiene valores finitos y el mes objetivo esperado.
- Se verificó diseño adaptable en los anchos de 637 y 1 440 píxeles, sin desbordamiento horizontal general.
- Cada familia produce 280 961 filas únicas de Test, con ID y Target. El recomendado coincide con XGBoost.
- El RMSE se recalculó a partir de los errores de las predicciones guardadas y coincide con los manifiestos.
- Los checkpoints se recargaron y conservaron sus predicciones.
- Todas las celdas del notebook están ejecutadas y no contienen salidas de error.
- Se revisaron visualmente todas las páginas del Word renderizado; el PDF final se exportó de ese mismo documento. Las figuras recortadas por interlineado fijo se corrigieron antes de la entrega.
- Se revisaron las 16 diapositivas. El validador de estructura, geometría, tablas nativas y libros incrustados de las gráficas pasó. La imagen de la aplicación se incrustó como bytes para conservarla en el PPTX.

- La copia portátil de entrega, sin CSV originales ni cachés, pasó las 18 pruebas en 14.07 segundos.
- La presentación final se volvió a importar y renderizar: sus 16 diapositivas coinciden píxel por píxel con la versión revisada.

## Interpretación de resultados

XGBoost quedó seleccionado antes de la prueba final y mejora RMSE frente a persistencia en 17.10 %. LSTM obtuvo el menor RMSE final observado, 0.6989, frente a 0.7035 de XGBoost; el intervalo de su diferencia incluye cero. No se utiliza la prueba para reajustar esa decisión.

La máscara sintética aproxima el problema de disponibilidad y la prueba evalúa nuevas fechas en celdas conocidas. No prueba transferencia espacial ni precisión sobre Test, cuyo objetivo no es público. Las unidades de predicción son estandarizadas; no equivalen a centímetros ni a categorías de sequía.

## Portabilidad

El ZIP incluye historia observable sin target, modelos seleccionados de confirmación, prueba y producción, metadatos de todas las configuraciones, métricas y pronósticos completos. Excluye los CSV originales, cachés grandes, entornos virtuales y los pesos de configuraciones descartadas. La guía explica cómo reconstruir esos productos.
