"""
Verifica que el notebook cubra cada criterio de la rúbrica del Proyecto 2.

Comprueba la presencia de las secciones y de las técnicas exigidas por la guía
del curso, además de tres salvaguardas metodológicas: que no se afirme
causalidad, que los valores atípicos no se hayan eliminado y que las limitaciones
estén declaradas.

Uso (desde la raíz del proyecto):
    python3 scripts/verificar_rubrica.py

Devuelve código de salida 1 si algún criterio no está cubierto.
"""

from pathlib import Path
import json
import re
import sys

RAIZ = Path(__file__).resolve().parent.parent
NOTEBOOK = RAIZ / "Proyecto2_Analisis_Exploratorio.ipynb"

# (criterio, puntos de la rúbrica, texto que lo evidencia, dónde buscarlo)
CRITERIOS = [
    ("Situación problemática",       10, "## 3. Situación problemática",                 "md"),
    ("Problema científico",          10, "## 4. Problema científico",                    "md"),
    ("Objetivo general",             10, "### 5.1 Objetivo general",                     "md"),
    ("Objetivos específicos",         0, "### 5.2 Objetivos específicos",                "md"),
    ("Variables y observaciones",    20, "## 8. Descripción de los datasets",            "md"),
    ("Tipos de cada variable",        0, "## 9. Identificación y clasificación",         "md"),
    ("Limpieza y preprocesamiento",   0, "## 11. Limpieza y preprocesamiento",           "md"),
    ("Estadística descriptiva",      30, "describe()",                                   "code"),
    ("Histogramas",                   0, ".hist(",                                       "code"),
    ("Diagramas de caja y bigotes",   0, ".boxplot(",                                    "code"),
    ("Gráficos de dispersión",        0, ".scatter(",                                    "code"),
    ("Matriz de correlación",         0, 'corr(method="pearson")',                       "code"),
    ("Análisis de outliers",          0, "## 15. Detección y análisis de valores",       "md"),
    ("Decisión sobre faltantes",      0, "### 10.1 Los faltantes no están donde",        "md"),
    ("Variables categóricas",         0, "## 13. Análisis de variables categóricas",     "md"),
    ("Gráficos de barras",            0, ".bar(",                                        "code"),
    ("Tablas de frecuencia",          0, "value_counts()",                               "code"),
    ("Tablas de proporciones",        0, "value_counts(normalize=True)",                 "code"),
    ("Hallazgos",                    20, "## 21. Hallazgos principales",                 "md"),
    ("Conclusiones",                  0, "## 22. Conclusiones",                          "md"),
    ("Próximos pasos",                0, "## 23. Próximos pasos",                        "md"),
]

SALVAGUARDAS = [
    ("No se afirma causalidad",      "En ningún punto se establece causalidad"),
    ("Outliers no eliminados",       "no se elimina ningún valor atípico"),
    ("Limitaciones declaradas",      "### Limitaciones del conjunto"),
    ("Interpretación de hallazgos",  "### Los ocho hallazgos del análisis"),
]


def normalizar(texto):
    """Colapsa los saltos de línea para que una frase partida en dos renglones
    del Markdown se siga encontrando."""
    return re.sub(r"\s+", " ", texto)


def main():
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    md = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "markdown")
    code = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")
    fuentes = {"md": normalizar(md), "code": code}

    sin_salida = [i for i, c in enumerate(nb["cells"])
                  if c["cell_type"] == "code" and not c.get("outputs")]

    print(f"Notebook: {NOTEBOOK.name}  ({len(nb['cells'])} celdas)\n")
    print(f"{'Criterio de la rúbrica':<32} {'Puntos':>7}  Estado")
    print("-" * 52)

    faltantes = []
    for nombre, puntos, evidencia, donde in CRITERIOS:
        buscado = normalizar(evidencia) if donde == "md" else evidencia
        ok = buscado in fuentes[donde]
        etiqueta = f"{puntos} pts" if puntos else ""
        print(f"{nombre:<32} {etiqueta:>7}  {'OK' if ok else 'FALTA'}")
        if not ok:
            faltantes.append(nombre)

    print("\nSalvaguardas metodológicas")
    print("-" * 52)
    for nombre, evidencia in SALVAGUARDAS:
        ok = normalizar(evidencia).lower() in fuentes["md"].lower()
        print(f"{nombre:<32} {'':>7}  {'OK' if ok else 'FALTA'}")
        if not ok:
            faltantes.append(nombre)

    print("\nReproducibilidad")
    print("-" * 52)
    ok_salidas = not sin_salida
    print(f"{'Todas las celdas ejecutadas':<32} {'':>7}  {'OK' if ok_salidas else 'FALTA'}")
    if not ok_salidas:
        print(f"  Celdas sin salida: {sin_salida}")
        faltantes.append("Celdas sin ejecutar")

    print()
    if faltantes:
        print("Criterios sin cubrir:", ", ".join(faltantes))
        sys.exit(1)
    print("Todos los criterios de la rúbrica están cubiertos.")


if __name__ == "__main__":
    main()
