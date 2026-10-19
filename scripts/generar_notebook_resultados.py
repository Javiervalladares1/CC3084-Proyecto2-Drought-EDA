"""Genera y ejecuta el notebook que documenta los experimentos reales."""
from pathlib import Path
import json
import os
import sys

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]


def main():
    cells = []
    def md(text):
        cells.append(nbformat.v4.new_markdown_cell(text))
    def code(text):
        cells.append(nbformat.v4.new_code_cell(text))
    md("# Proyecto 2 Resultados\n\n**Pronóstico de TWS con Random Forest, XGBoost y LSTM**\n\nJavier Valladares 23045, Ian Cumes 23236 y Javier Cifuentes 23079.\n\nEste notebook reúne auditoría, protocolo, configuraciones y resultados de los experimentos ejecutados con `scripts/entrenar_modelos.py`. Por defecto inspecciona los artefactos guardados y verifica sus métricas. El entrenamiento completo se puede activar explícitamente en la sección correspondiente. Test.csv no contiene etiquetas y no se utiliza para atribuir una precisión conocida.")
    code("from pathlib import Path\nimport json, sys, subprocess\nimport numpy as np\nimport pandas as pd\nfrom IPython.display import display, Image, Markdown\nROOT = Path.cwd()\nif not (ROOT / 'config/modelado.json').exists():\n    ROOT = ROOT.parent\nsys.path.insert(0, str(ROOT / 'src'))\nfrom tws.utils import RESULTS, FIGURES, FAMILIES, LABELS, sha256\nAUDIT = json.loads((RESULTS / 'auditoria.json').read_text())\nSUMMARY = json.loads((RESULTS / 'resumen_resultados.json').read_text())\npd.set_option('display.max_columns', 20)\nprint('Raíz del proyecto:', ROOT)\nprint('Familias:', ', '.join(LABELS[f] for f in FAMILIES))")
    md("## 1 Datos originales y trazabilidad\n\nUna fila representa una celda y un mes. Las etiquetas corresponden al siguiente mes calendario. Se conservaron los extremos y los archivos originales. Si están presentes los CSV crudos, se verifica su huella contra la ejecución registrada.")
    code("display(pd.DataFrame([{'conjunto':'Train','filas':AUDIT['train_rows'],'meses_observados':AUDIT['train_observed_months']},\n                      {'conjunto':'Test','filas':AUDIT['test_rows'],'meses_observados':AUDIT['test_observed_months']}]))\nprint('Celdas:', AUDIT['cells'])\nprint('Meses calendario ausentes en Train:', len(AUDIT['train_missing_months']))\nprint('TWS oculto en Test:', f\"{AUDIT['test_mask_rate']:.2%}\")\nfor name, expected in AUDIT['raw_sha256'].items():\n    path = ROOT / 'data/raw' / name\n    if path.exists():\n        assert sha256(path) == expected\n        print(name, 'SHA-256 verificado')\n    else:\n        print(name, 'no incluido en la entrega; se conserva la huella de la ejecución original')\ndisplay(pd.read_csv(RESULTS / 'estadisticas_originales.csv', index_col=0))")
    md("## 2 Análisis exploratorio\n\nEl calendario contiene huecos y los ciclos regionales se compensan al promediar globalmente. La cobertura del hemisferio norte es mayor. Estos hallazgos motivan ventanas por mes calendario, estacionalidad y evaluación regional.")
    code("for name in ['00_cobertura_calendario.png','01_eda_temporal_estacional.png','02_eda_espacial.png']:\n    display(Image(filename=str(FIGURES / name), width=950))")
    md("## 3 Protocolo temporal y prevención de fuga\n\nLos cortes usan la fecha del objetivo. Las configuraciones se ajustan con 2011-2012, se confirman en 2013 y la prueba final de 2014-2015 queda fuera del ajuste. La historia solo utiliza TWS observable y covariables hasta la emisión. Los tres algoritmos reciben la misma información y la misma máscara.")
    code("display(pd.DataFrame(AUDIT['partitions']).T)\nprint('Máscara sintética global:', f\"{AUDIT['synthetic_mask_rate']:.2%}\")\nprint('Variables preparadas:', AUDIT['feature_count'])\nfrom tws.data import feature_names\ndisplay(pd.DataFrame({'variable':feature_names()}))")
    md("## 4 Algoritmos y configuraciones\n\nRandom Forest representa una referencia tabular no lineal, XGBoost combina árboles de forma secuencial y LSTM aprende una representación de seis meses de historia. La revisión de literatura y las referencias APA se incluyen en el informe final. Las reglas del reto prohíben AutoML; las configuraciones se definieron manualmente.")
    code("CONFIG = json.loads((ROOT / 'config/modelado.json').read_text())\nfor family in FAMILIES:\n    display(Markdown('### ' + LABELS[family]))\n    display(pd.DataFrame(CONFIG[family]))")
    md("## 5 Ejecución o reanudación del entrenamiento\n\nLos experimentos ya se ejecutaron y sus modelos están guardados. Active la siguiente variable para ejecutar el flujo y reutilizar sus checkpoints. El script aísla cada familia en un proceso para evitar conflictos de runtimes OpenMP en macOS. La selección se fija antes de la prueba reservada.")
    code("RUN_ENTRENAMIENTO = False\nif RUN_ENTRENAMIENTO:\n    subprocess.run([sys.executable, str(ROOT/'scripts/entrenar_modelos.py'), '--stage','all','--family','all'], cwd=ROOT, check=True)\nelse:\n    print('Se documenta la ejecución real guardada; no se repite el entrenamiento.')\nprint(json.loads((RESULTS/'estado.json').read_text())['entrenamiento_completo']['status'])")
    md("## 6 Resultados de ajuste y confirmación\n\nLa tabla reúne las nueve configuraciones evaluadas sobre las mismas filas. La confirmación de 2013 determina la familia recomendada. La prueba final no cambia retrospectivamente esta decisión.")
    code("experiments = pd.read_csv(RESULTS/'experimentos.csv')\nexperiments['orden'] = experiments.family.map({f:i for i,f in enumerate(FAMILIES)})\ndisplay(experiments.sort_values(['orden','configuration']).drop(columns='orden'))\nperformance = pd.read_csv(RESULTS/'metricas_modelos.csv')\ndisplay(performance[performance.stage=='confirmation'])\nprint('Recomendación fijada:', LABELS[SUMMARY['recommended_family']])\ndisplay(Image(filename=str(FIGURES/'11_aprendizaje_lstm.png'), width=950))")
    md("## 7 Prueba final reservada y comprobación de métricas\n\nSe recalcula el RMSE desde las predicciones individuales. Todos los modelos se evalúan con las mismas observaciones; se distingue el resultado final del ajuste de parámetros y de las predicciones no etiquetadas de Test.")
    code("display(performance[performance.stage=='holdout'])\ndisplay(pd.read_csv(RESULTS/'metricas_referencias.csv'))\npredictions = pd.read_parquet(RESULTS/'predicciones_prueba_completas.parquet')\nfor family in FAMILIES:\n    error = predictions[f'pred_{family}'].to_numpy(dtype=float) - predictions.target.to_numpy(dtype=float)\n    recalculated = np.sqrt(np.mean(error**2))\n    recorded = performance.loc[(performance.stage=='holdout') & (performance.family==family),'rmse'].iloc[0]\n    assert abs(recalculated-recorded)<1e-9\n    print(LABELS[family], 'RMSE verificado:', round(recalculated,6))\ndisplay(Image(filename=str(FIGURES/'03_comparacion_rmse.png'), width=950))\ndisplay(Image(filename=str(FIGURES/'04_eficiencia.png'), width=950))")
    md("## 8 Tiempo, regiones, disponibilidad y extremos\n\nUna mejora global debe interpretarse junto con los grupos donde el error aumenta. Las diferencias entre grupos son asociaciones predictivas; no aíslan un efecto causal del enmascaramiento.")
    code("for name in ['05_error_temporal.png','06_error_regional.png','07_error_disponibilidad.png','08_error_antiguedad.png','09_observado_predicho.png','10_residuos.png']:\n    display(Image(filename=str(FIGURES/name), width=950))\ndisplay(pd.read_csv(RESULTS/'metricas_extremos.csv'))\nprint('Cortes de extremos fijados en entrenamiento:', SUMMARY['extreme_thresholds_training'])")
    md("## 9 Incertidumbre e interpretación\n\nEl remuestreo circular usa bloques de tres meses observados y mantiene juntas las celdas del mismo mes. Un intervalo de diferencia que incluye cero no respalda un orden temporal estable. Las importancias de árboles se agrupan por dominio y no prueban causalidad.")
    code("uncertainty=json.loads((RESULTS/'incertidumbre_bloques.json').read_text())\nprint('Meses observados:', uncertainty['observed_months'], 'Remuestreos:',uncertainty['repetitions'])\ndisplay(pd.DataFrame(uncertainty['intervals']))\ndisplay(pd.DataFrame(uncertainty['paired_differences']))\ndisplay(Image(filename=str(FIGURES/'12_importancias.png'), width=950))")
    md("## 10 Predicciones de Test y aplicación\n\nSe reajustó cada configuración seleccionada con todas las etiquetas de Train.csv. Se entregan las columnas ID y Target para las 280 961 filas de Test. Estos archivos no permiten medir precisión sin sus etiquetas reales.\n\nLa aplicación se inicia con `python -m streamlit run app.py`. Permite explorar los datos, pronosticar una observación o un CSV y mostrar u ocultar métricas interactivas. El preprocesamiento es compartido con el entrenamiento.")
    code("rows=[]\nfor family in FAMILIES:\n    frame=pd.read_csv(RESULTS/f'submission_{family}.csv')\n    assert list(frame.columns)==['ID','Target']\n    assert len(frame)==AUDIT['test_rows'] and frame.ID.is_unique\n    assert np.isfinite(frame.Target).all()\n    rows.append({'algoritmo':LABELS[family],'filas':len(frame),'mínimo_predicho':frame.Target.min(),'máximo_predicho':frame.Target.max()})\ndisplay(pd.DataFrame(rows))\nprint('No se calcula RMSE para Test porque no contiene etiquetas.')")
    md("## 11 Conclusiones y reproducción\n\nLa comparación usa evaluación temporal y disponibilidad causal de entradas. La selección registrada en 2013 y el menor error final se presentan por separado. Los resultados no demuestran transferencia a regiones no observadas ni a todos los años futuros. Las versiones, semillas, huellas y parámetros quedan disponibles en los manifiestos.")
    code("display(Markdown(f\"Modelo recomendado antes de abrir la prueba: **{LABELS[SUMMARY['recommended_family']]}**. Menor RMSE final descriptivo: **{LABELS[SUMMARY['best_holdout_family_descriptive']]}**.\"))\ndisplay(pd.DataFrame(SUMMARY['holdout_results'])[['algorithm','rmse','mae','r2','improvement_vs_persistence_pct']])\ndisplay(pd.DataFrame(json.loads((RESULTS/'entorno.json').read_text())['versions'].items(),columns=['paquete','versión']))")
    md("## Referencias y materiales\n\nLa revisión bibliográfica completa y las citas APA se encuentran en `docs/Informe_Final_Parte2_TWS.md` y en el informe PDF/Word de `output/`. El código de entrenamiento se encuentra en `src/tws/training.py`, las arquitecturas en `src/tws/models.py` y `src/tws/neural.py`, y la preparación causal en `src/tws/data.py`.\n\nRepositorio: https://github.com/Javiervalladares1/CC3084-Proyecto2-Drought-EDA\n\nReto: https://zindi.world/competitions/one-step-ahead-of-drought-forecasting-global-water-storage-challenge")
    notebook = nbformat.v4.new_notebook(cells=cells)
    notebook.metadata['kernelspec'] = {'display_name':'Proyecto 2 Modelado','language':'python','name':'proyecto2-modelado'}
    notebook.metadata['language_info'] = {'name':'python','version':sys.version.split()[0]}
    kernel_root = ROOT/'tmp/jupyter/share/jupyter/kernels/proyecto2-modelado'
    kernel_root.mkdir(parents=True,exist_ok=True)
    (kernel_root/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],
                                                      'display_name':'Proyecto 2 Modelado','language':'python'}))
    os.environ['JUPYTER_PATH'] = str(ROOT/'tmp/jupyter/share/jupyter') + os.pathsep + os.environ.get('JUPYTER_PATH','')
    client = NotebookClient(notebook,timeout=300,kernel_name='proyecto2-modelado',resources={'metadata':{'path':str(ROOT)}})
    client.execute()
    output=ROOT/'Proyecto2_Resultados.ipynb'
    nbformat.write(notebook,output)
    assert all(cell.get('execution_count') is not None for cell in notebook.cells if cell.cell_type=='code')
    assert not any(o.output_type=='error' for cell in notebook.cells if cell.cell_type=='code' for o in cell.outputs)
    print(f'Notebook ejecutado: {output}')


if __name__ == '__main__':
    main()
