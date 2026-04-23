from __future__ import annotations

from src.scripts.smoke_validation_dataset import (
    describe_smoke_validation_dataset,
    ensure_smoke_validation_dataset,
)


def run() -> None:
    """Create or refresh the explicit local/staging smoke-validation dataset."""
    dataset = ensure_smoke_validation_dataset()
    for line in describe_smoke_validation_dataset(dataset):
        print(line)


if __name__ == '__main__':
    run()
