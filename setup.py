from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="zfs-backup-manager",
    version="0.1.0",
    description="Python program which manages monthly, weekly, and daily backups using ZFS snapshots",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Caligatio/zfs-backup-manager",
    author="Brian Turek",
    author_email="brian.turek@gmail.com",
    license="Unlicense",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Archiving",
        "Topic :: System :: Archiving :: Backup",
        "License :: The Unlicense",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3 :: Only",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    package_data={"zfs_backup_manager": ["py.typed"]},
    python_requires=">=3.6, <4",
    install_requires=["mypy_extensions;python_version<'3.8'", "toml"],
    entry_points={"console_scripts": ["zfs_backup_manager=zfs_backup_manager:cli"]},
)
