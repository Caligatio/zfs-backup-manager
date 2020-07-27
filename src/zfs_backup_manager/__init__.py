import argparse
import logging
import pathlib
import subprocess
import sys
from collections import defaultdict
from datetime import date, datetime
from json import dumps
from shutil import which
from typing import DefaultDict, List, cast

import toml

from .types import Config, ValidatedDatasetEntry

DEFAULT_DOM = 1
DEFAULT_DOW = 7
DEFAULT_RECURSIVE = True
DEFAULT_KEEP_DAYS = 0
DEFAULT_KEEP_WEEKS = 0
DEFAULT_KEEP_MONTHS = 0


def get_sorted_snapshots(config: Config) -> DefaultDict[str, List[date]]:
    """
    Queries ZFS and returns a dictionary containing managed snapshots.

    :return: Sorted dictionary of dataset->datetime mappings
    """
    ret_val: DefaultDict[str, List[date]] = defaultdict(list)

    stdout = subprocess.check_output(["zfs", "list", "-t", "snapshot"], stderr=subprocess.STDOUT, encoding="utf8")
    if stdout == "no datasets available":
        return ret_val

    lines = stdout.splitlines()
    # skip the header
    for line in lines[1:]:
        parts = line.split()
        dataset, timestamp = parts[0].split("@")
        try:
            parsed_timestamp = datetime.strptime(timestamp, "{}%Y%m%d".format(config.get("snapshot_prefix", "")))
            ret_val[dataset].append(parsed_timestamp.date())
        except ValueError:
            pass

    # Sort the dates in descending order
    for dataset in ret_val:
        ret_val[dataset].sort(reverse=True)

    return ret_val


def get_dataset_configs(config: Config) -> List[ValidatedDatasetEntry]:
    """
    Validates the configurations for datasets for required key(s) and inherits defaults, as needed.

    :param config: The backup manager configuration.
    :return: Configurations for the various datasets.
    """
    ret_val = []
    for i, dataset in enumerate(config.get("datasets", [])):
        try:
            dataset_name = dataset["name"]
        except KeyError as exc:
            raise RuntimeError(f"Dataset config #{i} must have a name") from exc

        validated_dict: ValidatedDatasetEntry = {
            "name": dataset_name,
            "recursive": dataset.get("recursive", config.get("recursive", DEFAULT_RECURSIVE)),
            "dom": dataset.get("dom", config.get("dom", DEFAULT_DOM)),
            "dow": dataset.get("dow", config.get("dow", DEFAULT_DOW)),
            "keep_days": dataset.get("keep_days", config.get("keep_days", DEFAULT_KEEP_DAYS)),
            "keep_weeks": dataset.get("keep_weeks", config.get("keep_weeks", DEFAULT_KEEP_WEEKS)),
            "keep_months": dataset.get("keep_months", config.get("keep_months", DEFAULT_KEEP_MONTHS)),
        }
        ret_val.append(validated_dict)

    return ret_val


def main(config: Config, dry_run: bool = False) -> int:
    """
    Main entrypoint into the program. Takes specified snapshots if they don't exist and deletes old entrys as specified.

    :param config: The backup manager configuration.
    :param dry_run: Flag to indicate that no commands should be run
    :return: 0 on success, non-zero on failure
    """
    zfs_path = which("zfs")
    if zfs_path is None:
        logging.critical("zfs command cannot be found")
        return 2

    try:
        dataset_configs = get_dataset_configs(config)
    except RuntimeError as exc:
        logging.critical(exc)
        return 3

    logging.debug(
        "Parsed dataset configs: \n\t%s", "\n\t".join((dumps(config) for config in dataset_configs)),
    )

    today = datetime.now().date()

    for dataset_config in dataset_configs:
        if not (
            dataset_config["keep_days"] > 0
            or (dataset_config["keep_weeks"] > 0 and today.isoweekday() == dataset_config["dow"])
            or (dataset_config["keep_months"] > 0 and today.day == dataset_config["dom"])
        ):
            logging.debug("No snapshot scheduled for dataset %s", dataset_config["name"])
            continue

        today_snapshot_name = "{}@{}{}".format(
            dataset_config["name"], config.get("snapshot_prefix", ""), today.strftime("%Y%m%d")
        )

        if today in get_sorted_snapshots(config)[dataset_config["name"]]:
            logging.warning("Snapshot %s already exists", today_snapshot_name)
            continue

        cmd = ["zfs", "snapshot", today_snapshot_name]
        if dataset_config["recursive"]:
            cmd.insert(2, "-r")

        logging.info("Creating snapshot %s", today_snapshot_name)
        logging.debug("Running command: %s", cmd)
        if not dry_run:
            try:
                subprocess.check_output(cmd, stderr=subprocess.PIPE, encoding="utf-8")
            except subprocess.CalledProcessError as exc:
                logging.error("zfs command failed with error: %s", exc.stderr)

        # Cleanup snapshots
        dataset_snapshots = get_sorted_snapshots(config)[dataset_config["name"]]
        keep_daily_set = set(dataset_snapshots[: dataset_config["keep_days"]])
        keep_weekly_set = set(
            [snapshot for snapshot in dataset_snapshots if snapshot.isoweekday() == dataset_config["dow"]][
                : dataset_config["keep_weeks"]
            ]
        )
        keep_monthly_set = set(
            [snapshot for snapshot in dataset_snapshots if snapshot.day == dataset_config["dom"]][
                : dataset_config["keep_months"]
            ]
        )
        keep_set = keep_daily_set | keep_weekly_set | keep_monthly_set

        for snapshot in set(dataset_snapshots) - keep_set:
            delete_snapshot_name = "{}@{}{}".format(
                dataset_config["name"], config.get("snapshot_prefix", ""), snapshot.strftime("%Y%m%d")
            )

            cmd = [
                "zfs",
                "destroy",
                delete_snapshot_name,
            ]
            if dataset_config["recursive"]:
                cmd.insert(2, "-r")

            logging.info("Destroying snapshot %s", delete_snapshot_name)
            logging.debug("Running command: %s", cmd)
            if not dry_run:
                try:
                    subprocess.check_output(cmd, stderr=subprocess.PIPE, encoding="utf-8")
                except subprocess.CalledProcessError as exc:
                    logging.error("zfs command failed with error: %s", exc.stderr)

    return 0


def cli() -> None:
    """CLI entrypoint.  Reads arguments from the command line and processes+passes them to `main`."""
    parser = argparse.ArgumentParser(description="Manages monthly, weekly, and daily backups using ZFS snapshots")
    parser.add_argument("config", type=pathlib.Path, help="Path to configuration file")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Flag to disable changes from being made.  Recommend setting log level to DEBUG",
    )
    log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    parser.add_argument(
        "--logging", choices=log_levels, help="Logging level, overrides the config file value",
    )

    args = parser.parse_args()
    config = cast(Config, toml.load(args.config))

    log_level = args.logging or config.get("logging", "INFO")
    if log_level not in log_levels:
        logging.basicConfig(level=logging.CRITICAL, format="%(levelname)s - %(message)s")
        logging.critical("log level must be one of: %s", ", ".join(log_levels))
        sys.exit(1)
    else:
        logging.basicConfig(level=getattr(logging, log_level), format="%(levelname)s - %(message)s")

    sys.exit(main(config, args.dry_run))


if __name__ == "__main__":
    cli()
