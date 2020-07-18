import sys
from typing import List

if sys.version_info >= (3, 8):
    from typing import Literal, TypedDict
else:
    from mypy_extensions import Literal, TypedDict


class _DatasetEntryBase(TypedDict):
    """Bare minimum necessary keys for a dataset entry."""

    name: str


class DatasetEntry(_DatasetEntryBase, total=False):
    """Dataset entry with all optional keys."""

    recursive: bool
    keep_days: int
    keep_weeks: int
    keep_months: int
    dow: int
    dom: int


class ValidatedDatasetEntry(_DatasetEntryBase):
    """Dataset entry with all ultimately needed keys present."""

    recursive: bool
    keep_days: int
    keep_weeks: int
    keep_months: int
    dow: int
    dom: int


class Config(TypedDict, total=False):
    """Dictionary-equivalent to the config file with all possible keys present."""

    dom: int
    dow: int
    keep_days: int
    keep_weeks: int
    keep_months: int
    recursive: bool
    datasets: List[DatasetEntry]
    snapshot_prefix: str
    logging: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
