"""Empaqueta solo los productos finales y recursos de ejecución de la parte 2."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'entrega_parte2'
ZIP = ROOT / 'output/Entrega_Parte2_TWS.zip'


def copy(relative):
    source = ROOT / relative
    target = DEST / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def build_directory():
    DEST.mkdir(exist_ok=True)
    for name in ['app.py', 'Proyecto2_Resultados.ipynb', 'requirements.txt',
                 'requirements-modelado.txt', 'requirements-modelado.lock.txt',
                 'requirements-documentos.txt', 'pytest.ini', '.streamlit/config.toml',
                 'config/modelado.json', 'docs/PLAN_PARTE2.md', 'docs/GUIA_PARTE2.md',
                 'docs/VERIFICACION_PARTE2.md', 'docs/Revision_Bibliografica_TWS.md',
                 'docs/Informe_Final_Parte2_TWS.md', 'docs/Guion_Presentacion_Resultados.json',
                 'output/word/Informe_Final_Parte2_TWS.docx',
                 'output/pdf/Informe_Final_Parte2_TWS.pdf',
                 'output/presentacion/Proyecto2_Resultados_TWS_Final.pptx']:
        copy(Path(name))
    for directory, suffixes in [('src', {'.py'}), ('tests', {'.py'}),
                               ('figures/resultados', {'.png','.jpg'}),
                               ('outputs/modelado', {'.json','.csv','.parquet'})]:
        for source in sorted((ROOT / directory).rglob('*')):
            if source.is_file() and source.suffix in suffixes and '__pycache__' not in source.parts:
                copy(source.relative_to(ROOT))
    script_names = ['entrenar_modelos.py', 'analizar_resultados.py', 'preparar_datos_aplicacion.py',
                    'generar_notebook_resultados.py', 'crear_informe_resultados.py',
                    'formato_informe_resultados.py', 'crear_revision_word.py',
                    'crear_presentacion_resultados.mjs', 'preparar_entrega_parte2.py']
    for name in script_names:
        copy(Path('scripts') / name)
    for stage in ['confirmation','holdout','production','tuning']:
        for source in sorted((ROOT / 'models' / stage).rglob('*')):
            if source.is_file() and (stage != 'tuning' or source.suffix == '.json'):
                copy(source.relative_to(ROOT))
    raw = DEST / 'data/raw'
    raw.mkdir(parents=True,exist_ok=True)
    (raw / 'README.md').write_text('Descargue Train.csv y Test.csv desde el reto Zindi para reentrenar. La aplicación usa la historia observable incluida en outputs/modelado/.\n',encoding='utf-8')
    (DEST / 'README.md').write_text('''# Entrega de la parte 2

Pronóstico del almacenamiento de agua con Random Forest, XGBoost y LSTM.

Abra el informe editable en `output/word/`, el PDF en `output/pdf/` y la presentación en `output/presentacion/`. El notebook conserva la ejecución real.

Para iniciar la aplicación, cree un entorno con Python 3.12, instale `requirements-modelado.lock.txt` y ejecute `python -m streamlit run app.py` desde esta carpeta. La aplicación utiliza los modelos entrenados y la historia observable incluidos, sin requerir los CSV originales. Lea `docs/GUIA_PARTE2.md` para el recorrido completo y la reproducción.

`docs/VERIFICACION_PARTE2.md` identifica evidencias y límites de la evaluación. `MANIFIESTO_SHA256.json` permite comprobar integridad de los archivos.

Repositorio: https://github.com/Javiervalladares1/CC3084-Proyecto2-Drought-EDA

El enlace de Google Drive debe ser el real del trabajo grupal. El Word está preparado para subir o importar en esa carpeta.
''',encoding='utf-8')
    notes=json.loads((DEST/'docs/Guion_Presentacion_Resultados.json').read_text())
    script=['# Guion de presentación de resultados','Duración sugerida total: 15 minutos. Ajustar a la distribución de tiempo indicada en clase.']
    for row in notes:
        script.extend([f"## Diapositiva {row['slide']} {row['title']}",f"Tiempo sugerido: {row['seconds']} segundos.",row['notes']])
    (DEST/'docs/Guion_Presentacion_Resultados.md').write_text('\n\n'.join(script)+'\n',encoding='utf-8')


def make_zip():
    records=[]
    for source in sorted(DEST.rglob('*')):
        if source.is_file() and source.name!='MANIFIESTO_SHA256.json' and '__pycache__' not in source.parts and '.pytest_cache' not in source.parts:
            digest=hashlib.sha256()
            with source.open('rb') as stream:
                for chunk in iter(lambda:stream.read(8*1024*1024),b''):digest.update(chunk)
            records.append({'path':source.relative_to(DEST).as_posix(),'bytes':source.stat().st_size,'sha256':digest.hexdigest()})
    (DEST/'MANIFIESTO_SHA256.json').write_text(json.dumps({'files':records},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    ZIP.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(ZIP,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5) as archive:
        for row in records:
            source=DEST/row['path'];archive.write(source,Path('Entrega_Parte2_TWS')/row['path'])
        archive.write(DEST/'MANIFIESTO_SHA256.json','Entrega_Parte2_TWS/MANIFIESTO_SHA256.json')
    with zipfile.ZipFile(ZIP) as archive:
        assert archive.testzip() is None
    print(json.dumps({'zip':str(ZIP),'files':len(records)+1,'bytes':ZIP.stat().st_size},ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--directory-only',action='store_true');parser.add_argument('--zip-only',action='store_true');args=parser.parse_args()
    if not args.zip_only:build_directory()
    if not args.directory_only:make_zip()
