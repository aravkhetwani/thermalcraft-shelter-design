"""
Single-command reproduction of the full ML research pipeline:
dataset generation -> model training/evaluation -> optimization -> benchmark.

Usage (from the `Ansys simulation` directory):
    pip install -r research/requirements.txt
    python -m research.run_all
"""
from __future__ import annotations

try:
    from . import dataset, train, optimize, benchmark
except ImportError:
    import dataset, train, optimize, benchmark


def main():
    print("=" * 70)
    print("STEP 1/4: Generating synthetic dataset")
    print("=" * 70)
    dataset.main()

    print("\n" + "=" * 70)
    print("STEP 2/4: Training and evaluating surrogate models")
    print("=" * 70)
    train.main()

    print("\n" + "=" * 70)
    print("STEP 3/4: Surrogate-driven design optimization + simulator validation")
    print("=" * 70)
    optimize.main()

    print("\n" + "=" * 70)
    print("STEP 4/4: Surrogate vs. simulator speedup benchmark")
    print("=" * 70)
    benchmark.main()

    print("\nDone. See research/results/ for all metrics, and research/models/ for trained models.")


if __name__ == "__main__":
    main()
