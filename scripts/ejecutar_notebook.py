"""
Ejecuta el notebook principal de principio a fin y guarda la versión ejecutada.

Sirve como verificación de reproducibilidad: si alguna celda falla, el script
reporta la celda y el error en lugar de dejar el notebook a medias.

Uso (desde la raíz del proyecto):
    python3 scripts/ejecutar_notebook.py
"""

from pathlib import Path
import sys

import nbformat as nbf
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

RAIZ = Path(__file__).resolve().parent.parent
NOTEBOOK = RAIZ / "Proyecto2_Analisis_Exploratorio.ipynb"


def main():
    nb = nbf.read(NOTEBOOK, as_version=4)
    cliente = NotebookClient(
        nb,
        timeout=1800,
        kernel_name="python3",
        resources={"metadata": {"path": str(RAIZ)}},
    )

    print(f"Ejecutando {NOTEBOOK.name} ({len(nb.cells)} celdas)...")
    try:
        cliente.execute()
    except CellExecutionError as error:
        nbf.write(nb, NOTEBOOK)
        print("\nLa ejecución falló:\n", error, file=sys.stderr)
        sys.exit(1)

    nbf.write(nb, NOTEBOOK)
    print("Ejecución completa sin errores.")


if __name__ == "__main__":
    main()
