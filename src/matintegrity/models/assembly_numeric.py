"""Registry exposure for explicit assembly geometry and thermal calculations."""

from pydantic import Field

from ..assembly_calculations import (
    ElasticJointLoad,
    TubeCondition,
    TubeLayout,
    elastic_joint_load,
    tube_bundle_inventory,
    tube_layout_geometry,
)
from ..contracts import Calculation, Contract
from ..fad_envelope import FadEnvelope, FadPoint, evaluate_fad_envelope
from ..gasket_contact import (
    NonlinearBoltGasketJoint,
    NonlinearGasketJoint,
    evaluate_nonlinear_bolt_gasket_joint,
    evaluate_nonlinear_gasket_joint,
)
from ..gasket_relaxation import (
    GasketRelaxationRequest,
    GasketViscoelasticHistoryRequest,
    GasketViscoelasticJointHistoryRequest,
    NonlinearGasketViscoelasticJointHistoryRequest,
    UnilateralNonlinearGasketJointHistoryRequest,
    evaluate_gasket_relaxation,
    evaluate_gasket_viscoelastic_history,
    evaluate_gasket_viscoelastic_joint_history,
    evaluate_nonlinear_gasket_viscoelastic_joint_history,
    evaluate_unilateral_nonlinear_gasket_joint_history,
)
from ..insulation_surface import InsulationSurfaceRequest, solve_insulation_surface
from ..registry import ModelSpec


class FadEnvelopeAssessment(Contract):
    point: FadPoint
    envelope: FadEnvelope


class TubeBundleInventory(Contract):
    tubes: tuple[TubeCondition, ...] = Field(min_length=1)


def _calculation(function, request):
    values = dict(function(request))
    status = values.pop("status", "computed")
    basis = values.pop("basis", None)
    return Calculation(status=status, values=values, notes=(basis,) if basis else ())


