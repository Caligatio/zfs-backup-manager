# ZFS Backup Manager
ZFS Backup Manger (zbm) is a simple Python program to help manage daily, weekly, and monthly ZFS backup snapshots.  It
is primarily designed to be run via cron and is only tested on Linux.

## Usage
Upon installation, an executable should be installed called `zfs_backup_manager` that is the main entrypoint.  It
requires a single positional argument which is the path to the config file (example below) but also has several optional
arguments that be explored by running it with `--help`.

## Config File
Below is an example config TOML file that illustrates all the available options.

```toml
# day of month is the date that should be considered as a monthly candidate, defaults to 1 (1st of month)
dom = 1
# day of week is the date that should be considered as a weekly candidate, defaults to 0 (Sunday)
dow = 0

# Number of days/weeks/months to keep, all default to 0
keep_days = 7
keep_weeks = 4
keep_months = 3

# recursive defaults to true, this essentially adds the "-r" flag to the zfs commands
recursive = true

# snapshots are prefixed with this, recommend non-empty value to help idenify zbm-controlled snapshots
snapshot_prefix = "zbm-"

# Must be one of DEBUG, INFO, WARNING, ERROR, or CRITICAL
logging = "INFO"

[[datasets]]
# This is the pool/dataset name
name = "tank/home"

[[datasets]]
name = "tank/var"
# This overwrites global value
recursive = false
# These also overwrite the global values
keep_days = 1
keep_months = 0
```

## Known Shortcomings
Below are known shortcomings that are not planned to be fixed.

### Nested Datasets
Controlling multiple levels in a nested dataset hierarchy while using "recursive" can cause undesirable behavior. For
instance, setting a fewer number of `keep_days` on `tank/var` with `recursive = true` may interfere if another dataset
like `tank/var/log` has a greater `keep_days` value.

### Changing `snapshot_prefix`
If `snapshot_prefix` is changed, any previously created snapshots are effectively "invisible" to future
`zfs_backup_manager` invocations.  It is up to the user to manually destroy previous snapshots if desired.


### `--dry-run` option is incomplete
Due to the order of how snapshots are created then evaluated for deletion, the `--dry-run` option won't show any
deletions that would have depended on a snapshot that was created during the same `zfs_backup_manager` execution.
