"""Synthetic temperature/ionic-strength activity table; not measured data."""

from matintegrity.models.aqueous_tabulated_activity import (
    AqueousActivityCoefficientPoint,
    AqueousActivityCoefficientTemperatureSlice,
    AqueousSpeciesActivityCurve,
)


sodium_activity_curve = AqueousSpeciesActivityCurve(
    species_id="Na+",
    temperature_slices=(
        AqueousActivityCoefficientTemperatureSlice(
            temperature_K=278.15,
            points=(
                AqueousActivityCoefficientPoint(ionic_strength_mol_kg=0.0, activity_coefficient=1.0),
                AqueousActivityCoefficientPoint(ionic_strength_mol_kg=0.1, activity_coefficient=0.84),
                AqueousActivityCoefficientPoint(ionic_strength_mol_kg=0.5, activity_coefficient=0.70),
            ),
        ),
        AqueousActivityCoefficientTemperatureSlice(
            temperature_K=298.15,
            points=(
                AqueousActivityCoefficientPoint(ionic_strength_mol_kg=0.0, activity_coefficient=1.0),
                AqueousActivityCoefficientPoint(ionic_strength_mol_kg=0.1, activity_coefficient=0.86),
                AqueousActivityCoefficientPoint(ionic_strength_mol_kg=0.5, activity_coefficient=0.73),
            ),
        ),
        AqueousActivityCoefficientTemperatureSlice(
            temperature_K=318.15,
            points=(
                AqueousActivityCoefficientPoint(ionic_strength_mol_kg=0.0, activity_coefficient=1.0),
                AqueousActivityCoefficientPoint(ionic_strength_mol_kg=0.1, activity_coefficient=0.88),
                AqueousActivityCoefficientPoint(ionic_strength_mol_kg=0.5, activity_coefficient=0.76),
            ),
        ),
    ),
)

print(sodium_activity_curve.model_dump(mode="json"))
