"""A science-only feature must not make the base installation unimportable."""

import subprocess
import sys


def test_registry_and_basic_calculation_work_when_optional_imports_are_blocked():
    program = """
import importlib.abc
import sys
class NoOptionalScience(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'scipy','CoolProp','pandas','rainflow','h5py','pydicom','openpyxl','DefDAP'}:
            raise ModuleNotFoundError('Optional science library deliberately unavailable: '+fullname)
sys.meta_path.insert(0, NoOptionalScience())
from matintegrity import evaluate
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext
assert len(default_registry().list_models()) >= 757
result=evaluate('corrosion.coupon_loss',dict(mass_loss_kg=0.001,exposed_area_m2=0.01,density_kg_m3=1000.,duration_s=100.),RunContext(asset_id='authored',location_id='authored',time_basis='seconds'))
assert result.status=='computed'
assert abs(result.values['mean_penetration_m']-0.0001)<1e-15
"""
    result = subprocess.run([sys.executable, "-I", "-c", program], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
