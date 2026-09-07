"""
Arma la carpeta `repo/` con todo lo que se entrega del Proyecto 2.

Parte de los archivos versionados en git —que ya excluyen los CSV del reto— y
quita el material que no es obra del grupo: los notebooks de ejemplo del curso y
el PDF del enunciado. El resultado es una carpeta autocontenida con el código,
los productos del análisis y los documentos finales.

La carpeta se reconstruye desde cero en cada ejecución, así que nunca queda
desactualizada respecto del proyecto.

Uso (desde la raíz del proyecto):
    python3 scripts/preparar_entrega.py
"""

from pathlib import Path
import json
import shutil
import subprocess
import sys

RAIZ = Path(__file__).resolve().parent.parent
ENTREGA = RAIZ / "repo"

# Material que el curso proporcionó: sirvió de referencia pero no se entrega.
EXCLUIR = {
    "Ejemplo CNN gatos y perros.ipynb",
    "Ejemplo series de tiempo LSTM.ipynb",
    "EjemploGIS_Sentinel2.ipynb",
    "Practica01_Incendios.ipynb",
    "Proyecto 2. Análisis Exploratorio. 2026.pdf",
}

CATEGORIAS = [
    ("Notebook del análisis",  lambda r: r.suffix == ".ipynb"),
    ("Código (scripts)",       lambda r: r.parts[0] == "scripts"),
    ("Documentos finales",     lambda r: r.parts[0] == "docs"),
    ("Figuras del análisis",   lambda r: r.parts[0] == "figures" and r.suffix == ".png"),
    ("Tablas del análisis",    lambda r: r.parts[0] == "outputs" and r.suffix == ".csv"),
    ("Instrucciones de datos", lambda r: r.parts[0] == "data" and r.name == "README.md"),
    ("Configuración",          lambda r: len(r.parts) == 1
                                         and r.name in {"README.md", "requirements.txt", ".gitignore"}),
    ("Marcadores de carpeta",  lambda r: r.name == ".gitkeep"),
]


def archivos_versionados():
    salida = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=RAIZ, check=True, capture_output=True, text=True,
    ).stdout
    return [Path(p) for p in salida.split("\0") if p]


def avisar_pendientes():
    """La entrega se arma con lo versionado. Un archivo sin commitear quedaría
    fuera sin que nadie se entere, así que se avisa antes de copiar."""
    salida = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=RAIZ, check=True, capture_output=True, text=True,
    ).stdout.strip()
    if not salida:
        return
    print("Aviso: hay cambios sin commitear. La entrega se arma con lo que está")
    print("versionado, así que estos archivos NO se incluirán tal como están:\n")
    for linea in salida.splitlines():
        print(f"      {linea}")
    print()


def ajustar_readme(destino):
    """El README del proyecto menciona los ejemplos de clase, que no se copian."""
    ruta = destino / "README.md"
    if not ruta.exists():
        return
    texto = ruta.read_text(encoding="utf-8")
    sobra = """└── *.ipynb                 Ejemplos de clase (referencia metodológica, sin modificar)
"""
    texto = texto.replace(sobra, "")
    texto = texto.replace(
        """Los notebooks `EjemploGIS_Sentinel2.ipynb`, `Practica01_Incendios.ipynb`,
`Ejemplo series de tiempo LSTM.ipynb` y `Ejemplo CNN gatos y perros.ipynb` son
material del curso y se conservan **sin modificaciones** como referencia
metodológica.""",
        """Esta carpeta contiene únicamente el trabajo del grupo. Los notebooks de
ejemplo del curso y el PDF del enunciado quedaron fuera a propósito: sirvieron
como referencia metodológica pero no forman parte de la entrega.""",
    )
    ruta.write_text(texto, encoding="utf-8")


def main():
    avisar_pendientes()
    rutas = [r for r in archivos_versionados() if r.name not in EXCLUIR]
    omitidos = [r for r in archivos_versionados() if r.name in EXCLUIR]

    if ENTREGA.exists():
        shutil.rmtree(ENTREGA)

    copiados, pesos = [], 0
    for relativa in rutas:
        origen = RAIZ / relativa
        if not origen.exists():
            continue
        destino = ENTREGA / relativa
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origen, destino)
        copiados.append(relativa)
        pesos += origen.stat().st_size

    ajustar_readme(ENTREGA)

    print(f"Carpeta de entrega: {ENTREGA.relative_to(RAIZ)}/\n")
    for etiqueta, criterio in CATEGORIAS:
        del_grupo = [r for r in copiados if criterio(r)]
        if del_grupo:
            print(f"  {etiqueta:<24} {len(del_grupo):>3} archivo(s)")

    sin_clasificar = [
        r for r in copiados
        if not any(c(r) for _, c in CATEGORIAS)
    ]
    if sin_clasificar:
        print(f"  {'Otros':<24} {len(sin_clasificar):>3} archivo(s)")
        for r in sin_clasificar:
            print(f"      {r}")

    print(f"\n  Total: {len(copiados)} archivos, {pesos / 1024**2:.1f} MB")

    # El notebook debe entregarse ejecutado: quien lo revise tiene que ver los
    # resultados sin volver a correrlo. Regenerarlo con construir_notebook.py
    # dentro de esta carpeta borraría las salidas, así que se comprueba aquí.
    notebook = ENTREGA / "Proyecto2_Analisis_Exploratorio.ipynb"
    celdas = json.loads(notebook.read_text(encoding="utf-8"))["cells"]
    codigo = [c for c in celdas if c["cell_type"] == "code"]
    sin_salida = [c for c in codigo if not c.get("outputs")]
    print(f"\n  Notebook: {len(codigo)} celdas de código, "
          f"{len(codigo) - len(sin_salida)} con salida")
    if sin_salida:
        sys.exit(f"  ERROR: {len(sin_salida)} celdas sin salida. El notebook debe "
                 f"entregarse ejecutado.\n  Corra: python3 scripts/ejecutar_notebook.py")
    print(f"\n  Excluido (material del curso, no es obra del grupo):")
    for r in omitidos:
        print(f"      {r}")


if __name__ == "__main__":
    main()
