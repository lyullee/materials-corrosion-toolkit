"""Setuptools build hook that prevents stale catalogs entering an installed wheel."""

import importlib.util
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py

_release_script = Path(__file__).resolve().parent / "scripts" / "build_release.py"
_spec = importlib.util.spec_from_file_location("matintegrity_build_release", _release_script)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load release catalog validator: {_release_script}")
_release_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_release_module)


class CatalogCheckedBuildPy(build_py):
    def run(self):
        _release_module.validate_catalog_sync(Path(__file__).resolve().parent)
        super().run()


setup(cmdclass={"build_py": CatalogCheckedBuildPy})
