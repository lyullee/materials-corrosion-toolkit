"""Registry adapter for explicit caller-calibrated CO2 corrosion composition."""

from ..co2_corrosion_campaign import Co2CorrosionCampaign, evaluate_co2_corrosion_campaign
from ..contracts import Calculation
from ..electrochemical_transport import ElectrochemicalTransport, solve_electrochemical_transport
from ..crevice_geometry import (
    PlanarSlitApertureHistory,
    PlanarSlitHydraulicFlow,
    PlanarSlitHydraulicHistory,
    PlanarSlitGeometry,
    evaluate_planar_slit_hydraulic_flow,
    evaluate_planar_slit_hydraulic_history,
    planar_slit_aperture_history,
    planar_slit_transport_geometry,
)
from ..registry import ModelSpec
from ..single_solid_equilibrium import SingleSolidEquilibrium, evaluate_single_solid_equilibrium
from ..competing_solid_equilibrium import (
    CompetitiveSolidEquilibrium,
    evaluate_competitive_solid_equilibrium,
)


def _evaluate(request, evaluator=evaluate_co2_corrosion_campaign):
    values = evaluator(request)
    status = values.pop("status")
    basis = values.pop("basis", None)
    return Calculation(status=status, values=values, notes=(basis,) if basis else ())


def specifications():
    return [
        ModelSpec(
            "chemistry.single_solid_precipitation_equilibrium",
            SingleSolidEquilibrium,
            lambda x: _evaluate(x, evaluate_single_solid_equilibrium),
            {"reaction_extent_mol_m3": "mol/m3", "final_solid_moles_per_solution_volume_mol_m3": "mol/m3"},
            (
                "One explicitly declared neutral pure solid with fixed activity coefficients/solution volume and atom/charge-conserving extent; no competing phases or kinetic prediction.",
            ),
            ("single_solid_stoichiometric_equilibrium",),
        ),
        ModelSpec(
            "chemistry.competitive_solid_equilibrium",
            CompetitiveSolidEquilibrium,
            lambda x: _evaluate(x, evaluate_competitive_solid_equilibrium),
            {
                "final_aqueous_concentration_mol_m3": "mol/m3",
                "solid_phase_results": "phase-wise mol/m3 and log saturation ratio",
            },
            (
                "Caller-declared competing neutral pure solids in one fixed-volume liquid with fixed activity coefficients; candidate phase list, stoichiometry and source-backed equilibrium constants are explicit. No automated aqueous speciation or kinetic precipitation is inferred.",
            ),
            ("competitive_pure_solid_fixed_gamma_equilibrium",),
        ),
        ModelSpec(
            "corrosion.planar_slit_geometry",
            PlanarSlitGeometry,
            lambda x: _evaluate(x, planar_slit_transport_geometry),
            {
                "length_m": "m",
                "axial_cross_section_m2": "m2",
                "cell_volume_m3": "m3",
                "wall_area_per_volume_m2_m3": "1/m",
            },
            (
                "Explicit constant-aperture planar slit and selected reactive broad faces; no kinetics or advection inferred.",
            ),
            ("planar_slit_geometry_reduction",),
        ),
        ModelSpec(
            "corrosion.planar_slit_aperture_history",
            PlanarSlitApertureHistory,
            lambda x: _evaluate(x, planar_slit_aperture_history),
            {
                "cell_aperture_m": "m",
                "geometry_states[].elapsed_time_s": "s",
                "geometry_states[].cell_aperture_m": "m",
                "geometry_states[].axial_cross_section_m2": "m2",
                "geometry_states[].cell_volume_m3": "m3",
                "computed_prefix_geometry_states[].elapsed_time_s": "s",
                "computed_prefix_geometry_states[].cell_aperture_m": "m",
                "computed_prefix_geometry_states[].axial_cross_section_m2": "m2",
                "computed_prefix_geometry_states[].cell_volume_m3": "m3",
                "failed_elapsed_time_s": "s",
                "axial_cross_section_m2": "m2",
                "cell_volume_m3": "m3",
                "wall_area_per_volume_m2_m3": "1/m",
            },
            (
                "Sequential geometry remapping from a caller-pinned cell-average signed wall-recession history within declared aperture support; support failure preserves an out-of-scope prefix and failed interval, and subsequent transport is a separate calculation.",
            ),
            ("planar_slit_aperture_evolution",),
        ),
        ModelSpec(
            "corrosion.planar_slit_hydraulic_flow",
            PlanarSlitHydraulicFlow,
            lambda x: _evaluate(x, evaluate_planar_slit_hydraulic_flow),
            {
                "volume_flow_rate_m3_s": "m3/s",
                "transport_face_velocity_m_s": "m/s",
                "cell_boundary_pressure_Pa": "Pa",
            },
            (
                "Steady incompressible Newtonian laminar flow in caller-declared variable-gap planar-slit cells; optional aperture state is digest-bound, and unsupported Reynolds/aspect ratios fail closed.",
            ),
            ("planar_slit_steady_laminar_hydraulic_reduction",),
        ),
        ModelSpec(
            "corrosion.planar_slit_hydraulic_history",
            PlanarSlitHydraulicHistory,
            lambda x: _evaluate(x, evaluate_planar_slit_hydraulic_history),
            {
                "elapsed_time_s": "s",
                "flow_snapshots": "aligned steady snapshots, SI",
            },
            (
                "Digest-bound pressure samples are paired to every computed aperture-history knot; each knot is solved independently and the result is operator-split, not transiently or fully coupled.",
            ),
            ("planar_slit_sequential_hydraulic_history",),
        ),
        ModelSpec(
            "corrosion.explicit_co2_campaign",
            Co2CorrosionCampaign,
            _evaluate,
            {},
            (
                "Explicit caller-calibrated carbonate boundary, reaction/ionic transport, surface kinetics and reviewed metal-dissolution mapping in fixed geometry.",
            ),
            ("explicit_co2_corrosion_campaign",),
        ),
        ModelSpec(
            "electrochemistry.restricted_transport_campaign",
            ElectrochemicalTransport,
            lambda x: _evaluate(x, solve_electrochemical_transport),
            {},
            (
                "Caller-calibrated homogeneous ionic reactions and Butler-Volmer tip/wall boundaries on a fixed one-dimensional transport grid; an optional digest-matched activity-coefficient correction multiplies species concentrations in homogeneous rates only when separately reviewed. Wall kinetics require explicit area-density, local potential and reviewed equipotential-metal assumptions.",
            ),
            (
                "electrochemical_transport_composition",
                "caller_gamma_corrected_effective_concentration_kinetics",
            ),
        ),
    ]
