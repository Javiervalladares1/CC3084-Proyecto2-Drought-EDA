"""
Inspección inicial de los archivos crudos del reto.

Este script NO modifica los datos originales. Solo lee los archivos de
`data/raw/`, reporta su estructura real y guarda un resumen en
`outputs/inspeccion_datos.json` para que el notebook y el informe partan de
columnas verificadas y no de suposiciones.

Uso (desde la raíz del proyecto):
    python3 scripts/inspeccionar_datos.py
"""

from pathlib import Path
import json

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
CRUDOS = RAIZ / "data" / "raw"
SALIDAS = RAIZ / "outputs"

ARCHIVOS_ESPERADOS = ["Train.csv", "Test.csv", "SampleSubmission.csv"]
FILAS_MUESTRA = 200_000  # suficiente para tipos y rangos sin cargar 276 MB


def formato_tamano(bytes_):
    for unidad in ("B", "KB", "MB", "GB"):
        if bytes_ < 1024:
            return f"{bytes_:.1f} {unidad}"
        bytes_ /= 1024
    return f"{bytes_:.1f} TB"


def contar_filas(ruta):
    """Cuenta filas de datos sin cargar el archivo completo en memoria."""
    with open(ruta, "rb") as f:
        return sum(1 for _ in f) - 1  # se descuenta el encabezado


def inspeccionar(ruta):
    print(f"\n{'=' * 78}\n{ruta.name}\n{'=' * 78}")
    print(f"Tamaño en disco : {formato_tamano(ruta.stat().st_size)}")

    n_filas = contar_filas(ruta)
    print(f"Filas de datos  : {n_filas:,}")

    muestra = pd.read_csv(ruta, nrows=FILAS_MUESTRA)
    print(f"Columnas ({muestra.shape[1]}): {list(muestra.columns)}\n")

    print("Tipos inferidos y faltantes (sobre la muestra leída):")
    resumen = pd.DataFrame({
        "dtype": muestra.dtypes.astype(str),
        "faltantes": muestra.isna().sum(),
        "faltantes_%": (muestra.isna().mean() * 100).round(2),
        "n_unicos": muestra.nunique(dropna=True),
    })
    print(resumen.to_string())

    numericas = muestra.select_dtypes("number")
    if not numericas.empty:
        print("\nRangos de las variables numéricas:")
        print(numericas.describe().T[["count", "mean", "std", "min", "max"]].to_string())

    print("\nPrimeras 3 filas:")
    print(muestra.head(3).to_string())

    return {
        "archivo": ruta.name,
        "tamano_bytes": ruta.stat().st_size,
        "filas_totales": n_filas,
        "filas_muestreadas": int(len(muestra)),
        "columnas": list(muestra.columns),
        "dtypes": {c: str(t) for c, t in muestra.dtypes.items()},
        "faltantes_pct_muestra": {c: round(v, 4) for c, v in (muestra.isna().mean() * 100).items()},
    }


def main():
    SALIDAS.mkdir(parents=True, exist_ok=True)

    faltantes = [n for n in ARCHIVOS_ESPERADOS if not (CRUDOS / n).exists()]
    if faltantes:
        print("Faltan archivos en data/raw/: " + ", ".join(faltantes))
        print("Consulte data/raw/README.md para las instrucciones de descarga.")
        if len(faltantes) == len(ARCHIVOS_ESPERADOS):
            return

    reporte = [inspeccionar(CRUDOS / n) for n in ARCHIVOS_ESPERADOS if (CRUDOS / n).exists()]

    destino = SALIDAS / "inspeccion_datos.json"
    destino.write_text(json.dumps(reporte, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResumen guardado en: {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
