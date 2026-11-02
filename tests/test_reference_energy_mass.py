import pytest
from pydantic import ValidationError

from matintegrity.models.inspection import ReferenceEnergyMass, reference_energy_mass


def test_declared_energy_and_reference_preserve_energy_balance_and_identity():
    request = ReferenceEnergyMass(energy_J=2e6, reference_specific_energy_J_kg=4e6,
                                  reference_id="synthetic-reference", energy_basis="declared available work")
    result = reference_energy_mass(request)
    assert result.values["reference_equivalent_mass_kg"] == pytest.approx(0.5)
    assert result.values["reference_equivalent_mass_kg"] * 4e6 == pytest.approx(2e6)
    assert result.values["reference_id"] == "synthetic-reference"
    assert result.values["energy_basis"] == "declared available work"


def test_zero_energy_has_zero_equivalent_mass():
    result = reference_energy_mass(ReferenceEnergyMass(
        energy_J=0.0, reference_specific_energy_J_kg=4e6,
        reference_id="synthetic-reference", energy_basis="declared available work",
    ))
    assert result.values["reference_equivalent_mass_kg"] == 0.0


@pytest.mark.parametrize("energy,reference", [(-1.0, 4e6), (1.0, 0.0), (float("inf"), 4e6)])
def test_invalid_energy_or_reference_is_rejected(energy, reference):
    with pytest.raises(ValidationError):
        ReferenceEnergyMass(energy_J=energy, reference_specific_energy_J_kg=reference,
                            reference_id="synthetic-reference", energy_basis="declared available work")
