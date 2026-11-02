"""Registry exposure for calibrated sequence-growth and critical-plane life APIs."""

from ..contracts import Calculation
from ..critical_plane_life import CriticalPlaneFsLife, evaluate_critical_plane_fs_life
from ..critical_plane_cycle_pairing import (
    CriticalPlaneCyclePairDamage,
    CriticalPlaneIntervalOverlapPairing,
    critical_plane_cycle_pair_damage,
    propose_critical_plane_interval_overlap_pairing,
)
from ..multiaxial_life_campaign import MultiaxialLifeCampaign, evaluate_multiaxial_life_campaign
from .continuous_plane_life_bound import (
    ContinuousPlaneFsLifeBound,
    map_continuous_plane_fs_bound_to_life,
)
from .multiaxial_work_life import ClosedTensorWorkLife, closed_tensor_work_life
from ..registry import ModelSpec
from ..sequence_crack_growth import SequenceCrackGrowth, evaluate_sequence_crack_growth


def _evaluate(function, request):
    values = dict(function(request))
    status = values.pop("status")
    basis = values.pop("basis", None)
    return Calculation(status=status, values=values, notes=(basis,) if basis else ())


def specifications():
    return [
        ModelSpec(
            "fatigue.multiaxial_life_campaign",
            MultiaxialLifeCampaign,
            lambda x: _evaluate(evaluate_multiaxial_life_campaign, x),
            {},
            (
                "Closed caller local tensor cycle to supplied sampled planes and same-condition FS/SWT or caller shear-normal calibration; preserve ties and support limits.",
            ),
            (
                "multiaxial_cycle_life_composition",
                "caller_shear_normal_strain_curve_life",
                "kandil_brown_miller_curve_life",
            ),
        ),
        ModelSpec(
            "fatigue.continuous_plane_fs_life_bound",
            ContinuousPlaneFsLifeBound,
            map_continuous_plane_fs_bound_to_life,
            {
                "minimum_cycles_to_failure_bound": "cycle",
                "maximum_cycles_to_failure_bound": "cycle",
                "life_interval_width_cycles": "cycle",
                "sampled_maximum_fatemi_socie_factor": "1",
                "certified_continuous_plane_factor_upper_bound": "1",
            },
            (
                "Map a certified sampled-cycle continuous-plane FS factor interval to a conservative caller-calibrated cycle-life interval over declared support.",
                "The mapping assumes and requires caller review of monotone factor-to-life behavior; it does not bound unsampled time response, calibration or physical model error.",
            ),
            ("continuous_plane_fs_life_bound_mapping",),
        ),
        ModelSpec(
            "fracture.sequence_zone_memory",
            SequenceCrackGrowth,
            lambda x: _evaluate(evaluate_sequence_crack_growth, x),
            {
                "completed_cycles": "cycle",
                "completed_cycles_this_run": "cycle",
                "final_depth_m": "m",
                "plastic_zone_tip_m": "m",
                "limiting_depth_m": "m",
            },
            (
                "Caller-calibrated opening ratio and plastic-zone memory with explicit whole-cycle stepping, state checkpoints, and distinct fracture/depth/support termination.",
            ),
            ("sequence_zone_memory_and_partial_dissolution",),
        ),
        ModelSpec(
            "fatigue.critical_plane_fs_life",
            CriticalPlaneFsLife,
            lambda x: _evaluate(evaluate_critical_plane_fs_life, x),
            {"cycles_to_failure": "cycle", "reversals_to_failure": "reversal"},
            (
                "Identified Fatemi-Socie factor mapped to caller-calibrated engineering-shear strain-life coefficients inside declared cycle support.",
            ),
            ("calibrated_fs_factor_life",),
        ),
        ModelSpec(
            "fatigue.explicit_critical_plane_cycle_pair_damage",
            CriticalPlaneCyclePairDamage,
            lambda x: _evaluate(critical_plane_cycle_pair_damage, x),
            {
                "total_miner_damage": "1",
                "pair_results[].miner_damage": "1",
                "pair_results[].allocated_cycle_count": "cycle",
                "pair_results[].cycles_to_failure": "cycle",
            },
            (
                "Caller-declared scalar normal/shear rainflow cycle allocations with calibrated Fatemi-Socie life and explicit Miner accumulation; no temporal pairing is inferred.",
            ),
            ("explicit_critical_plane_cycle_pair_damage",),
        ),
        ModelSpec(
            "fatigue.propose_critical_plane_interval_overlap_pairing",
            CriticalPlaneIntervalOverlapPairing,
            lambda x: _evaluate(propose_critical_plane_interval_overlap_pairing, x),
            {
                "pairings[].allocated_cycle_count": "cycle",
                "pairings[].interval_intersection_over_union": "1",
                "normal_unallocated_cycle_count": "cycle",
                "shear_unallocated_cycle_count": "cycle",
                "normal_cycle_count": "cycle",
                "shear_cycle_count": "cycle",
            },
            (
                "Deterministic continuous-capacity bipartite min-cost max-flow proposal over overlapping sample-index intervals; maximize paired cycle count, then allocated-count-weighted interval IoU.",
                "The proposed map is not a physical pairing law; caller review and explicit unallocated-cycle treatment are required before a calibrated damage calculation.",
            ),
            ("critical_plane_interval_overlap_pairing_proposal",),
        ),
        ModelSpec(
            "fatigue.closed_tensor_work_life",
            ClosedTensorWorkLife,
            closed_tensor_work_life,
            {
                "cycle_results[].signed_closed_loop_work_density_J_m3": "J/m^3",
                "cycle_results[].dissipated_energy_density_J_m3": "J/m^3",
                "cycle_results[].cycles_to_failure": "cycle",
                "cycle_results[].miner_damage": "1",
                "total_miner_damage": "1",
                "cycle_count": "cycle",
            },
            (
                "Caller-provided closed 3D stress-strain tensor cycles and material-matched work-life calibration with bounded log-log interpolation and explicit Miner accumulation.",
                "Path-work response is caller-calibrated and is not a universal nonproportional fatigue law or code acceptance result.",
            ),
            ("closed_tensor_work_life_calibration",),
        ),
    ]
