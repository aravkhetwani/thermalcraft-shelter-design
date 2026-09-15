"""Train/validation/test split integrity tests."""
from research.dataset import generate_dataset
from research.features import engineer_features
from research.train import split_indices


def test_splits_are_disjoint_and_cover_all_rows():
    df = engineer_features(generate_dataset(n_samples=500, seed=9))
    train_idx, val_idx, test_idx = split_indices(df, seed=42)

    train_set, val_set, test_set = set(train_idx), set(val_idx), set(test_idx)
    assert train_set.isdisjoint(val_set)
    assert train_set.isdisjoint(test_set)
    assert val_set.isdisjoint(test_set)
    assert train_set | val_set | test_set == set(df.index)


def test_split_proportions_approximately_70_15_15():
    df = engineer_features(generate_dataset(n_samples=2000, seed=9))
    train_idx, val_idx, test_idx = split_indices(df, seed=42)
    n = len(df)
    assert abs(len(train_idx) / n - 0.70) < 0.02
    assert abs(len(val_idx) / n - 0.15) < 0.02
    assert abs(len(test_idx) / n - 0.15) < 0.02


def test_split_is_reproducible_given_same_seed():
    df = engineer_features(generate_dataset(n_samples=300, seed=9))
    a = split_indices(df, seed=42)
    b = split_indices(df, seed=42)
    for idx_a, idx_b in zip(a, b):
        assert list(idx_a) == list(idx_b)
