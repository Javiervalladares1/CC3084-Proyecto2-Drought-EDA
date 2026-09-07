"""
Genera el informe final en .docx y en .pdf a partir de docs/Informe_Analisis_Exploratorio.md.

El Markdown es la única fuente: los dos formatos se derivan de él, de modo que no
puedan quedar desincronizados. Las figuras provienen de figures/, generadas por el
notebook.

Requiere pandoc y LibreOffice (soffice), ambos disponibles vía Homebrew.

Uso (desde la raíz del proyecto):
    python3 scripts/crear_informe.py
"""

from pathlib import Path
import shutil
import subprocess
import sys

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
FUENTE = DOCS / "Informe_Analisis_Exploratorio.md"
DOCX = DOCS / "Informe_Analisis_Exploratorio.docx"
PDF = DOCS / "Informe_Analisis_Exploratorio.pdf"


def requerir(programa):
    ruta = shutil.which(programa)
    if ruta is None:
        sys.exit(f"No se encontró '{programa}'. Instálelo con: brew install {programa}")
    return ruta


def main():
    requerir("pandoc")
    soffice = requerir("soffice")

    if not FUENTE.exists():
        sys.exit(f"No se encontró la fuente del informe: {FUENTE}")

    # Markdown -> Word. --resource-path permite resolver las rutas ../figures/.
    subprocess.run(
        ["pandoc", FUENTE.name, "-o", DOCX.name,
         "--resource-path", f".:{RAIZ}",
         "--syntax-highlighting", "tango"],
        cwd=DOCS, check=True,
    )
    print(f"Escrito: {DOCX.relative_to(RAIZ)}  ({DOCX.stat().st_size / 1024:.0f} KB)")

    # Word -> PDF, para que ambos entregables salgan del mismo archivo.
    subprocess.run(
        [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(DOCS), str(DOCX)],
        check=True, capture_output=True,
    )
    print(f"Escrito: {PDF.relative_to(RAIZ)}  ({PDF.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