def specifications():
    return [
        ModelSpec(
            "fabrication.gasket_relaxation_curve",
            GasketRelaxationRequest,
            lambda x: _calculation(evaluate_gasket_relaxation, x),
            {"force_history_N.residual_preload_N": "N", "force_history_N.elapsed_time_s": "s"},
            (
                "Authorized caller retention observations are linearly interpolated only inside the exact declared time support; no universal gasket relaxation law or leakage/acceptance result is inferred.",
            ),
            ("caller_gasket_relaxation_curve",),
        ),
        ModelSpec(
            "fabrication.gasket_prony_history",
            GasketViscoelasticHistoryRequest,
            lambda x: _calculation(evaluate_gasket_viscoelastic_history, x),
            {
                "response_history.total_compressive_stress_Pa": "Pa",
                "response_history.compressive_force_N": "N",
                "response_history.elapsed_time_s": "s",
            },
            (
                "Caller-authorized generalized Maxwell terms and separately reviewed explicit initial branch stresses are integrated over a reviewed piecewise-linear compression-strain history.",
                "The model does not fit or transfer material coefficients, infer flange flexibility or leakage, or represent tensile contact loss and acceptance.",
            ),
            ("caller_gasket_prony_constitutive_response",),
        ),
        ModelSpec(
            "fabrication.gasket_prony_joint_history",
            GasketViscoelasticJointHistoryRequest,
            lambda x: _calculation(evaluate_gasket_viscoelastic_joint_history, x),
            {
                "response_history.elapsed_time_s": "s",
                "response_history.compressive_strain": "1",
                "response_history.compressive_displacement_m": "m",
                "response_history.branch_stress_Pa": "Pa",
                "response_history.gasket_stress_Pa": "Pa",
                "response_history.gasket_force_N": "N",
                "response_history.bolt_force_N": "N",
                "response_history.external_separating_force_N": "N",
                "response_history.bolt_free_length_change_m": "m",
                "response_history.bolt_extension_change_m": "m",
                "response_history.force_balance_residual_N": "N",
                "initial_bolt_preload_N": "N",
            },
            (
                "Caller-authorized Prony gasket history is coupled to a linear bolt and quasi-static force equilibrium at each declared time knot.",
                "Only closed contact, piecewise-linear interval strain evolution and a uniform single-degree-of-freedom joint are represented; flange field, leakage and acceptance are outside scope.",
            ),
            ("caller_coupled_prony_bolt_gasket_history",),
        ),
        ModelSpec(
            "fabrication.nonlinear_gasket_prony_joint_history",
            NonlinearGasketViscoelasticJointHistoryRequest,
            lambda x: _calculation(evaluate_nonlinear_gasket_viscoelastic_joint_history, x),
            {
                "response_history.elapsed_time_s": "s",
                "response_history.compressive_strain": "1",
                "response_history.compressive_displacement_m": "m",
                "response_history.equilibrium_backbone_stress_Pa": "Pa",
                "response_history.branch_stress_Pa": "Pa",
                "response_history.gasket_stress_Pa": "Pa",
                "response_history.gasket_force_N": "N",
                "response_history.bolt_force_N": "N",
                "response_history.external_separating_force_N": "N",
                "response_history.bolt_free_length_change_m": "m",
                "response_history.bolt_extension_change_m": "m",
                "response_history.force_balance_residual_N": "N",
                "initial_bolt_preload_N": "N",
            },
            (
                "Caller-authorized monotone nonlinear stress-strain backbones for equilibrium and generalized-Maxwell branches are coupled to a caller nonlinear bolt curve and knotwise force balance.",
                "Branch forcing is integrated exactly for piecewise-linear strain segments split at every declared backbone breakpoint; contact opening, spatial flange behavior, leakage and qualification are not modeled.",
            ),
            ("caller_nonlinear_gasket_prony_joint_history",),
        ),
        ModelSpec(
            "fabrication.unilateral_nonlinear_gasket_prony_joint_history",
            UnilateralNonlinearGasketJointHistoryRequest,
            lambda x: _calculation(evaluate_unilateral_nonlinear_gasket_joint_history, x),
            {
                "response_history.elapsed_time_s": "s",
                "response_history.compressive_strain": "1",
                "response_history.compressive_displacement_m": "m",
                "response_history.branch_stress_Pa": "Pa",
                "response_history.gasket_force_N": "N",
                "response_history.bolt_force_N": "N",
                "response_history.external_separating_force_N": "N",
                "response_history.force_balance_residual_N": "N",
                "initial_bolt_preload_N": "N",
            },
            (
                "Caller-authorized nonlinear generalized-Maxwell gasket curves and a nonlinear bolt curve are solved with compression-only contact at each declared time knot.",
                "Open/reclose transitions are knotwise; branch state is frozen at zero compression while open. No between-knot event time, flange field, leakage or acceptance is inferred.",
            ),
            ("caller_nonlinear_gasket_prony_joint_history",),
            qualification="user_model",
        ),
        ModelSpec(
            "fabrication.nonlinear_gasket_contact",
            NonlinearGasketJoint,
            lambda x: _calculation(evaluate_nonlinear_gasket_joint, x),
            {"bolt_force_N": "N", "gasket_force_N": "N", "compression_m": "m", "contact_gap_m": "m"},
            (
                "Elastic bolt and authorized reversible caller compression-force curve, with explicit contact loss and no extrapolation.",
            ),
            ("reversible_gasket_contact_equilibrium",),
        ),
        ModelSpec(
            "fabrication.nonlinear_bolt_gasket_contact",
            NonlinearBoltGasketJoint,
            lambda x: _calculation(evaluate_nonlinear_bolt_gasket_joint, x),
            {
                "bolt_force_N": "N",
                "gasket_force_N": "N",
                "compression_m": "m",
                "contact_gap_m": "m",
                "bolt_extension_change_m": "m",
                "force_balance_residual_N": "N",
            },
            (
                "Single-degree-of-freedom quasi-static joint equilibrium using caller-authorized monotone nonlinear bolt force-extension and gasket force-compression curves, with no extrapolation.",
                "Caller may supply a validated equivalent assembly curve; this does not resolve a spatial flange bending field, hysteresis, leakage or acceptance.",
            ),
            ("caller_nonlinear_bolt_gasket_equilibrium",),
        ),
        ModelSpec(
            "structural.caller_fad_envelope",
            FadEnvelopeAssessment,
            lambda x: _calculation(lambda request: evaluate_fad_envelope(request.point, request.envelope), x),
            {"kr_limit": "1", "kr_margin": "1", "within_caller_envelope": "1"},
            (
                "Compare identified provider FAD coordinates only against a reviewed caller curve with matching material/geometry/load basis.",
            ),
            ("caller_fad_and_assembly_geometry",),
        ),
        ModelSpec(
            "fabrication.tube_bundle_inventory",
            TubeBundleInventory,
            lambda x: _calculation(lambda request: tube_bundle_inventory(request.tubes), x),
            {
                "total_tube_count": "count",
                "active_tube_count": "count",
                "plugged_tube_count": "count",
                "active_flow_area_m2": "m2",
                "wall_loss_fraction_by_tube": "1",
            },
            (
                "Identified tube wall-loss and plugged-bore geometric inventory only; no tube capacity or leakage conclusion.",
            ),
            ("caller_fad_and_assembly_geometry",),
        ),
        ModelSpec(
            "fabrication.regular_tube_layout",
            TubeLayout,
            lambda x: _calculation(tube_layout_geometry, x),
            {
                "ligament_m": "m",
                "ligament_fraction": "1",
                "ideal_lattice_void_fraction": "1",
                "tube_side_flow_area_m2": "m2",
            },
            (
                "Explicit regular square or triangular tube lattice geometry; no shell/baffle clearance or pressure-drop inference.",
            ),
            ("caller_fad_and_assembly_geometry",),
        ),
        ModelSpec(
            "fabrication.elastic_joint_load",
            ElasticJointLoad,
            lambda x: _calculation(elastic_joint_load, x),
            {"bolt_force_N": "N", "clamp_force_N": "N", "thermal_preload_change_N": "N"},
            (
                "Reviewed linear two-spring closed-contact load partition with caller stiffness and differential thermal displacement.",
            ),
            ("caller_fad_and_assembly_geometry",),
            version="1.0.1",
        ),
        ModelSpec(
            "thermal.insulation_surface_balance",
            InsulationSurfaceRequest,
            lambda x: _calculation(solve_insulation_surface, x),
            {
                "outer_surface_temperature_K": "K",
                "heat_from_inner_surface_W": "W",
                "convective_heat_out_W": "W",
                "radiative_heat_out_W": "W",
                "balance_residual_W": "W",
            },
            (
                "Steady single-layer radial conduction with caller constant convection and gray radiation boundaries.",
            ),
            ("cylindrical_surface_energy_balance",),
            version="1.0.1",
        ),
    ]
