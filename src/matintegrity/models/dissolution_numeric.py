"""Registry adapter for signed coupled lateral-wall metal-loss exchange."""

from ..contracts import Calculation
from ..dissolution_adapter import CoupledWallMetalLossRequest, coupled_wall_metal_loss
from ..registry import ModelSpec


def specifications():
    def evaluate(request):
        result = coupled_wall_metal_loss(request)
        status = result.pop("status")
        wall_result = result.get("wall_metal_loss")
        interpretation = wall_result.get("interpretation") if isinstance(wall_result, dict) else None
        return Calculation(status=status, values=result, notes=(interpretation,) if interpretation else ())

    return [
        ModelSpec(
            "corrosion.coupled_wall_metal_loss",
            CoupledWallMetalLossRequest,
            evaluate,
            {
                "wall_metal_loss.elapsed_time_s": "s",
                "wall_metal_loss.reactive_wall_area_m2": "m2",
                "wall_metal_loss.reactive_wall_area_over_reference_area": "1",
                "wall_metal_loss.history.net_metal_amount_per_reference_area_mol_m2": "mol/m2",
                "wall_metal_loss.history.net_metal_amount_mol": "mol",
                "wall_metal_loss.history.net_mass_loss_kg": "kg",
                "wall_metal_loss.history.net_volume_change_m3": "m3",
                "wall_metal_loss.history.signed_area_average_recession_m": "m",
            },
            (
                "Signed integrated lateral-wall species flux is converted with reviewed metal stoichiometry, physical reference area, reactive wall area, molar mass and density; no local thinning map or acceptance is inferred.",
            ),
            ("explicit_coupled_wall_metal_loss",),
        )
    ]
