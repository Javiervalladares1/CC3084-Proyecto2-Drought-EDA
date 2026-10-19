"""Proceso aislado de inferencia para evitar conflictos de OpenMP en macOS."""
import argparse
import numpy as np

from .models import load_bundle
from .utils import FAMILIES, MODELS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--family", choices=FAMILIES, required=True)
    parser.add_argument("--stage", choices=["production", "holdout", "confirmation"], default="production")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    model = load_bundle(MODELS / args.stage / args.family)
    X = np.load(args.input, mmap_mode="r")
    prediction = model.predict(X)
    np.save(args.output, prediction)


if __name__ == "__main__":
    main()
