"""Export current public Pydantic contracts for independently developed consumers."""

import hashlib
import json
from collections import Counter
from pathlib import Path

from matintegrity.models.component_pressure_reference import ComponentPressureLimit
from matintegrity.models.pressure_limit_binding import PressureLimitBinding, PressureLimitReferenceContext

from matintegrity.adapters import (
    ActionEventProbabilityEvaluation,
    Co2MixtureFugacityHistory,
    FaultTreeActionEventInput,
    FaultTreeActionResultLineage,
    FaultTreeInspectionRiskCampaignReport,
    LocalTensorHistory,
    MonitoringAssessmentRecord,
    OperatingHistory,
    PSADynaMeanStreamFugacityBatch,
    PSADynaMeanStreamFugacityRow,
)
from matintegrity.adaptive_cycle_block_damage import (
    AdaptiveCycleBlockDamageRequest,
    CycleBlockLawParameter,
    IntegerCycleDamageBlock,
)
from matintegrity.api581_exchange import (
    Api581DamageExchangeRecord,
    Api581InspectionLineage,
    Api581WallFlawMaterialState,
)
from matintegrity.api581_numeric_provider import Api581NumericFrequencyReport, Api581NumericFrequencySettings
from matintegrity.api581_pinned_adapter import PinnedPofMethodSelectionRequest
from matintegrity.api581_pinned_validation import Api581PinnedSchemaValidationReport
from matintegrity.aquasoldb_data import (
    AquaSolDBCo2SolubilityObservation,
    AquaSolDBCo2SolubilityQuery,
    AquaSolDBFixedFugacityComparisonInput,
)
from matintegrity.aqueous_mass_action_scenario_envelope import (
    AqueousMassActionScenario,
    AqueousMassActionScenarioEnvelope,
)
from matintegrity.aqueous_mass_action_topology_envelope import (
    AqueousMassActionTopologyCase,
    AqueousMassActionTopologyEnvelope,
)
from matintegrity.aqueous_solid_phase_candidates import AqueousSolidPhaseCandidateEnumeration
from matintegrity.assembly_calculations import ElasticJointLoad, TubeCondition, TubeLayout
from matintegrity.atmospheric_data import AtmosphericCorrosionObservation
from matintegrity.atmospheric_typed_rows import (
    AtmosphericArchiveAuditRequest,
    AtmosphericCorrosionObservationRow,
    AtmosphericReadAuthorization,
)
from matintegrity.calibrated_condition_loss import (
    CalibratedConditionLossLaw,
    ConditionLossHistory,
    ConditionLossInterval,
    ConditionLossRateAssessment,
    LogRateInteraction,
    LossCondition,
    LossRateFeature,
)
from matintegrity.calibrated_damage_history import CalibratedDamageHistory, CalibratedDamageInterval
from matintegrity.carbonate_reaction_network import CarbonateReactionConstants
from matintegrity.carbonate_transport_adapter import CarbonateBoundarySelection, CarbonateTransportBoundary
from matintegrity.carpinteri_spagnoli_finite_screen import (
    CarpinteriSpagnoliFiniteScreen,
    CarpinteriSpagnoliPlane,
)
from matintegrity.carpinteri_spagnoli_life import CarpinteriSpagnoliLife
from matintegrity.cathodic_protection_data import (
    CathodicProtectionArchiveAuditRequest,
    CathodicProtectionCurveRecord,
    CathodicProtectionDatasetAudit,
    CathodicProtectionReadAuthorization,
    CathodicProtectionSample,
)
from matintegrity.ccps_native_provider import CcpsNativePlumeProviderReport, CcpsNativePlumeSettings
from matintegrity.ceit_typed_rows import (
    CeitFieldArchiveAuditRequest,
    CeitFieldObservationRow,
    CeitFieldReadAuthorization,
)
from matintegrity.certificate_reconciliation import (
    CertificateMeasurementRecord,
    CertificateReconciliationInput,
    CertificateReconciliationReport,
    CertificateRequirement,
    CertificateUnitRule,
    MaterialCertificateEvidence,
    ReconciledEvidenceRow,
)
from matintegrity.cmsx6_creep_lis_typed_rows import (
    CMSX6LISColumnValue,
    CMSX6LISReadAuthorization,
    CMSX6LISReadRequest,
    CMSX6LISTypedRow,
)
from matintegrity.co2_corrosion_campaign import Co2CorrosionCampaign
from matintegrity.coating_adhesion_data import (
    CoatingAdhesionDatasetAudit,
    CoatingAdhesionGroupRecord,
)
from matintegrity.competing_solid_equilibrium import (
    CompetitiveAqueousSpecies,
    CompetitiveSolidEquilibrium,
    CompetitiveSolidPhase,
)
from matintegrity.composition import ParameterProfile, SatisfactionGate, WorkflowStep
from matintegrity.consequence_exchange import (
    CompositionComponent,
    ConsequenceQuantity,
    ConsequenceScenarioHandoff,
    ConsequenceScenarioResultRecord,
    ConsequenceStageResult,
    IntegrityEventBasis,
    ProcessStateBasis,
    ReleaseScenarioBasis,
    RequestedConsequenceModel,
)
from matintegrity.consequence_pinned_adapter import (
    PinnedExternalSourceTerm,
    PinnedProviderEvidence,
    PinnedProviderRequestEnvelope,
    PinnedProviderRequestOptions,
)
from matintegrity.consequence_pinned_validation import (
    PinnedProviderRequestValidationReport,
    PinnedSchemaValidationIssue,
)
from matintegrity.consequence_release_history_adapter import (
    CcpsDenseAtmosphere,
    CcpsDenseReceptor,
    CcpsDenseSubstance,
    CcpsReleaseHistoryInterval,
    CcpsReleaseHistoryRequestEnvelope,
    CcpsReleaseHistorySettings,
    CcpsReleaseHistorySource,
)
from matintegrity.contracts import AssessmentResult, EventProbability, Evidence, RunContext
from matintegrity.controlled_ae_data import (
    AECoordinateRecord,
    AEWaveformRecord,
    ControlledAEDatasetAudit,
)
from matintegrity.coqtel_typed_rows import (
    CoqtelArchiveAuditRequest,
    CoqtelElectrochemistryRow,
    CoqtelReadAuthorization,
)
from matintegrity.corrosion_fta_binding import (
    CorrosionFaultTreeBindingRequest,
    CorrosionFaultTreeEventBinding,
    CorrosionFaultTreeProbabilityInput,
)
from matintegrity.corrosion_metrics_typed_rows import (
    CorrosionMetricObservationRow,
    CorrosionMetricsArchiveAuditRequest,
    CorrosionMetricsReadAuthorization,
)
from matintegrity.corrosion_rate_history import CorrosionRateHistoryKnot, CorrosionRateThicknessHistoryRequest
from matintegrity.crack_arrest_typed_rows import (
    CrackArrestArchiveAuditRequest,
    CrackArrestObservationRow,
    CrackArrestReadAuthorization,
)
from matintegrity.creep_fatigue_campaign import CreepFatigueCampaign, CreepFatigueCampaignResult
from matintegrity.creep_fatigue_interaction import (
    CreepFatigueInteractionEnvelope,
    CreepFatigueInteractionPoint,
    CreepFatigueInteractionResult,
)
from matintegrity.creep_history import CreepHistoryInterval, CreepHistoryRequest, CreepHistoryResult
from matintegrity.crevice_activity_corrected_transport import (
    CreviceActivityCorrectedTransportRequest,
    CreviceActivityReactiveReaction,
    CreviceActivityReactiveSpecies,
    CreviceActivityReactiveTerm,
    CreviceActivityReactiveTransportRequest,
    CreviceActivityTransportSpecies,
)
from matintegrity.crevice_activity_gradient_flux import (
    CreviceActivityGradientFluxRequest,
    CreviceActivityGradientSpecies,
)
from matintegrity.crevice_activity_reaction_rates import (
    CreviceActivityRateReaction,
    CreviceActivityRateRequest,
    CreviceActivityRateSpecies,
    CreviceActivityRateTerm,
)
from matintegrity.crevice_activity_transport_phase_aperture import (
    CreviceActivityTransportPhaseApertureRequest,
)
from matintegrity.crevice_activity_transport_sequential_aperture import (
    CreviceActivityTransportSequentialApertureCampaign,
)
from matintegrity.crevice_aperture_displacement_flow import CreviceApertureDisplacementFlowRequest
from matintegrity.crevice_aqueous_component_ledger import (
    ComponentSpeciesCoefficient,
    ConservedAqueousComponent,
    ConstraintRoleAssignment,
    CreviceAqueousComponentLedgerRequest,
    SpeciesCellAmount,
    SpeciesFaceTransfer,
)
from matintegrity.crevice_bdf_nucleation_operator_split import CreviceBDFNucleationOperatorSplitRequest
from matintegrity.crevice_calibrated_wall_flux_callback import CreviceCalibratedWallFluxRequest
from matintegrity.crevice_calibrated_wall_sink_history import CreviceCalibratedWallSinkHistoryRequest
from matintegrity.crevice_campaign import CreviceGeometryTransportCampaign, CreviceTransportRecessionFeedback
from matintegrity.crevice_cellwise_nucleation_kinetic_history import (
    CreviceCellwiseNucleationKineticHistoryRequest,
    FixedKineticCell,
)
from matintegrity.crevice_closed_batch_aqueous_equilibrium import (
    CreviceClosedBatchAqueousEquilibriumRequest,
    InitialSpeciesAmount,
)
from matintegrity.crevice_competing_solid_equilibrium import (
    CreviceCompetingSolidEquilibriumRequest,
    CreviceCompetingSolidPhase,
    CreviceEquilibriumAqueousSpecies,
)
from matintegrity.crevice_component_solid_partition import (
    ComponentTotalInventory,
    CreviceComponentSolidPartitionRequest,
)
from matintegrity.crevice_component_state_bdf import (
    CapacitiveCellCurrentSchedule,
    CellAqueousEquilibriumTemplate,
    CellDynamicSolidGeometry,
    CellSolidPhaseSet,
    ComponentInventoryByCell,
    CreviceComponentStateBDFRequest,
    ElectrochemicalSourceExtentSchedule,
    ElectrochemicalSourceReaction,
    ExternalReservoirComponentChange,
    ExternalReservoirElementChange,
    IonicFaceCurrentSchedule,
    SolidPhaseGeometryMap,
    SpeciesFaceDiffusivity,
)
from matintegrity.crevice_bdf_kinetic_phase_set import (
    CreviceBDFInitialSolidInventory,
    CreviceBDFKineticPhaseSet,
)
from matintegrity.crevice_component_state_faradaic_binding import (
    CreviceCurrentCarryingCellBinding,
    CreviceCurrentCarryingComponentStateBinding,
)
from matintegrity.crevice_component_state_segment_handoff import (
    CreviceComponentStateSegmentHandoffRequest,
    HandoffPhaseGeometry,
)
from matintegrity.crevice_component_state_segment_transition import (
    CreviceComponentStateSegmentTransitionRequest,
    CreviceSegmentGeometry,
)
from matintegrity.crevice_current_carrying_aperture_feedback import (
    CreviceCurrentCarryingApertureFeedbackRequest,
)
from matintegrity.crevice_current_carrying_metal_loss import (
    CreviceCurrentBranchMetalMapping,
    CreviceCurrentCarryingExtentMetalLossRequest,
)
from matintegrity.crevice_current_carrying_np_faradaic import CreviceCurrentCarryingNernstPlanckRequest
from matintegrity.crevice_deposition_aperture_history import (
    CreviceDepositionApertureHistoryRequest,
    CreviceDepositionVolumeKnot,
)
from matintegrity.crevice_deposition_transport_geometry import CreviceDepositionTransportGeometryRequest
from matintegrity.crevice_double_layer_bdf_binding import CreviceDoubleLayerBDFBindingRequest
from matintegrity.crevice_double_layer_charge_history import CreviceDoubleLayerChargeHistoryRequest
from matintegrity.crevice_dynamic_double_layer_bdf_binding import (
    CreviceDynamicDoubleLayerBDFBindingRequest,
    DynamicBranchReactionMap,
)
from matintegrity.crevice_dynamic_double_layer_faradaic_history import (
    CreviceDynamicDoubleLayerFaradaicHistoryRequest,
    DynamicDoubleLayerPolarizationBranch,
)
from matintegrity.crevice_electroneutral_diffusion import (
    CreviceElectroneutralDiffusionRequest,
    CreviceElectroneutralSpecies,
)
from matintegrity.crevice_external_activity_solid_saturation import (
    CreviceExternalActivitySolidSaturationRequest,
)
from matintegrity.crevice_faradaic_fta_binding import (
    CreviceFaradaicFaultTreeBindingRequest,
    CreviceFaradaicFaultTreeEventBinding,
    CreviceFaradaicFaultTreeProbabilityInput,
)
from matintegrity.crevice_faradaic_spatial_chemistry_coupling import (
    CreviceFaradaicBranchMap,
    CreviceFaradaicSpatialChemistryRequest,
    CreviceNernstBranchMap,
)
from matintegrity.crevice_geometry import (
    PlanarSlitApertureHistory,
    PlanarSlitEndpointVelocityPath,
    PlanarSlitGeometry,
    PlanarSlitHydraulicFlow,
    PlanarSlitHydraulicHistory,
)
from matintegrity.crevice_geometry_aware_chemistry import (
    CreviceGeometryAwareAqueousChemistryContract,
    GeometryAwareAqueousSpecies,
    GeometryAwareReactionDefinition,
)
from matintegrity.crevice_geometry_aware_solid_deposition import (
    CallerSolidReactionExtent,
    CreviceGeometryAwareSolidDepositionContract,
    SolidCoupledSpecies,
    SolidPhaseInventoryBasis,
)
from matintegrity.crevice_hydraulic_component_advection import CreviceHydraulicComponentAdvection
from matintegrity.crevice_dynamic_hydraulic_advection import CreviceDynamicHydraulicAdvection
from matintegrity.crevice_hydraulic_parameter_fit import (
    CreviceHydraulicParameterFitRequest,
    HydraulicFlowObservationRun,
)
from matintegrity.crevice_hydraulic_stage_rhs import CreviceHydraulicStageRHSRequest
from matintegrity.crevice_ionic_reactive_transport import (
    CreviceIonicReaction,
    CreviceIonicReactionTerm,
    CreviceIonicReactiveSpecies,
    CreviceIonicReactiveTransportRequest,
)
from matintegrity.crevice_kinetic_solid_volume_history import CreviceKineticSolidVolumeHistoryRequest
from matintegrity.crevice_local_solid_saturation import CreviceLocalSolidSaturationRequest
from matintegrity.crevice_local_speciation_ledger import (
    CreviceCellSpeciationRecord,
    CreviceLocalExternalActivityProjectionRequest,
    CreviceLocalMassActionProjectionRequest,
    CreviceLocalSpeciationLedgerRequest,
    CreviceMassActionProjectionCell,
    CreviceMassActionProjectionKnot,
    CreviceSpeciationKnot,
)
from matintegrity.crevice_moving_volume_continuity import CreviceMovingVolumeContinuityRequest
from matintegrity.crevice_component_state_bdf import CreviceComponentStateBDFRequest
from matintegrity.crevice_moving_volume_hydraulic_history import CreviceMovingVolumeHydraulicHistoryRequest
from matintegrity.crevice_multispecies_wall_flux_callback import (
    CreviceMultispeciesWallFluxRequest,
    CreviceSpeciesWallRateHistory,
)
from matintegrity.crevice_nucleation_kinetic_history import (
    CreviceMolarNucleationLaw,
    CreviceNucleationKineticHistoryRequest,
    EvidenceBoundSaturationGrowthLaw,
    NucleationSaturationInterval,
)
from matintegrity.crevice_reactive_transport_1d import (
    CreviceNeutralReactiveTransportRequest,
    ReactiveTransportReaction,
    ReactiveTransportSpecies,
    ReactiveTransportTerm,
)
from matintegrity.crevice_repassivation_margin import (
    CreviceOperatingPotentialKnot,
    CreviceRepassivationExcursionDurationRequest,
    CreviceRepassivationMarginHistoryRequest,
    CreviceRepassivationThresholdKnot,
)
from matintegrity.crevice_saturation_exposure_history import (
    CreviceSaturationExposureHistoryRequest,
    CreviceSaturationHistoryKnot,
)
from matintegrity.crevice_saturation_interval_rate import (
    CreviceLocalSaturationKnot,
    CreviceSaturationIntervalRateRequest,
)
from matintegrity.crevice_solid_inventory_geometry_remap import CreviceSolidInventoryGeometryRemapRequest
from matintegrity.crevice_solid_volume_inventory import CreviceSolidVolumeInventoryRequest
from matintegrity.crevice_spatial_activity_solid_fixed_point import (
    CreviceCellActivitySolidInput,
    CreviceSpatialActivitySolidFixedPointRequest,
)
from matintegrity.crevice_spatial_chemistry_aperture_fixed_point import (
    CreviceSpatialChemistryApertureFixedPointRequest,
)
from matintegrity.crevice_spatial_chemistry_transport import (
    CreviceChemistryKnot,
    CreviceSpatialChemistryTransportRequest,
)
from matintegrity.crevice_spatial_mass_action_workflow import (
    CreviceSpatialMassActionWorkflow,
)
from matintegrity.crevice_spatial_metal_loss import (
    CreviceSpatialDissolutionBranchMapping,
    CreviceSpatialMetalLossRequest,
)
from matintegrity.crevice_spatial_ohmic_mixed_potential import (
    CreviceSpatialOhmicMixedPotentialRequest,
    CreviceSpatialReactionBranch,
)
from matintegrity.crevice_steady_wall_sink import CreviceSteadyWallSinkRequest
from matintegrity.crevice_transient_wall_sink import CreviceTransientWallSinkRequest
from matintegrity.crevice_transport_composition_bridge import CreviceTransportCompositionBridge
from matintegrity.crevice_transport_local_mass_action import (
    CreviceLocalEquilibriumKnot,
    CreviceTransportConstraintBinding,
    CreviceTransportLocalMassActionRequest,
)
from matintegrity.crevice_variable_area_activity_transport import (
    VariableAreaCreviceActivityReactiveTransportRequest,
)
from matintegrity.crevice_wall_flux_inventory_history import CreviceWallFluxInventoryHistoryRequest
from matintegrity.crevice_wall_sink_arrhenius_calibration import (
    CreviceWallSinkArrheniusCalibrationRequest,
    CreviceWallSinkRateObservations,
)
from matintegrity.crevice_wall_sink_group_cv import CreviceWallSinkGroupCVRequest
from matintegrity.crevice_wall_sink_rate_history import CreviceWallSinkRateHistoryRequest
from matintegrity.critical_plane_cycle_pairing import (
    CriticalPlaneCyclePair,
    CriticalPlaneCyclePairDamage,
    CriticalPlaneIntervalOverlapPairing,
)
from matintegrity.critical_plane_life import CriticalPlaneFsLife, CriticalPlaneSwtLife
from matintegrity.crossland_proportional_miner_campaign import (
    CrosslandProportionalBlock,
    CrosslandProportionalMinerCampaign,
)
from matintegrity.ct110_data import (
    CT110ProviderFile,
    CT110Source,
    CT110WeldCorrosionDataset,
    CT110WeldCorrosionObservation,
)
from matintegrity.ct110_wet_co2_typed_rows import (
    CT110CorrosionRateRow,
    CT110ReadAuthorization,
    CT110WorkbookAuditRequest,
)
from matintegrity.dang_van_finite_life_curve import DangVanFiniteParameterLifeCurve
from matintegrity.dissolution_adapter import DissolutionSelection, NetMetalBoundarySelection
from matintegrity.dryad_formate_packer_corrosion_rows import (
    FormatePackerReadAuthorization,
    FormatePackerWorkbookAuditRequest,
    FormatePackerWorkbookCell,
    FormatePackerWorkbookRow,
)
from matintegrity.eddy_current_data import EddyCurrentDicondeRecord
from matintegrity.elastic_joint_to_flange_contact_history import (
    ElasticJointToFlangeContactHistory,
)
from matintegrity.electrochemical_transport import ConcentrationKineticLaw, ElectrochemicalTransport
from matintegrity.electrochemical_wall_flux_schedule import ElectrochemicalWallFluxScheduleRequest
from matintegrity.electrode_kinetics import ButlerVolmerReaction
from matintegrity.electrolyte_extension import ElectrolyteSpecies
from matintegrity.equilibrium_reactive_transport import EquilibriumReactiveTransport
from matintegrity.escape_leak_data import EscapeLeakDatasetAudit, EscapeLeakTraceRecord
from matintegrity.exchange_receipt import (
    ExchangeCompatibilityCheck,
    ExchangeCompatibilityReceipt,
    ExchangeEndpoint,
    ExchangeFieldDecision,
)
from matintegrity.external_schema_audit import ExternalSchemaAuditRecord
from matintegrity.fabest_lcf_data import (
    FabestLcfArchiveAudit,
    FabestLcfExperimentAudit,
    FabestLcfMemberAudit,
    FabestLcfTableAudit,
)
from matintegrity.fad_envelope import FadEnvelope, FadPoint
from matintegrity.fad_fta_binding import (
    FADFaultTreeBindingRequest,
    FADFaultTreeEventBinding,
    FADFaultTreeProbabilityInput,
)
from matintegrity.fad_history import (
    FADAssessmentHistoryKnot,
    FADAssessmentHistoryRequest,
    FADHistoryProviderReceipt,
)
from matintegrity.fatigue_miner_block_history import (
    FindleyLifeCycleBlock,
    FindleyMinerHistoryRequest,
)
from matintegrity.fcgr_curve_import import (
    FcgrCsvImportRequest,
    FcgrCsvImportResult,
    FcgrImportedRow,
    FcgrWorkbookCurveResult,
    FcgrWorkbookImportedPoint,
    FcgrWorkbookImportRequest,
    FcgrWorkbookImportResult,
    FcgrWorkbookSheetSelection,
)
from matintegrity.fire_thermal_response import FireThermalResponse
from matintegrity.fixed_fugacity_carbonate_scale_kinetics import (
    CallerSpeciesActivityRecord,
    CarbonateActivityCoefficientRecord,
    CarbonateKspKnotRecord,
    FixedFugacityCarbonateScaleKinetics,
    FixedFugacityCarbonateScaleKnot,
)
from matintegrity.fracture_toughness_typed_rows import (
    FractureToughnessArchiveAuditRequest,
    FractureToughnessObservationRow,
    FractureToughnessReadAuthorization,
)
from matintegrity.galvanic_data import Ti6Al4VCathodicPolarizationImportRequest
from matintegrity.galvanized_polarization_rows import (
    GalvanizedPolarizationArchiveAuditRequest,
    GalvanizedPolarizationReadAuthorization,
    GalvanizedPolarizationSample,
)
from matintegrity.gasket_contact import (
    BoltForceChangePoint,
    GasketCompressionPoint,
    NonlinearBoltGasketJoint,
    NonlinearGasketJoint,
)
from matintegrity.gasket_correlated_uncertainty import (
    GasketLeakageBoxEnvelope,
    GasketLeakageBoxNode,
    GasketLeakageCorrelatedScenario,
    GasketLeakageCorrelatedScenarioEnvelope,
    GasketLeakageWeightedScenarioMoments,
)
from matintegrity.gasket_joint_load_history import ElasticJointLoadHistoryRequest, ElasticJointLoadKnot
from matintegrity.gasket_prony_relaxation_fit import (
    GasketPronyRelaxationObservation,
    GasketPronyRelaxationSpectrumFit,
    GasketPronyRelaxationTest,
)
from matintegrity.gasket_relaxation import (
    GasketBackbonePoint,
    GasketPronyBranch,
    GasketViscoelasticHistoryRequest,
    GasketViscoelasticJointHistoryRequest,
    GasketViscoelasticMaterial,
    NonlinearGasketMaxwellBranch,
    NonlinearGasketViscoelasticJointHistoryRequest,
    NonlinearGasketViscoelasticMaterial,
    UnilateralNonlinearGasketJointHistoryRequest,
)
from matintegrity.guided_wave_typed_rows import (
    GuidedWaveArchiveAuditRequest,
    GuidedWaveReadAuthorization,
    GuidedWaveSampleRow,
)
from matintegrity.helpr_adapter import HelprLifeCriteriaRecord
from matintegrity.high_temperature_history import (
    HighTemperatureCallerProfile,
    HighTemperatureExposureInterval,
    HighTemperatureFinding,
    HighTemperatureHistoryAssessment,
    HighTemperatureHistoryReport,
    HighTemperatureMeasurementCriterion,
    HighTemperatureMeasurementEvidence,
)
from matintegrity.human_reliability_exchange import HumanReliabilityEstimateRecord
from matintegrity.hydrogen_exchange import HydrogenTransportHistory
from matintegrity.hydrogen_exports import (
    HydrogenPermeationSignalCalibration,
    HydrogenTdsSignalCalibration,
    TabularExportProvenance,
)
from matintegrity.hydrogen_fatigue_data import (
    HydrogenFatigueGrowthPoint,
    HydrogenFatigueSeries,
    HydrogenFatigueWorkbookAudit,
)
from matintegrity.identification import (
    ChemistryRecord,
    ChemistryRequirements,
    DesignationAlias,
    MaterialDesignation,
)
from matintegrity.ince_glinka_gsa_curve_life import GSALifeCurvePoint, InceGlinkaGSACurveLife
from matintegrity.ince_glinka_gsa_miner_campaign import (
    InceGlinkaCycleGroup,
    InceGlinkaGSAMinerCampaign,
)
from matintegrity.insulation_surface import InsulationSurfaceRequest
from matintegrity.itoh_nonproportional_miner_blocks import ItohMinerCycleBlock, ItohNonproportionalMinerBlocks
from matintegrity.itoh_nonproportional_strain_life import ItohNonproportionalStrainLife
from matintegrity.itoh_nonproportional_strain_parameter import ItohNonproportionalStrainRequest
from matintegrity.j2_armstrong_frederick_history import J2ArmstrongFrederickStrainHistory
from matintegrity.j2_prager_strain_history import J2PragerStrainHistory
from matintegrity.lh2dt_adapter import LH2DTNodeStateHistory, LH2DTNodeThermoPoint
from matintegrity.local_environment_history import (
    ElectrodeMaterialCouple,
    LocalEnvironmentExposureState,
    LocalEnvironmentFact,
    LocalEnvironmentFinding,
    LocalEnvironmentHistoryAssessment,
    LocalEnvironmentHistoryCriterion,
    LocalEnvironmentHistoryReport,
)
from matintegrity.mendeley_316l_metastable_pitting_rows import (
    MetastablePittingMeasurementRow,
    MetastablePittingReadAuthorization,
    MprDecodedRecord,
)
from matintegrity.mendeley_ahss1300_permeation_rows import (
    AHSS1300PermeationReadAuthorization,
    AHSS1300PermeationWorkbookRow,
    AHSS1300WorkbookAuditRequest,
    AHSS1300WorkbookCell,
    AHSS1300WorksheetManifest,
)
from matintegrity.mendeley_aisi1018_aerobic_inventory import (
    AISI1018FileMapping,
    AISI1018InventoryItem,
    AISI1018InventoryRequest,
    AISI1018ReadAuthorization,
)
from matintegrity.mendeley_az31b_corrosion_fatigue_rows import (
    AZ31BCorrosionFatigueAuditRequest,
    AZ31BCorrosionFatigueReadAuthorization,
    AZ31BCorrosionFatigueWorkbookCell,
    AZ31BCorrosionFatigueWorkbookRow,
)
from matintegrity.mendeley_explosive_weld_fatigue_rows import (
    ExplosiveWeldFatigueAuditRequest,
    ExplosiveWeldFatigueColumnMapping,
    ExplosiveWeldFatigueMappedImportRequest,
    ExplosiveWeldFatigueMappedObservationRow,
    ExplosiveWeldFatigueObservationField,
    ExplosiveWeldFatigueReadAuthorization,
    ExplosiveWeldFatigueWorkbookCell,
    ExplosiveWeldFatigueWorkbookRow,
    ExplosiveWeldFatigueWorksheetMapping,
)
from matintegrity.mendeley_internal_corrosion_doobn_rows import (
    InternalCorrosionReadAuthorization,
    InternalCorrosionWorkbookAuditRequest,
    InternalCorrosionWorkbookCell,
    InternalCorrosionWorkbookRow,
)
from matintegrity.mendeley_mdea_co2_eis_rows import (
    MDEAEISCell,
    MDEAEISFolderAuditRequest,
    MDEAEISPointRow,
    MDEAEISReadAuthorization,
)
from matintegrity.mendeley_mdea_eis_complex import MDEAEISComplexConversionRequest, MDEAEISComplexPoint
from matintegrity.mendeley_mg_fsp_scc_rows import (
    MagnesiumFspSccAuditRequest,
    MagnesiumFspSccReadAuthorization,
    MagnesiumFspSccWorkbookCell,
    MagnesiumFspSccWorkbookRow,
)
from matintegrity.mendeley_x80_srb_scc_rows import (
    X80SCCDirectoryAuditRequest,
    X80SCCReadAuthorization,
    X80SCCWorkbookCell,
    X80SCCWorkbookRow,
)
from matintegrity.metal_dissolution import PartialMetalDissolutionHistory
from matintegrity.metropt3_data import MetroPT3ArchiveAuditRequest, MetroPT3ArchiveAuthorization, MetroPT3Row
from matintegrity.ml_ndt_data import MlNdtBatchAudit, MlNdtFlawMetadata, MlNdtImageLabel
from matintegrity.models.allowable_property_provider import (
    AllowablePropertyProviderAudit,
    AllowablePropertyQueryRecord,
    AllowablePropertyTableRecord,
)
from matintegrity.models.aqueous_activity_iteration import (
    AqueousBdotIteration,
    AqueousDaviesIteration,
    AqueousSITIteration,
    BdotSpeciesParameter,
)
from matintegrity.models.aqueous_bdot_history import AqueousBdotSpeciationHistory
from matintegrity.models.aqueous_candidate_network_workflow import AqueousCandidateNetworkWorkflow
from matintegrity.models.aqueous_candidate_speciation import AqueousCandidateNetworkSpeciation
from matintegrity.models.aqueous_extended_debye_huckel_iteration import (
    AqueousExtendedDebyeHuckelIteration,
    ExtendedDebyeHuckelSpeciesParameter,
)
from matintegrity.models.aqueous_external_activity import (
    ExternalAqueousActivityIteration,
    ExternalAqueousTransportActivity,
)
from matintegrity.models.aqueous_external_activity_history import ExternalAqueousActivityHistory
from matintegrity.models.aqueous_mass_action import (
    AqueousActivitySpecies,
    AqueousCandidateReactionBindingRequest,
    AqueousCandidateReactionSelection,
    AqueousEquilibriumReaction,
    AqueousLinearConstraint,
    AqueousMassActionSystem,
    AqueousMassActionSystemAssemblyRequest,
    AqueousReactionCandidateEnumeration,
    AqueousReactionCandidateSpecies,
    AqueousStoichiometricTerm,
)
from matintegrity.models.aqueous_mass_action_nernst import AqueousMassActionToNernstHistory
from matintegrity.models.aqueous_saturation_screening import (
    AqueousSaturationScreen,
    CandidateSolid,
    SaturationScreenSpecies,
    SaturationScreenTerm,
)
from matintegrity.models.aqueous_tabulated_activity import (
    AqueousActivityCoefficientPoint,
    AqueousActivityCoefficientTemperatureSlice,
    AqueousSpeciesActivityCurve,
    AqueousTabulatedActivityIteration,
)
from matintegrity.models.aqueous_vant_hoff_history import (
    ActivityCoefficientKnot,
    AqueousMassActionVanTHoffHistory,
    ReactionEnthalpyReference,
)
from matintegrity.models.aqueous_vant_hoff_saturation import (
    AqueousSolubilityKnot,
    AqueousVanTHoffSaturationHistory,
    TemperatureSupportedCandidate,
)
from matintegrity.models.assembly_numeric import FadEnvelopeAssessment, TubeBundleInventory
from matintegrity.models.atmospheric import (
    AtmosphericFirstYearFit,
    AtmosphericFirstYearFitRow,
    AtmosphericFirstYearModel,
    AtmosphericFirstYearPrediction,
)
from matintegrity.models.atmospheric_ensemble import AtmosphericScenario, AtmosphericScenarioEnsemble
from matintegrity.models.bolted_joint_assembly_profile import (
    AssemblyBoltPreload,
    BoltedJointAssemblyAssessment,
    BoltedJointAssemblyAssessmentResult,
    CallerBoltedJointProfile,
    CallerGasketCompressionRecoveryEnvelope,
    FlangeFaceAlignmentObservation,
    GasketAssemblyMeasurement,
    JointAssemblyRuleFinding,
    JointLeakageObservation,
    JointThermalPressureCycle,
)
from matintegrity.models.bonded_layer_integrity_campaign import (
    BondedAssemblyEvidence,
    BondedAssemblyGeometry,
    BondedLayerCallerProfile,
    BondedLayerCriterion,
    BondedLayerIntegrityCampaignAssessment,
    BondedLayerIntegrityCampaignReport,
    BondedLayerObservation,
    BondedLayerSample,
    BondProcessEvent,
)
from matintegrity.models.brazing_bonding_campaign import (
    BrazingBondingCampaignResult,
    BrazingBondingProductionCampaign,
    CallerBrazingBondingProfile,
    CallerProductionCriterion,
    CampaignFinding,
    ProductionCycleInterval,
    ProductionJointMeasurement,
    ProductionJointRecord,
)
from matintegrity.models.burst_validation import BurstPressureComparison, BurstPressureComparisonRow
from matintegrity.models.carbonate_alkalinity import (
    CarbonateActivityConstants,
    CarbonateAlkalinitySpeciation,
)
from matintegrity.models.casting_forging_quality_campaign import (
    CastingForgingCallerProfile,
    CastingForgingQualityCampaignAssessment,
    CastingForgingQualityCampaignReport,
    CastingForgingQualityCriterion,
    ManufacturedProductEvidence,
    ManufacturingHeatTreatment,
    ProductQualityObservation,
    ProductSampleEvidence,
)
from matintegrity.models.certificate_campaign import CertificateCampaign, CertificateCoverageRecord
from matintegrity.models.chemical_cleaning import (
    ChemicalCleaningRecord,
    ChemicalCleaningStep,
    CleaningCompatibilityEnvelope,
)
from matintegrity.models.chemical_cleaning_bath_inventory import ChemicalCleaningBathHistory
from matintegrity.models.chemical_cleaning_campaign import (
    ChemicalBatch,
    ChemicalCleaningCampaign,
    ChemicalComponent,
    CleaningEvent,
    CleaningMeasurement,
    WasteDisposition,
)
from matintegrity.models.chemical_cleaning_campaign import (
    Criterion as ChemicalCleaningCriterion,
)
from matintegrity.models.chemical_cleaning_campaign import (
    Profile as ChemicalCleaningProfile,
)
from matintegrity.models.chemical_cleaning_campaign import (
    Result as ChemicalCleaningResult,
)
from matintegrity.models.chloride_scc import SCCCrackVelocityHistoryRequest, SCCCrackVelocityLaw
from matintegrity.models.classification_assignment import (
    ClassificationContext,
    ClassificationQuery,
    ClassificationWPSBinding,
    DeclaredClassificationRecord,
)
from matintegrity.models.co2_fixed_fugacity_equilibrium import (
    Co2HenrySolubilityRecord,
    FixedFugacityCarbonateEnsemble,
    FixedFugacityCarbonateEquilibrium,
    FixedFugacityCarbonateHistory,
    FixedFugacityCarbonateScenario,
)
from matintegrity.models.co2_fugacity import (
    CoolPropCo2FugacityRequest,
    CoolPropCo2MixtureFugacityRequest,
    MixtureCo2FugacityHistory,
    PureCo2FugacityHistory,
)
from matintegrity.models.co2_henry_carbonate_adapter import (
    Co2HenryCarbonateAdapterRequest,
    FixedFugacityCarbonateEquilibriumTemplate,
)
from matintegrity.models.co2_henry_carbonate_history_adapter import Co2HenryCarbonateHistoryAdapterRequest
from matintegrity.models.co2_henry_vant_hoff import Co2HenryTemperatureCorrectionRequest
from matintegrity.models.coating_campaign_profile import (
    CallerCoatingCampaignProfile,
    CallerCoatingMetricRule,
    CoatingCampaignAssessment,
    CoatingCampaignAssessmentResult,
    CoatingCampaignFinding,
    CoatingCureHeatInterval,
    CoatingQualityMeasurement,
)
from matintegrity.models.competitive_solid_activity_iteration import CompetitiveSolidDaviesIteration
from matintegrity.models.competitive_solid_bdot_iteration import CompetitiveSolidBdotIteration
from matintegrity.models.competitive_solid_sit_iteration import CompetitiveSolidSITIteration
from matintegrity.models.component_material_class import (
    ComponentMaterialClassAssessment,
    ComponentMaterialRequirement,
    MaterialClassComponentRecord,
)
from matintegrity.models.composition_temperature import CompositionSupportRange
from matintegrity.models.constitutive import MorrowStrainLife, SWTStrainLife
from matintegrity.models.continuous_plane_life_bound import ContinuousPlaneFsLifeBound
from matintegrity.models.corrosion import (
    CorrosionRateJointScenario,
    CorrosionRateModelOutputWallLossScenario,
    CorrosionRateObservation,
    CorrosionRateProjectionRow,
    CorrosionRateQuantileForecast,
    CorrosionRateSampleSummary,
    CouponLoss,
    CouponLossWithUncertainty,
    FaradayLoss,
    MaterialCorrosionRateContrast,
    SimulationRateWallLossScenario,
)
from matintegrity.models.crack import (
    CrackGrowthScenario,
    CrackGrowthScenarioEvaluation,
    CrackGrowthScenarioManifestRow,
    CrackGrowthUncertaintyDesignLevel,
    CrackGrowthUncertaintySample,
    TabulatedCrackGrowth,
    TabulatedCrackGrowthCurve,
    TabulatedCrackGrowthCurveFamily,
    TabulatedCrackGrowthScenarioEnsemble,
    TabulatedCrackGrowthScenarioReduction,
    TabulatedCrackGrowthUncertainty,
    TabulatedCrackGrowthUncertaintyConvergence,
    TabulatedCurveFamilyGrowth,
    TabulatedGrowthLoadBlock,
    TabulatedGrowthRateQuery,
)
from matintegrity.models.creep import CreepLifeModel
from matintegrity.models.crevice_aperture_refinement import CreviceApertureHistoryRefinement
from matintegrity.models.crevice_chemistry import (
    CreviceRateSupport,
    CreviceSpecies,
    CreviceSpeciesInventoryHistory,
    CreviceSpeciesRateInterval,
)
from matintegrity.models.crevice_component_diffusion import (
    CreviceComponentDiffusionHistory,
    CreviceComponentDiffusionInterval,
    CreviceComponentDiffusionSupport,
)
from matintegrity.models.crevice_composition_mass_action import CreviceCompositionToMassActionHistory
from matintegrity.models.crevice_electrochemical_composition import (
    CreviceElectrochemicalCompositionHistory,
    CreviceElectrolyteVolumeKnot,
    CreviceInitialSpeciesInventory,
)
from matintegrity.models.crevice_electrochemical_inventory import CreviceElectrochemicalInventoryIntegration
from matintegrity.models.crevice_kinetic_network import (
    CreviceAqueousKineticNetwork,
    CreviceKineticInterval,
    CreviceKineticReaction,
    CreviceKineticSpecies,
    CreviceKineticTerm,
)
from matintegrity.models.crevice_lumped_exchange_reaction import CreviceLumpedExchangeReactionHistory
from matintegrity.models.crevice_mixed_potential_history import (
    CreviceMixedPotentialHistory,
    CreviceMixedPotentialReaction,
)
from matintegrity.models.crevice_nernst_profile import CreviceNernstProfile, NernstDrivenButlerVolmerHistory
from matintegrity.models.crevice_wall_shear_exposure import CreviceWallShearExposure
from matintegrity.models.damage_mechanism_screening import DamageMechanismFact, DamageMechanismProfile
from matintegrity.models.davies_activity import DaviesActivityCoefficientInput, DaviesActivitySpecies
from matintegrity.models.degradation import CavitationHistory
from matintegrity.models.eddy_current import (
    EddyCurrentExamination,
    EddyCurrentIndication,
    EddyCurrentProbe,
    EddyCurrentReferenceFeature,
    EddyCurrentReferenceStandard,
    EncodedEddyCurrentScan,
)
from matintegrity.models.electrochemical_crevice_geometry import (
    ElectrochemicalCreviceGeometryHistory,
    ReactionCellVolumeAllocation,
)
from matintegrity.models.electrochemical_metal_loss import (
    ElectrochemicalMetalLossHistory,
    MetalDissolutionReactionMapping,
)
from matintegrity.models.electrochemical_wall_thickness import ElectrochemicalWallThicknessHistory
from matintegrity.models.electrochemical_wall_thickness_scenario_envelope import (
    ElectrochemicalWallThicknessScenario,
    ElectrochemicalWallThicknessScenarioEnvelope,
)
from matintegrity.models.electrochemistry import (
    ChronoamperometryWindowSummary,
    MixedPotential,
    MixedPotentialEquilibrium,
    PolarizationCurve,
    PolarizedElectrode,
)
from matintegrity.models.electromagnetic_campaign_quality import (
    ElectromagneticAcquisitionConfiguration,
    ElectromagneticCampaignAcceptanceProfile,
    ElectromagneticCampaignQualityAssessment,
    ElectromagneticCampaignQualityReport,
    ElectromagneticQualityCriterion,
    ElectromagneticReferenceCheck,
    ElectromagneticReferenceFeature,
    ElectromagneticReferenceStandard,
    EncodedElectromagneticScanEvidence,
)
from matintegrity.models.engineering_correlations import (
    BlindIndicatorHoleLigament,
    BoltReferenceTorqueScaling,
    BrinellSurfaceObservation,
    CarbonEquivalentRecipe,
    CarbonIndexResponse,
    CarbonIndexTerm,
    ChemicalAnalysisLimit,
    ChemicalAnalysisLinearRule,
    ChemicalAnalysisObservation,
    ChemicalAnalysisSumRule,
    ChemicalToleranceBranch,
    CompositionIndexFactor,
    CompositionIndexRecipe,
    CompositionIndexTerm,
    CorrelationBasis,
    CouplingPressure,
    DeclaredAnalysisToleranceRecipe,
    DeclaredChemicalAnalysisComparison,
    DeclaredConsumableDepositionRate,
    DeclaredEquipmentEffectiveness,
    DeclaredFluxBasicityRatio,
    DeclaredHydrogenSusceptibilityIndex,
    DeclaredImpactSubsizeRequirements,
    DeclaredInverseSqrtDensityVelocity,
    DeclaredLogSlopeRuptureFactor,
    DeclaredParetoCategory,
    DeclaredParetoSummary,
    DeclaredShellCharacteristicLengths,
    DevicePressureDropCavitationIndex,
    FlooredCompositionIndexRecipe,
    FluxMoistureHydrogen,
    FrictionResolvedBoltTorque,
    GoverningThicknessRecipe,
    HomogeneousNoSlipMixtureDensity,
    HotTapBranchTestPressureCap,
    ImpactWidthTemperatureReduction,
    IndicationWindowAccumulation,
    MatingBrinellHardnessDifference,
    MeanShearStress,
    NoSlipPhaseFlow,
    PiecewiseThicknessSoakDuration,
    PipeBendWallAllowance,
    PipingDisplacementAllowance,
    PlanarStressLinearization,
    PressureTemperatureRampLimits,
    ProjectedIndicationInterval,
    ReliefPressureEnvelope,
    ResinHdtHeadroom,
    ScaledStrengthCandidate,
    ScaledStrengthMinimum,
    SolutionConcentrationConversion,
    SteelCompositionIndexRecipe,
    TemperatureTrendStrengthScaling,
    ThicknessDimension,
    ThicknessExpression,
    ThicknessRetentionFactor,
    ThicknessScaledRateLimit,
    ThicknessSoakBand,
    ThicknessSoakDuration,
    ThreadConnectionPressure,
    TubeBendPreformThickness,
    TubeExpansionWallReduction,
    WeldCoolingCorrelation,
    WellMixedGasPurge,
    WellMixedPurgeStage,
    ZenerHollomonParameter,
)
from matintegrity.models.extended_debye_huckel_activity import (
    ExtendedDebyeHuckelActivityInput,
    ExtendedDebyeHuckelSpecies,
)
from matintegrity.models.external_crevice_solver import ExternalCreviceSolverHistory
from matintegrity.models.external_flange_compliance import ExternalFlangeComplianceBinding
from matintegrity.models.external_flange_diagnostic_screen import (
    ExternalFlangeDiagnosticScreenRequest,
    FlangeDiagnosticCriterion,
)
from matintegrity.models.external_gasket_fe_field_import import (
    ExternalGasketFEFieldImportRequest,
    GasketFEContactLocation,
    GasketFEContactSnapshot,
    GasketFEFieldSelection,
    GasketFENormalizedFieldArray,
    GasketFESupportObservation,
)
from matintegrity.models.external_pressure_campaign import (
    ExternalPressureCampaignAssessment,
    ExternalPressureCampaignCallerProfile,
    ExternalPressureCampaignReport,
    ExternalPressureConvergenceEvidence,
    ExternalPressureReceiptCriterion,
)
from matintegrity.models.fabrication import (
    MeasuredPipeOvality,
    MeasuredWeldEnergy,
    RosenthalCoolingIntervalLink,
    RosenthalPointSource3D,
    WaveformEnergy,
    WeldPowerTravel,
)
from matintegrity.models.fabrication_surface import (
    CoatingDamageAreaInventory,
    CoatingDamagePatch,
    DepositedLayerGeometry,
    DepositionRemovalHistory,
    LayerGeometryEvent,
    SurfaceProfileDeviation,
    SurfaceProfilePoint,
    SurfaceProfileRoughness,
)
from matintegrity.models.fad import FailureAssessment, FailureAssessmentCurve, FailureAssessmentPoint
from matintegrity.models.fatigue import (
    CriticalPlaneContinuousBound,
    CriticalPlanePiecewiseLinearTimeHistory,
    CriticalPlaneProjectedRainflow,
)
from matintegrity.models.fatigue_benchmark import (
    CyclicResponseRelativeError,
    CyclicResponseSeries,
    DynamicModulusDropEndpoint,
    FatigueLifeRmsle,
)
from matintegrity.models.fatigue_findley import CriticalPlaneFindleyStressHistory
from matintegrity.models.fatigue_findley_life import (
    CriticalPlaneFindleyCalibratedLife,
    FindleyParameterLifePoint,
)
from matintegrity.models.fault_tree import FaultTreeAssessment, FaultTreeBasicEvent
from matintegrity.models.file_fmc_tfm import (
    FileHomogeneousFmcTfm,
    FilePlanarMultiviewFmcTfm,
    FmcNpyMatrix,
    StoredFmcTrace,
)
from matintegrity.models.flange_compliance_reduction import (
    FlangeComplianceReductionHistoryRequest,
    FlangeComplianceReductionRequest,
)
from matintegrity.models.flange_contact_field import (
    FlangeContactFieldRequest,
    FlangeNonlinearContactFieldRequest,
    FlangePronyBranch,
    FlangeViscoelasticContactHistoryRequest,
)
from matintegrity.models.flange_nonlinear_viscoelastic import FlangeNonlinearViscoelasticContactHistory
from matintegrity.models.fmc_tfm import FmcElement, FmcTimeTrace, HomogeneousFmcTfm, TfmImagePoint
from matintegrity.models.forming_qualification import (
    FormingOperation,
    FormingProcessSequence,
    FormingSequencePlan,
    FormingTreatmentWaiverBranch,
    InterOperationCoolingPoint,
)
from matintegrity.models.fracture_toughness_testing import (
    CallerValidityFlag,
    FatiguePrecrackEvidence,
    FractureSpecimenGeometry,
    FractureToughnessCallerProfile,
    FractureToughnessCampaignAssessment,
    FractureToughnessCampaignReport,
    FractureToughnessCriterion,
    FractureToughnessSpecimenRecord,
)
from matintegrity.models.galvanic_coupling import (
    ElectricalConnection,
    GalvanicCouplingAssessment,
    GalvanicElectrodeEvidence,
    GalvanicEnvironment,
    PartialDissolutionObservation,
)
from matintegrity.models.galvanic_resistive_coupling import (
    ResistanceComponent,
    ResistiveGalvanicConnection,
    ResistiveGalvanicCoupling,
)
from matintegrity.models.gasket_bolt_cyclic_damage import BoltFatigueCurve, GasketBoltCyclicDamage
from matintegrity.models.gasket_bolt_preload_sequence_redistribution import (
    GasketBoltPreloadSequenceRedistribution,
    GasketBoltTighteningOperation,
)
from matintegrity.models.gasket_bolt_strength_margin import (
    BoltMaterialStrengthBasis,
    BoltProofStrengthPoint,
    GasketBoltNominalStrengthScreen,
)
from matintegrity.models.gasket_circumferential_contact_continuity import (
    CircumferentialContactNode,
    GasketCircumferentialContactContinuity,
)
from matintegrity.models.gasket_compression_curve_monotone_fit import (
    GasketCompressionCurveMonotoneFit,
    GasketCompressionCurveObservation,
)
from matintegrity.models.gasket_compression_hysteresis_energy import (
    GasketCompressionHysteresisEnergy,
    GasketCompressionLoop,
)
from matintegrity.models.gasket_contact_distribution_statistics import (
    GasketContactDistributionStatistics,
    GasketPressureThreshold,
)
from matintegrity.models.gasket_contact_pressure_screen import GasketContactPressureScreen
from matintegrity.models.gasket_contact_root_localization import (
    ContactResponseQuery,
    ContactResponseReceipt,
    GasketContactRootLocalization,
)
from matintegrity.models.gasket_contact_state_grid_sweep import (
    ExternalContactStateGridQuery,
    ExternalContactStateGridResponse,
    GasketContactStateGridSweep,
)
from matintegrity.models.gasket_contact_subthreshold_exposure import GasketContactSubthresholdExposure
from matintegrity.models.gasket_contact_transition_brackets import GasketContactTransitionBrackets
from matintegrity.models.gasket_contact_transition_refinement import (
    ExternalContactStateQuery,
    ExternalContactStateResponse,
    GasketContactTransitionRefinement,
)
from matintegrity.models.gasket_contact_window_events import GasketContactPressureWindowEvents
from matintegrity.models.gasket_evidence_bound_prony_history import (
    EvidenceBoundGasketViscoelasticHistoryRequest,
    EvidenceBoundGasketViscoelasticMaterial,
)
from matintegrity.models.gasket_fe_von_mises_caller_limit_screen import (
    GasketFEVonMisesCallerLimitScreen,
    TensorComponentBinding,
)
from matintegrity.models.gasket_finite_scenario_dependence import GasketFiniteScenarioDependence
from matintegrity.models.gasket_joint_equilibrium_covariance import (
    GasketJointEquilibriumLocalCovariance,
    JointLoadCovarianceCoordinate,
)
from matintegrity.models.gasket_joint_spatial_resultants import (
    GasketBoltPlanarPosition,
    GasketContactNodePlanarPosition,
    GasketJointSpatialResultantBalance,
)
from matintegrity.models.gasket_leakage_calibration import (
    GasketLeakageCalibrationMap,
    GasketLeakageCalibrationRow,
    GasketLeakageHistory,
    GasketLeakageNodePressureEnvelope,
    GasketLeakageRateEnvelope,
)
from matintegrity.models.gasket_leakage_fit_diagnostics import GasketLeakageFitDiagnostics
from matintegrity.models.gasket_leakage_map_fit import GasketLeakageFitObservation, GasketLeakageMapFit
from matintegrity.models.gasket_leakage_rate_threshold_events import GasketLeakageRateThresholdEvents
from matintegrity.models.gasket_leakage_scenario_exposure import GasketLeakageScenarioExposure
from matintegrity.models.gasket_multi_bolt_sector_equilibrium import GasketMultiBoltSectorEquilibrium
from matintegrity.models.gasket_nominal_contact_pressure import GasketNominalContactPressureRequest
from matintegrity.models.gasket_pressure_inventory_decay import GasketPressureInventoryDecay
from matintegrity.models.gasket_radial_open_path import GasketPolarContactMap, GasketRadialOpenPathScreen
from matintegrity.models.gasket_temperature_compression_curve import (
    GasketTemperatureCompressionCurveTransfer,
    TemperatureCompressionCurve,
)
from matintegrity.models.gasket_temperature_compression_joint_history import (
    GasketTemperatureCompressionJointHistory,
    TemperatureJointBolt,
    TemperatureJointLoadStep,
    TemperatureJointSector,
)
from matintegrity.models.gasket_temperature_shifted_prony_history import (
    GasketPronyTemperatureShiftLaw,
    GasketTemperatureShiftedPronyHistory,
)
from matintegrity.models.gasket_thermoelastic_expansion_joint_history import (
    ComponentThermalExpansionRecord,
    GasketThermoelasticExpansionJointHistory,
)
from matintegrity.models.gasket_transient_exposure import GasketLeakageScenarioRateInterval
from matintegrity.models.grain_planimetry import GrainCountField
from matintegrity.models.hardness_testing_campaign import (
    HardnessCampaignCallerProfile,
    HardnessReading,
    HardnessReferenceBlockEvidence,
    HardnessTestConfiguration,
    HardnessTestingCampaign,
    HardnessTestSubject,
)
from matintegrity.models.hydrogen import HydrogenTrapPopulation
from matintegrity.models.hydrogen_calibration import HydrogenThermalRateFit
from matintegrity.models.hydrogen_cylinder import HydrogenFiniteCylinder
from matintegrity.models.hydrogen_inverse import HydrogenSlabFlowMultiplierFit
from matintegrity.models.hydrogen_kinetics import HydrogenKineticTrap, HydrogenSlab, LatticeBoundary
from matintegrity.models.hydrogen_observation import HydrogenDetectorObservation
from matintegrity.models.hydrogen_rates import HydrogenTrapThermalRates, ThermallyActivatedFrequency
from matintegrity.models.hydrogen_surface import (
    HydrogenDissociativeSurfaceRates,
    ThermallyActivatedSurfaceFlux,
)
from matintegrity.models.imaging_campaign_quality import (
    ImagingAcquisitionEvidence,
    ImagingCampaignAcceptanceProfile,
    ImagingCampaignQualityAssessment,
    ImagingCampaignQualityReport,
    ImagingQualityCriterion,
    ImagingReferenceFeature,
    ImagingReferenceStandard,
    ImagingReferenceVerification,
)
from matintegrity.models.impact_metric_crossings import ImpactMetricCrossings, ImpactMetricPoint
from matintegrity.models.impact_testing_campaign import (
    ImpactCampaignCallerProfile,
    ImpactMachineConfiguration,
    ImpactMetricCriterion,
    ImpactReportedResult,
    ImpactSpecimenIdentity,
    ImpactTestingCampaign,
    ImpactTestRecord,
)
from matintegrity.models.ince_glinka_gsa import InceGlinkaGSACalculation
from matintegrity.models.inspection import (
    FiniteInspectionPolicyPathGeneration,
    FinitePolicyAction,
    FinitePolicyDecisionEpoch,
    FinitePolicyDecisionRule,
    FinitePolicyObservationProbability,
    FinitePolicyProbabilityCalibration,
    FinitePolicyState,
    FinitePolicyTransitionProbability,
    GuidedWavePairFeatures,
    GuidedWaveReferenceEnsemble,
    InitialPolicyStateProbability,
    InspectionActionExpectedLossComparison,
    InspectionActionRiskCandidate,
    InspectionDispositionDecisionTree,
    InspectionDispositionOutcomeBranch,
    InspectionForecastPoint,
    InspectionPolicyPath,
    InspectionPolicyStage,
    MultiPeriodInspectionPolicyCandidate,
    MultiPeriodInspectionPolicyComparison,
    MultiPeriodInspectionPolicyEvaluation,
    PipeMembraneTestPressure,
    PolicyCalibrationAction,
    PolicyObservationCalibrationRecord,
    PolicyObservationLabel,
    PolicyResourceConstraint,
    PolicyResourceUsage,
    PolicyStageCostComponent,
    PolicyTransitionCalibrationRecord,
    PulseEchoCalibrationObservation,
    PulseEchoSoundSpeedFit,
    ReferenceEnergyMass,
    RiskCostComponent,
    ThresholdInspectionSchedule,
    VisualExaminationArea,
    VisualSurfaceExamination,
    VisualSurfaceIndication,
)
from matintegrity.models.inspection_sampling import (
    InspectionLotSampling,
    InspectionSamplingPlan,
    InspectionUnitOutcome,
)
from matintegrity.models.leak_campaign_quality import (
    BlankBackgroundObservation,
    DetectionCapabilityEvidence,
    LeakCampaignAcceptanceProfile,
    LeakCampaignQualityCriterion,
    LeakCampaignStateIdentity,
    LeakTestCampaignQualityAssessment,
    ReferenceLeakCampaignPoint,
)
from matintegrity.models.local_capacity import (
    BulgingFactorTable,
    ProfileCapacityCorrosionScenario,
    ProfileCapacityRateFieldScenario,
    ReferenceCapacity,
)
from matintegrity.models.magnetic_flux_leakage import (
    EncodedMflScan,
    MflExamination,
    MflIndication,
    MflMagneticFieldCheckpoint,
    MflMagnetizer,
    MflReferenceFeature,
    MflReferenceStandard,
    MflSensorArray,
)
from matintegrity.models.materials import FormingAreaReduction
from matintegrity.models.mcdiarmid_miner_campaign import (
    McDiarmidCycleBlock,
    McDiarmidIndexLifePoint,
    McDiarmidLifeCurve,
    McDiarmidMinerCampaign,
)
from matintegrity.models.mechanics import (
    PressureTemperatureEnvelope,
    PressureTemperatureEnvelopeKnot,
    PressureTemperatureOperatingPoint,
)
from matintegrity.models.multi_bolt_flange_contact_influence import (
    MultiBoltFlangeContactInfluenceOutput,
    MultiBoltFlangeContactInfluenceRequest,
)
from matintegrity.models.multiaxial_life_scenario_envelope import (
    MultiaxialLifeScenario,
    MultiaxialLifeScenarioEnvelope,
)
from matintegrity.models.multiaxial_mcdiarmid_limit_screen import (
    McDiarmidCandidatePlane,
    McDiarmidCriticalPlaneLimitScreen,
    McDiarmidTensorState,
)
from matintegrity.models.multiaxial_weighted_life_scenarios import MultiaxialWeightedLifeScenarioMoments
from matintegrity.models.multiaxial_work_life import ClosedTensorCycle, ClosedTensorWorkLife
from matintegrity.models.multienvironment_material_profile import (
    CallerEnvironmentEnvelope,
    CallerMaterialStateProfile,
    CallerPropertyRule,
    MaterialExposureInterval,
    MaterialProfileFinding,
    MaterialPropertyObservation,
    MaterialStateIdentity,
    MediaComponentConcentration,
    MultiEnvironmentMaterialAssessment,
    MultiEnvironmentMaterialAssessmentResult,
    PropertyEnvelopePoint,
)
from matintegrity.models.overlay_cladding_campaign import (
    CallerOverlayCriterion,
    CallerOverlayProfile,
    OverlayCladdingCampaign,
    OverlayCladdingCampaignResult,
    OverlayDepositionPass,
    OverlayFinding,
    OverlayHeatInterval,
    OverlayMeasurement,
)
from matintegrity.models.phase_fraction_contrast import (
    PhaseFractionContrastAssessment,
    PhaseFractionContrastObservation,
    PhaseFractionContrastRequirement,
    PhaseFractionCovariance,
    PhaseFractionLinearTerm,
)
from matintegrity.models.phase_point_count import PhasePointCountField, PhasePointCountSummary
from matintegrity.models.phased_array import (
    EncodedPhasedArrayFrame,
    PhasedArrayBeamLaw,
    PhasedArrayExamination,
    PhasedArrayIndication,
    PhasedArrayProbe,
    PhasedArrayWedge,
)
from matintegrity.models.piping_class import PipingClassAssessment, PipingComponentRecord, PipingComponentRule
from matintegrity.models.pitzer_single_salt import PitzerSingleSaltActivity
from matintegrity.models.planar_multiview_tfm import PlanarMultiviewFmcTfm, PlanarTfmView
from matintegrity.models.planar_slit_transient_hydraulic import PlanarSlitTransientHydraulicHistory
from matintegrity.models.production_weld_test_campaign import (
    CallerProductionWeldTestProfile,
    CallerWeldTestCriterion,
    ProductionWeldIdentity,
    ProductionWeldTestCampaign,
    ProductionWeldTestCampaignResult,
    WeldCouponSpecimen,
    WeldTestFinding,
    WeldTestMeasurement,
)
from matintegrity.models.quality import ProvenanceWeldConstituent, WeldDilutionUncertainty
from matintegrity.models.radiography import (
    RadiographicExamination,
    RadiographicImageIndication,
    RadiographicImageQualityRecord,
)
from matintegrity.models.rectilinear_thickness_map import RectilinearThicknessMap
from matintegrity.models.reliability import (
    BayesianLinearThicknessUpdate,
    ContinuousTimeMarkovChain,
    GaussianMeanShiftImportanceSampling,
    GaussianThicknessPosteriorSampleDesign,
    JointEventDistribution,
    LinearThicknessFirstPassageSample,
    LinearThicknessStateSpaceUpdate,
    PiecewiseContinuousTimeMarkovChain,
    SampledLinearThicknessFirstPassage,
    ThicknessObservation,
)
from matintegrity.models.repair_welding_campaign import (
    Criterion as RepairWeldingCriterion,
)
from matintegrity.models.repair_welding_campaign import (
    ExcavationEvidence,
    RepairEvent,
    RepairIdentity,
    RepairObservation,
    RepairWeldingCampaign,
)
from matintegrity.models.repair_welding_campaign import (
    Profile as RepairWeldingProfile,
)
from matintegrity.models.repair_welding_campaign import (
    Result as RepairWeldingResult,
)
from matintegrity.models.replica_metallography_campaign import (
    ReplicaAcquisitionConfiguration,
    ReplicaCampaignCallerProfile,
    ReplicaCampaignField,
    ReplicaCampaignObservation,
    ReplicaMetallographyCampaign,
    ReplicaObservationCriterion,
    ReplicaServiceInterval,
)
from matintegrity.models.scale_coverage_kinetics import CallerScaleCoverageKinetics
from matintegrity.models.scale_film_transport import LayeredScaleDiffusionLimit, ScaleTransportLayer
from matintegrity.models.scale_moving_boundary import (
    PlanarScaleDiffusionReactionHistory,
    ScaleDiffusionReactionInterval,
)
from matintegrity.models.scale_reaction_demand_balance import (
    PlanarScaleReactionDemandBalance,
    ScaleReactionDemandInterval,
)
from matintegrity.models.scc_rule_screening import (
    SCCMechanismProfile,
    SCCRuleCondition,
    SCCScreeningFact,
    SCCScreeningRule,
    UserDefinedSCCScreening,
)
from matintegrity.models.service_category_screening import (
    ServiceCategoryCondition,
    ServiceCategoryFact,
    ServiceCategoryProfile,
    ServiceCategoryRule,
)
from matintegrity.models.sit_activity import SITActivityCoefficientInput, SITInteraction, SITSpecies
from matintegrity.models.specification_aliases_campaign import (
    SpecificationAliasProfileSetAudit,
    SpecificationAliasQuery,
    SpecificationProfileMaterialBinding,
)
from matintegrity.models.storage_preservation_campaign import (
    PreservationCampaignFact,
    PreservationFactCriterion,
    PreservationSystemIdentity,
    StoragePreservationCallerProfile,
    StoragePreservationCampaign,
    StoragePreservationEvent,
)
from matintegrity.models.surface_cleanliness_campaign import (
    CallerCleanlinessProfile,
    CleanlinessCriterion,
    CleanlinessMeasurement,
    PreparationEvent,
    SurfaceCleanlinessCampaign,
    SurfaceCleanlinessResult,
)
from matintegrity.models.surface_cleanliness_campaign import (
    Finding as SurfaceCleanlinessFinding,
)
from matintegrity.models.surface_examination import (
    LiquidPenetrantExamination,
    MagneticParticleExamination,
    MagnetizationPass,
    SurfaceExaminationArea,
    SurfaceIndication,
)
from matintegrity.models.surface_indication_assessment import (
    AcceptanceRuleEvaluation,
    CallerAcceptanceProfile,
    CallerIndicationGroup,
    ExaminedSurfaceRegion,
    NumericAcceptanceRule,
    ProfileSurfaceIndication,
    ProhibitedClassRule,
    SurfaceIndicationAssessment,
    SurfaceIndicationAssessmentResult,
    SurfaceInspectionProcedure,
)
from matintegrity.models.surface_scale_kinetics import (
    CallerSurfaceScaleKinetics,
    SurfaceScaleKineticInterval,
)
from matintegrity.models.tensile_offset_yield_campaign import (
    TensileCampaignCallerProfile,
    TensileMachineConfiguration,
    TensileMetricCriterion,
    TensileOffsetYieldCampaign,
    TensileReportedResult,
    TensileSpecimenIdentity,
    TensileTestRecord,
)
from matintegrity.models.test_water_quality_campaign import (
    TestWaterAnalyticalResult,
    TestWaterCallerProfile,
    TestWaterCircuitIdentity,
    TestWaterCriterion,
    TestWaterHistoryEvent,
    TestWaterQualityCampaignAssessment,
    TestWaterQualityCampaignReport,
    TestWaterSample,
)
from matintegrity.models.testmethods import (
    BoilOffCalorimetry,
    KnoopIndent,
    RockwellDepth,
    SaturationCalorimetryState,
)
from matintegrity.models.thermal_transient import (
    ThermalStressPropertyEvidence,
    ThroughWallThermalStress,
)
from matintegrity.models.thermohistory import (
    CoolingInterval,
    CoolingIntervalBatch,
    CoolingIntervalBranch,
    CoolingIntervalSensorBatch,
    CoolingIntervalSensorBranch,
    CoolingIntervalSensorTrace,
)
from matintegrity.models.tofd import (
    EncodedTofdFrame,
    TofdDiffractionPick,
    TofdExamination,
    TofdIndication,
    TofdProbePair,
)
from matintegrity.models.transport_erection import (
    EquipmentMassComponent,
    EquipmentMassProperties,
    EquipmentTwoSupportLift,
)
from matintegrity.models.transport_erection_campaign import (
    ErectionMeasurement,
    HandlingObservation,
    OrderedHandlingEvent,
    TemporarySupportEvidence,
    TransportErectionCallerProfile,
    TransportErectionCampaignAssessment,
    TransportErectionCampaignReport,
    TransportErectionCriterion,
)
from matintegrity.models.under_insulation_campaign import (
    CUIAccessCoverageRegion,
    CUIAccessInspectionRepairEvent,
    CUICallerProfile,
    CUICampaignCriterion,
    CUIEvidenceReceipt,
    CUIObservation,
    CUIScopeIdentity,
    UnderInsulationCampaignAssessment,
    UnderInsulationCampaignReport,
)
from matintegrity.models.wave_campaign_quality import (
    WaveAcquisitionConfiguration,
    WaveAcquisitionRecord,
    WaveArrayElement,
    WaveCampaignAcceptanceProfile,
    WaveCampaignQualityAssessment,
    WaveCampaignQualityReport,
    WaveQualityCriterion,
    WaveReferenceSourceCheck,
)
from matintegrity.models.wco2_chemistry_boundary import (
    ChemistryBoundaryLink,
    ChemistryBoundaryStage,
    ElectrochemicalChemistryBoundaryAudit,
    SpeciesHandoff,
)
from matintegrity.models.wco2_species_transfer import (
    ExcludedSpecies,
    SpeciesComposition,
    SpeciesTransferRule,
    StoichiometricTransferTerm,
    Wco2SpeciesTransferAuditRequest,
)
from matintegrity.models.weld_compatibility_profile import (
    CallerWeldCompatibilityProfile,
    CompatibilityFact,
    CompatibilityLayer,
    CompatibilityMaterial,
    CompatibilityRuleFinding,
    CompatibilityServiceEnvironment,
    IdentityEnvelopeRule,
    NumericEnvelopeRule,
    WeldCompatibilityAssessment,
    WeldCompatibilityAssessmentResult,
)
from matintegrity.models.weld_hardness_mapping_campaign import (
    HardnessRegionCriterion,
    WeldHardnessCallerProfile,
    WeldHardnessMappingCampaignAssessment,
    WeldHardnessMappingCampaignReport,
    WeldHardnessPoint,
    WeldHardnessSubject,
    WeldHardnessTraverse,
)
from matintegrity.models.weld_hardness_mapping_campaign import (
    HardnessTestConfiguration as WeldHardnessTestConfiguration,
)
from matintegrity.models.welding import HydrogenBakeoutSlab
from matintegrity.models.welding_preheat import (
    PreheatHistoryBinding,
    PreheatMeasurementIdentity,
    PreheatMeasurementTrace,
    PreheatMeasurementWindow,
    PreheatProcedureTemplate,
)
from matintegrity.models.welding_residual_stress import (
    DeclaredResidualStressSupport,
    ResidualStressEvidenceAssessment,
    ResidualStressEvidenceRecord,
    ResidualStressProviderQualification,
)
from matintegrity.models.wet_co2_elemental_phase_handoff import (
    ElementalComponent,
    WetCO2PhaseHistoryHandoff,
)
from matintegrity.multiaxial_calibration_transfer_audit import (
    MultiaxialCalibrationTransferAudit,
    PairedLifeCalibrationPoint,
)
from matintegrity.multiaxial_crossland_proportional_screen import MultiaxialCrosslandProportionalLimitScreen
from matintegrity.multiaxial_cycle_block_feature_handoff import (
    CycleBlockFeatureBinding,
    CycleBlockFeatureHandoffRequest,
    FiniteCyclePlane,
    TensorCycleBlockFeatureInput,
)
from matintegrity.multiaxial_cycle_block_result_summary import CycleBlockResultSummaryRequest
from matintegrity.multiaxial_cycle_exchange import MultiaxialCycleBlockReceipt, OrderedTensorCycleBlock
from matintegrity.multiaxial_damage_provider import (
    CallerMultiaxialDamageRequest,
    CallerStatefulMultiaxialDamageRequest,
    MultiaxialFatigueLawProfile,
)
from matintegrity.multiaxial_dang_van_finite_screen import (
    DangVanFiniteSampleScreen,
    DangVanShearSystem,
)
from matintegrity.multiaxial_deviatoric_path_variation import MultiaxialDeviatoricStressPathVariation
from matintegrity.multiaxial_fourier_tensor_work import PeriodicFourierTensorWork
from matintegrity.multiaxial_fourier_work_life import FourierTensorWorkLife, FourierWorkLifeCycle
from matintegrity.multiaxial_invariant_limit_screen import MultiaxialInvariantLimitScreen
from matintegrity.multiaxial_life_campaign import (
    FsLifeCalibration,
    KandilBrownMillerLifeCalibration,
    MultiaxialLifeCampaign,
    ShearNormalLifeCurvePoint,
    ShearNormalStrainLifeCalibration,
    SwtLifeCalibration,
)
from matintegrity.multiaxial_papadopoulos_p2_finite_screen import (
    PapadopoulosP2FiniteSampleScreen,
    PapadopoulosPlaneShearQuadrature,
)
from matintegrity.multiaxial_periodic_fourier_rates import PeriodicTensorFourierRates
from matintegrity.multiaxial_periodic_fourier_reconstruction import PeriodicTensorFourierReconstruction
from matintegrity.multiaxial_power_law_life_transfer import (
    MultiaxialPowerLawLifeTransfer,
    ReferenceMultiaxialLifeCurvePoint,
)
from matintegrity.multiaxial_shear_path_area import SampledShearPathArea
from matintegrity.multiaxial_sines_life_fit import MultiaxialSinesLifeFit, SinesLifeCalibrationTest
from matintegrity.multiaxial_sines_mean_limit_screen import MultiaxialSinesMeanLimitScreen
from matintegrity.multiaxial_sines_parameter_life import MultiaxialSinesParameterLife, SinesParameterLifePoint
from matintegrity.multiaxial_stress_invariant_history import SampledStressInvariantHistory
from matintegrity.multiaxial_tensor_work_cycle import MultiaxialTensorWorkCycle
from matintegrity.multiphase_equilibrium_transport import CompetitiveSolidEquilibriumTransport
from matintegrity.multiphase_kinetic_ledger import (
    CompetingSolidKineticInterval,
    CompetingSolidKineticLedger,
    CompetingSolidSaturationInterval,
    CompetingSolidSaturationKinetics,
    KineticAqueousSpecies,
    KineticAqueousSpeciesDefinition,
    KineticSolidPhase,
    KineticSolidReaction,
    SolidSaturationRateLaw,
)
from matintegrity.multiphase_kinetic_transport import (
    CellwiseCompetingSolidRateInterval,
    CompetingSolidKineticTransport,
)
from matintegrity.nist_corr_data import NistCorrDataArchiveAudit
from matintegrity.otto_electrolyte_data import OttoElectrolyteObservation
from matintegrity.oxford_ebsd import OxfordEbsdPhaseLabelReadRecord
from matintegrity.papadopoulos_p1_calibrated_life import PapadopoulosP1CalibratedLife
from matintegrity.papadopoulos_p1_calibration import PapadopoulosP1Calibration
from matintegrity.papadopoulos_p1_finite_integral_screen import (
    PapadopoulosP1FiniteIntegralScreen,
    PapadopoulosP1ShearSystem,
)
from matintegrity.papadopoulos_p1_miner_blocks import PapadopoulosP1CycleBlock, PapadopoulosP1MinerBlocks
from matintegrity.phase_map_data import (
    PhaseFractionMapRow,
    PhaseLabelMapAreaFractionResult,
    PhaseLabelMapMetadata,
    PhasePixelLabel,
)
from matintegrity.phase_map_topology import (
    PhaseMapClusterStatistics,
    PhaseMapInterfaceLength,
    PhaseMapTopologySummary,
)
from matintegrity.pinned_exchange_validation import (
    PinnedSchemaPathFinding,
    PinnedSchemaValidationReport,
)
from matintegrity.pipeline_exchange import PipelineAssessmentRecord
from matintegrity.pipeline_ili_data import PipelineIliFeature, PipelineIliWorkbookAudit
from matintegrity.pitting_data import LocalPittingMatRecord, NumericMatVariableRecord
from matintegrity.pitzer_salt_finite_scenario_envelope import PitzerSaltFiniteScenarioEnvelope
from matintegrity.pitzer_salt_saturation_index import PitzerSaltSaturationIndex
from matintegrity.pod_campaign import (
    PODCampaignAuditReport,
    PODCampaignAuditRequest,
    PODCampaignFinding,
    PODCampaignObservation,
    PODCampaignRequirementProfile,
)
from matintegrity.polarization_316l_typed_rows import (
    Polarization316LArchiveAuditRequest,
    Polarization316LRawRow,
    Polarization316LReadAuthorization,
)
from matintegrity.pressure_decay_leak_data import (
    PressureDecayLeakArchiveAuditRequest,
    PressureDecayLeakDatasetAudit,
    PressureDecayLeakReadAuthorization,
    PressureDecayLeakSample,
    PressureDecayLeakSeriesRecord,
)
from matintegrity.principal_stress_axis_rotation import PrincipalStressAxisRotation
from matintegrity.providers import DesignPropertyTable, PropertyQuery
from matintegrity.reaction_network import MassActionNetwork, MassActionReaction
from matintegrity.records import (
    FlawRecord,
    HeatTreatmentRecord,
    InspectionRecord,
    MaterialRecord,
    WeldProcedureRecord,
)
from matintegrity.reliability_sampling import (
    SubsetSimulationLevel,
    SubsetSimulationRequest,
    SubsetSimulationResult,
)
from matintegrity.remaining_strength_surface import (
    CallerStrengthCriterion,
    CapacitySurfaceAxis,
    FlawGeometrySample,
    InterpolatedStrengthSample,
    RemainingStrengthEvaluationInput,
    RemainingStrengthEvaluationReport,
    RemainingStrengthSurface,
)
from matintegrity.restricted_transport import RestrictedTransportRequest
from matintegrity.rules import Rule
from matintegrity.saturation_history_events import (
    SaturationHistoryAssessmentBinding,
    SaturationHistoryEventRequest,
    SaturationHistoryKnot,
)
from matintegrity.scale_diffusion_metal_loss_bound import (
    ScaleDiffusionMetalLossBound,
    ScaleLimitedMetalDissolutionPathway,
)
from matintegrity.scale_layer_stack_series_transport import LayeredScaleHistorySeriesTransport
from matintegrity.scale_layer_stack_transport import (
    LayeredScaleHistoryStackTransport,
    ScaleLayerHistoryBinding,
)
from matintegrity.scale_limited_electrochemistry import ScaleLimitedSurfaceFlux
from matintegrity.scale_precipitation_inventory_budget import (
    ScaleLimitingReactantInventory,
    ScalePrecipitationInventoryBudget,
    ScaleReactantIntervalSupply,
)
from matintegrity.scale_transport_adapter import (
    ScaleHistoryTransportLink,
    ScaleHistoryTransportSeriesLink,
    ScaleLimitedElectrochemicalHistory,
    ScaleLimitedElectrochemicalHistorySegment,
)
from matintegrity.scc_fta_binding import (
    SCCFaultTreeBindingRequest,
    SCCFaultTreeEventBinding,
    SCCFaultTreeProbabilityInput,
)
from matintegrity.seccm_data import (
    SeccmArchiveAudit,
    SeccmArchiveMemberRecord,
    SeccmChronoamperometryTrace,
)
from matintegrity.sensitivity import (
    RegistrySensitivityConfiguration,
    SobolDesign,
    SobolEvaluations,
    SobolInputBatch,
    SobolReport,
    SobolRequest,
)
from matintegrity.sequence_crack_growth import SequenceCrackGrowth, SequenceGrowthState
from matintegrity.single_solid_equilibrium import PrecipitatingAqueousSpecies, SingleSolidEquilibrium
from matintegrity.spatial_fields import (
    PlanarAffineCoordinateTransform,
    RectilinearFieldMetadata,
    RectilinearFieldSamplingRequest,
    RectilinearFieldSamplingResult,
)
from matintegrity.spatial_piecewise_reaction import (
    SpatialMassActionReaction,
    SpatialPiecewiseMassAction,
    SpatialReactionInterval,
)
from matintegrity.specification_aliases import (
    SpecificationAlias,
    SpecificationAliasResolution,
    SpecificationDesignation,
    SpecificationProfile,
)
from matintegrity.strain_life_campaign import (
    StrainLifeBlock,
    StrainLifeBlockResult,
    StrainLifeCampaign,
    StrainLifeCampaignResult,
)
from matintegrity.structural_provider_acceptance import (
    RequiredStructuralField,
    StructuralAcceptanceFinding,
    StructuralAcceptanceProfile,
    StructuralAcceptanceReport,
    StructuralDiagnosticCriterion,
    StructuralDiagnosticEvidence,
    StructuralMeshReceipt,
    StructuralProviderResultReceipt,
    StructuralResultFieldReceipt,
)
from matintegrity.subset_replicates import (
    SubsetReplicateRequest,
    SubsetReplicateResult,
    SubsetReplicateTask,
    SubsetReplicateTaskResult,
)
from matintegrity.tabular_contract_import import (
    TabularFieldMapping,
    TabularImportProfile,
    TabularImportReport,
    TabularRowFinding,
)
from matintegrity.thermal_expansion import TangentExpansionTable, ThermalExpansionResult
from matintegrity.thermal_typed_rows import (
    ThermalRodArchiveAuditRequest,
    ThermalRodObservationRow,
    ThermalRodReadAuthorization,
)
from matintegrity.thermo import ThermoRequest
from matintegrity.ti12mo5hf_aesec_rows import (
    Ti12Mo5HfAESECProvenance,
    Ti12Mo5HfAESECRequest,
    Ti12Mo5HfAESECRow,
)
from matintegrity.ti12mo5hf_corrosion_data import (
    Ti12Mo5HfArchiveAudit,
    Ti12Mo5HfArchiveAuditRequest,
    Ti12Mo5HfProviderCondition,
)
from matintegrity.ti12mo5zr_corrosion_data import (
    Ti12Mo5ZrRawRow,
    Ti12Mo5ZrWorkbookProvenance,
    Ti12Mo5ZrWorkbookRequest,
)
from matintegrity.ti12mo5zr_eis_complex import (
    Ti12Mo5ZrComplexEISPoint,
    Ti12Mo5ZrComplexEISRequest,
)
from matintegrity.ti12mo5zr_mass_balance import (
    Ti12Mo5ZrMassBalanceRequest,
    Ti12Mo5ZrMassBalanceResult,
    Ti12Mo5ZrPenetrationPoint,
)
from matintegrity.ti12mo5zr_ocp_window_summary import Ti12Mo5ZrOCPWindowRequest
from matintegrity.ti12mo5zr_remaining_thickness import (
    RemainingThicknessHistory,
    RemainingThicknessKnot,
    RemainingThicknessRequest,
)
from matintegrity.tribology_metadata_data import (
    TribologyMetadataDatasetAudit,
    TribologyMetadataFileAudit,
)
from matintegrity.tube_bundle_lame_stress_history import (
    TubeBundleLameStressHistory,
    TubePressureKnot,
    TubePressureStressHistory,
)
from matintegrity.ultrasound_data import PulseEchoThicknessCalibration
from matintegrity.wall_tolerances import (
    WallThicknessReplicate,
    WallToleranceAssessment,
    WallToleranceCallerProfile,
    WallToleranceReplicateFinding,
    WallToleranceReport,
)
from matintegrity.wang_brown_excursion_parameter import WangBrownReviewedExcursionParameter
from matintegrity.wang_brown_parameter_life_fit import WangBrownParameterLifeFit
from matintegrity.wang_brown_temporal_excursion import WangBrownTemporalExcursion
from matintegrity.waveform_energy_uncertainty import WaveformEnergyUncertainty
from matintegrity.wet_co2_carbonate_alkalinity_speciation import WetCo2CarbonateAlkalinityRequest
from matintegrity.wet_co2_carbonate_transport_history import (
    CarbonateBoundaryPartitionUse,
    CarbonateTransportBoundaryHistoryKnot,
    WetCo2CarbonateTransportBoundaryHistoryRequest,
)
from matintegrity.wet_co2_condensate_state import WetCo2CondensateStateRequest
from matintegrity.wet_co2_condensation_transfer_history import (
    WetCo2GasFilmCondensationHistoryRequest,
    WetCo2GasFilmCondensationInterval,
)
from matintegrity.wet_co2_coolprop_water import CoolPropPureWaterSinglePhaseStateRequest
from matintegrity.wet_co2_cylindrical_aqueous_scale_sink_feedback import (
    WetCo2AqueousScalePhase,
    WetCo2CylindricalAqueousScaleSinkFeedback,
    WetCo2ScaleReactionKnot,
)
from matintegrity.wet_co2_cylindrical_bv_wall_recession import WetCo2CylindricalBVWallRecession
from matintegrity.wet_co2_cylindrical_coupled_scale_geometry_replay import (
    WetCo2CylindricalCoupledScaleGeometryReplay,
)
from matintegrity.wet_co2_cylindrical_diffusion_limited_scale_growth import (
    WetCo2CylindricalDiffusionLimitedScaleGrowth,
    WetCo2DiffusionLimitedBulkKnot,
    WetCo2DiffusionLimitedBulkSpecies,
    WetCo2DiffusionLimitedSolidReactant,
)
from matintegrity.wet_co2_cylindrical_finite_gas_stage_geometry_feedback import (
    WetCo2CylindricalFiniteGasStageGeometryFeedback,
)
from matintegrity.wet_co2_cylindrical_finite_gas_stage_speciation_feedback import (
    WetCo2CylindricalFiniteGasStageSpeciationFeedback,
    WetCo2FiniteGasStageSpeciationKineticPhase,
    WetCo2FiniteGasStageSpeciationProductTerm,
)
from matintegrity.wet_co2_cylindrical_finite_liquid_transfer_inventory import (
    WetCo2CylindricalExternalLiquidExchange,
    WetCo2CylindricalFiniteLiquidTransferInventory,
    WetCo2CylindricalLiquidConcentrationKnot,
)
from matintegrity.wet_co2_cylindrical_geometry_coupled_history import WetCo2CylindricalGeometryCoupledHistory
from matintegrity.wet_co2_cylindrical_hydraulics_to_scale_removal import (
    WetCo2CylindricalHydraulicsToScaleRemoval,
)
from matintegrity.wet_co2_cylindrical_liquid_transfer_capacity import (
    WetCo2CylindricalLiquidDiffusivityKnot,
    WetCo2CylindricalLiquidTransferCapacityHistory,
)
from matintegrity.wet_co2_cylindrical_multilayer_transport import (
    WetCo2CylindricalMultilayerTransportKnot,
    WetCo2CylindricalMultilayerTransportResistance,
    WetCo2LayerSpeciesDiffusivity,
    WetCo2SolutionSpeciesDiffusivity,
)
from matintegrity.wet_co2_cylindrical_scale_geometry import (
    WetCo2CylindricalGeometryKnot,
    WetCo2CylindricalScaleGeometryHistory,
    WetCo2CylindricalScalePhase,
    WetCo2ScalePhaseLineInventory,
)
from matintegrity.wet_co2_cylindrical_scale_kinetics_geometry import (
    WetCo2CylindricalScaleKineticsGeometryHandoff,
)
from matintegrity.wet_co2_cylindrical_scale_recession_feedback import (
    WetCo2CylindricalPhaseGrowthCampaign,
    WetCo2CylindricalScaleRecessionFeedback,
)
from matintegrity.wet_co2_cylindrical_shear_limited_scale_removal import (
    WetCo2CylindricalShearLimitedScaleRemoval,
    WetCo2ScaleShearKnot,
)
from matintegrity.wet_co2_cylindrical_spatial_mixed_potential import (
    WetCo2CylindricalSpatialMixedPotential,
    WetCo2SpatialElectrochemicalKnot,
)
from matintegrity.wet_co2_cylindrical_stage_kinetic_scale_feedback import (
    WetCo2CylindricalStageKineticScaleFeedback,
    WetCo2StageActivityKnot,
    WetCo2StageActivityProductTerm,
    WetCo2StageKineticPhase,
)
from matintegrity.wet_co2_cylindrical_stage_speciation_scale_feedback import (
    WetCo2CylindricalStageSpeciationScaleFeedback,
    WetCo2StageSpeciationKineticPhase,
    WetCo2StageSpeciationProductTerm,
)
from matintegrity.wet_co2_cylindrical_steady_hydraulics import (
    WetCo2CylindricalHydraulicKnot,
    WetCo2CylindricalSteadyHydraulics,
)
from matintegrity.wet_co2_cylindrical_transient_transport import (
    WetCo2CylindricalTransientTransport,
    WetCo2ReactionExtentRate,
    WetCo2TransientInitialSpecies,
    WetCo2TransientSpecies,
    WetCo2TransientSpeciesBoundary,
    WetCo2TransientTransportKnot,
    WetCo2TransientWallReaction,
    WetCo2WallElement,
)
from matintegrity.wet_co2_cylindrical_transport_mixed_potential import (
    WetCo2CylindricalElectrodeKnot,
    WetCo2CylindricalSpeciesBoundary,
    WetCo2CylindricalTransportMixedPotential,
)
from matintegrity.wet_co2_cylindrical_wall_saturation_scale_kinetics import (
    WetCo2CylindricalActivityProductTerm,
    WetCo2CylindricalPhaseActivityKnot,
    WetCo2CylindricalWallSaturationScaleKinetics,
)
from matintegrity.wet_co2_data import (
    UnresolvedWetCo2CompilationRow,
    WetCo2LiteratureCrosswalkAudit,
    WetCo2LiteratureEvidenceRow,
    WetCo2LiteratureFieldComparison,
    WetCo2LiteratureFieldMap,
    WetCo2SimulationGridRow,
    WetCo2SimulationGridSummary,
    WetCo2SimulationSourceMatch,
    WetCo2SiObservation,
)
from matintegrity.wet_co2_finite_gas_liquid_exchange_history import (
    WetCo2FiniteGasLiquidHistoryRequest,
    WetCo2FiniteGasLiquidInterval,
)
from matintegrity.wet_co2_finite_gas_variable_liquid_history import (
    WetCo2FiniteGasVariableLiquidHistoryRequest,
    WetCo2FiniteGasVariableLiquidInterval,
)
from matintegrity.wet_co2_finite_gas_water_condensation import (
    FiniteGasWaterCondensationHistoryRequest,
    FiniteGasWaterExchangeInterval,
)
from matintegrity.wet_co2_finite_inventory_electrode_mixed_potential import (
    WetCo2FiniteInventoryElectrodeMixedPotential,
    WetCo2LumpedElectrochemicalExternalExchange,
    WetCo2LumpedElectrochemicalInitialInventory,
    WetCo2LumpedElectrochemicalInterval,
    WetCo2LumpedElectrochemicalReaction,
    WetCo2LumpedElectrochemicalSpecies,
    WetCo2LumpedElectrochemicalVolumeKnot,
)
from matintegrity.wet_co2_finite_inventory_saturation_scale_geometry import (
    WetCo2FiniteInventorySaturationScaleGeometry,
    WetCo2FiniteLiquidWallExchange,
)
from matintegrity.wet_co2_finite_liquid_transfer_history import (
    WetCo2FiniteLiquidTransferHistoryRequest,
    WetCo2FiniteLiquidTransferInterval,
)
from matintegrity.wet_co2_gas_side_mass_transfer import WetCo2GasSideMassTransferRequest
from matintegrity.wet_co2_geometry_fixed_point import WetCo2GeometryFixedPointRequest
from matintegrity.wet_co2_liquid_side_mass_transfer import WetCo2LiquidSideMassTransferRequest
from matintegrity.wet_co2_matched_contrast import WetCo2MatchedContrastRequest
from matintegrity.wet_co2_multispecies_finite_inventory_history import (
    WetCo2FiniteGasMultispeciesHistoryRequest,
    WetCo2SpeciesFluxInterval,
)
from matintegrity.wet_co2_neutral_solid_formula_proposals import (
    WetCo2AqueousIon,
    WetCo2NeutralSolidFormulaProposals,
)
from matintegrity.wet_co2_parallel_zone_transfer import (
    WetCo2ParallelTransferRequest,
    WetCo2ParallelTransferZone,
)
from matintegrity.wet_co2_reactive_film_transfer import WetCo2ReactiveFilmTransferRequest
from matintegrity.wet_co2_scale_corrosion_coupled_history import (
    WetCo2MetalToScaleYield,
    WetCo2MovingScaleInterval,
    WetCo2ScaleCorrosionMovingGeometryHistoryRequest,
)
from matintegrity.wet_co2_scale_corrosion_simultaneous import (
    WetCo2ScaleCorrosionSimultaneousHistoryRequest,
    WetCo2SimultaneousScaleInterval,
)
from matintegrity.wet_co2_scale_diffusion_electrode import (
    ScaleAnodicBranch,
    ScaleCathodicReactantBranch,
    ScaleDiffusionElectrodeKnot,
    WetCo2ScaleDiffusionElectrodeHistory,
)
from matintegrity.wet_co2_simulation_wall_loss_envelope import (
    WetCo2SimulationWallLossEnvelopeRequest,
    WetCo2SimulationWallLossScenario,
)
from matintegrity.wet_co2_transient_carbonate_gas_equilibrium import (
    WetCo2TransientCarbonateHistoryRequest,
    WetCo2TransientCarbonateInterval,
)
from matintegrity.wet_co2_transport_limited_mixed_potential import (
    WetCo2ReactantFilmRecord,
    WetCo2TransportLimitedMixedPotentialRequest,
)
from matintegrity.wet_co2_two_film_transfer import WetCo2TwoFilmTransferRequest
from matintegrity.wet_co2_two_film_transfer_history import (
    WetCo2TwoFilmTransferHistoryRequest,
    WetCo2TwoFilmTransferKnot,
)
from matintegrity.wet_co2_variable_condensate_transfer_history import (
    WetCo2VariableCondensateHistoryRequest,
    WetCo2VariableCondensateInterval,
)
from matintegrity.wet_co2_wall_reaction_coupled_history import (
    Co2starWallConsumptionMapping,
    WetCo2WallReactionCoupledHistoryRequest,
)
from matintegrity.wet_co2_wall_thermal_condensation import (
    LumpedWallCondensationInterval,
    WallWaterSaturationPoint,
    WetCo2LumpedWallThermalCondensationRequest,
)
from matintegrity.zenodo_cocr_wear_corrosion_rows import (
    CoCrCorrosionReadAuthorization,
    CoCrCorrosionWorkbookRow,
    CoCrWorkbookCell,
    CoCrWorkbookManifest,
    CoCrWorksheetManifest,
)
from matintegrity.zenodo_deis_import import (
    DeisAdjacentColumnPairView,
    DeisMatrixMember,
    ZenodoDeisArchiveAuditRequest,
    ZenodoDeisArchiveManifest,
    ZenodoDeisDepositorConditionSummary,
)
from matintegrity.zenodo_deis_typed_rows import (
    ZenodoDeisMatrixAuditRequest,
    ZenodoDeisMatrixRow,
    ZenodoDeisReadAuthorization,
)
from matintegrity.zenodo_zr_alloy_electrochemistry import (
    ZrAlloyReadAuthorization,
    ZrAlloyWorkbookAuditRequest,
    ZrAlloyWorkbookRow,
)

ROOT = Path(__file__).resolve().parents[1]


def contract_schema_filename(contract, name_counts: dict[str, int]) -> str:
    """Avoid overwriting public schemas when distinct modules reuse class names."""
    name = contract.__name__
    if name_counts[name] == 1:
        return f"{name}.json"
    module = contract.__module__.rsplit(".", 1)[-1]
    return f"{module}__{name}.json"


def complete_export_contracts(explicit_contracts, registry):
    """Preserve nested/public contracts and include every registered API input."""
    return tuple(
        dict.fromkeys(
            (*explicit_contracts, *(registry.input_type(model_id) for model_id in registry.list_models()))
        )
    )


def write_schema_index(target, contracts, name_counts, registry):
    """Bind each API to a generated file and digest without inferring validation."""
    records = {}
    for contract in contracts:
        filename = contract_schema_filename(contract, name_counts)
        records[contract] = dict(
            contract_id=f"{contract.__module__}.{contract.__qualname__}",
            filename=filename,
            sha256=hashlib.sha256((target / filename).read_bytes()).hexdigest(),
        )
    models = {model_id: records[registry.input_type(model_id)] for model_id in registry.list_models()}
    index = dict(
        schema_version="matintegrity.public_schema_index.v1",
        meaning="Registered input schema coverage only; not API execution or physical validation.",
        contract_count=len(records),
        registered_model_count=len(models),
        contracts=list(records.values()),
        models=models,
    )
    (target / "schema_index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return index


def main():
    from matintegrity.registry import default_registry

    target = ROOT / "docs/schemas"
    target.mkdir(parents=True, exist_ok=True)
    contracts = (
        PressureLimitBinding,
        PressureLimitReferenceContext,
        ComponentPressureLimit,
        SurfaceProfileRoughness,
        SolutionConcentrationConversion,
        ChemicalCleaningRecord,
        ChemicalCleaningStep,
        CleaningCompatibilityEnvelope,
        CoatingDamageAreaInventory,
        DepositedLayerGeometry,
        DepositionRemovalHistory,
        LayerGeometryEvent,
        CoatingDamagePatch,
        BoltReferenceTorqueScaling,
        BlindIndicatorHoleLigament,
        FrictionResolvedBoltTorque,
        InspectionLotSampling,
        InspectionSamplingPlan,
        InspectionUnitOutcome,
        PipeBendWallAllowance,
        ThicknessRetentionFactor,
        ThicknessSoakDuration,
        EquipmentMassComponent,
        EquipmentMassProperties,
        EquipmentTwoSupportLift,
        TubeExpansionWallReduction,
        TubeBendPreformThickness,
        GoverningThicknessRecipe,
        ThicknessDimension,
        ThicknessExpression,
        FormingOperation,
        InterOperationCoolingPoint,
        FormingTreatmentWaiverBranch,
        FormingSequencePlan,
        FormingProcessSequence,
        SurfaceProfileDeviation,
        SurfaceProfilePoint,
        FormingAreaReduction,
        ImpactMetricCrossings,
        ImpactMetricPoint,
        SteelCompositionIndexRecipe,
        ScaledStrengthCandidate,
        DeclaredImpactSubsizeRequirements,
        ImpactWidthTemperatureReduction,
        ScaledStrengthMinimum,
        PressureTemperatureRampLimits,
        PiecewiseThicknessSoakDuration,
        ThicknessSoakBand,
        ProjectedIndicationInterval,
        IndicationWindowAccumulation,
        HotTapBranchTestPressureCap,
        ThicknessScaledRateLimit,
        ZenerHollomonParameter,
        PlanarStressLinearization,
        ResinHdtHeadroom,
        BrinellSurfaceObservation,
        MatingBrinellHardnessDifference,
        PreheatProcedureTemplate,
        PreheatMeasurementIdentity,
        PreheatMeasurementTrace,
        PreheatMeasurementWindow,
        PreheatHistoryBinding,
        ChemicalAnalysisLimit,
        ChemicalAnalysisObservation,
        ChemicalAnalysisLinearRule,
        ChemicalAnalysisSumRule,
        ChemicalToleranceBranch,
        DeclaredAnalysisToleranceRecipe,
        DeclaredConsumableDepositionRate,
        DeclaredEquipmentEffectiveness,
        DeclaredFluxBasicityRatio,
        DeclaredParetoCategory,
        DeclaredParetoSummary,
        WellMixedGasPurge,
        WellMixedPurgeStage,
        DeclaredChemicalAnalysisComparison,
        FmcElement,
        FmcTimeTrace,
        TfmImagePoint,
        HomogeneousFmcTfm,
        StoredFmcTrace,
        FmcNpyMatrix,
        FileHomogeneousFmcTfm,
        FilePlanarMultiviewFmcTfm,
        PlanarMultiviewFmcTfm,
        PlanarTfmView,
        DeclaredLogSlopeRuptureFactor,
        TemperatureTrendStrengthScaling,
        MeanShearStress,
        DeclaredShellCharacteristicLengths,
        NoSlipPhaseFlow,
        HomogeneousNoSlipMixtureDensity,
        DeclaredInverseSqrtDensityVelocity,
        DevicePressureDropCavitationIndex,
        DeclaredHydrogenSusceptibilityIndex,
        CompositionIndexFactor,
        CompositionIndexTerm,
        CompositionIndexRecipe,
        FlooredCompositionIndexRecipe,
        ComponentMaterialRequirement,
        MaterialClassComponentRecord,
        ComponentMaterialClassAssessment,
        DamageMechanismFact,
        DamageMechanismProfile,
        CompositionSupportRange,
        GrainCountField,
        ServiceCategoryCondition,
        ServiceCategoryFact,
        ServiceCategoryProfile,
        ServiceCategoryRule,
        ClassificationContext,
        ClassificationQuery,
        ClassificationWPSBinding,
        DeclaredClassificationRecord,
        PhasePointCountField,
        PhasePointCountSummary,
        PipingClassAssessment,
        PipingComponentRecord,
        PipingComponentRule,
        ReliefPressureEnvelope,
        SaturationCalorimetryState,
        BoilOffCalorimetry,
        RockwellDepth,
        KnoopIndent,
        AqueousActivitySpecies,
        AqueousStoichiometricTerm,
        AqueousEquilibriumReaction,
        AqueousLinearConstraint,
        AqueousMassActionSystem,
        AqueousMassActionScenario,
        AqueousMassActionScenarioEnvelope,
        AqueousMassActionTopologyCase,
        AqueousMassActionTopologyEnvelope,
        AqueousMassActionSystemAssemblyRequest,
        AqueousMassActionVanTHoffHistory,
        ReactionEnthalpyReference,
        ActivityCoefficientKnot,
        AqueousVanTHoffSaturationHistory,
        AqueousSolubilityKnot,
        TemperatureSupportedCandidate,
        AqueousCandidateNetworkWorkflow,
        AqueousCandidateNetworkSpeciation,
        AqueousReactionCandidateEnumeration,
        AqueousCandidateReactionBindingRequest,
        AqueousCandidateReactionSelection,
        AqueousReactionCandidateSpecies,
        Ti6Al4VCathodicPolarizationImportRequest,
        PitzerSingleSaltActivity,
        ExternalAqueousActivityIteration,
        ExternalAqueousTransportActivity,
        ExternalAqueousActivityHistory,
        AqueousBdotSpeciationHistory,
        AqueousSaturationScreen,
        SaturationScreenSpecies,
        CandidateSolid,
        SaturationScreenTerm,
        BdotSpeciesParameter,
        AqueousBdotIteration,
        AqueousDaviesIteration,
        AqueousSITIteration,
        AqueousExtendedDebyeHuckelIteration,
        ExtendedDebyeHuckelSpeciesParameter,
        Co2HenryTemperatureCorrectionRequest,
        Co2HenryCarbonateAdapterRequest,
        FixedFugacityCarbonateEquilibriumTemplate,
        Co2HenryCarbonateHistoryAdapterRequest,
        EvidenceBoundGasketViscoelasticHistoryRequest,
        EvidenceBoundGasketViscoelasticMaterial,
        ItohMinerCycleBlock,
        ItohNonproportionalMinerBlocks,
        ItohNonproportionalStrainRequest,
        ItohNonproportionalStrainLife,
        GasketMultiBoltSectorEquilibrium,
        CompetitiveSolidDaviesIteration,
        CompetitiveSolidBdotIteration,
        CompetitiveSolidSITIteration,
        AqueousActivityCoefficientPoint,
        AqueousActivityCoefficientTemperatureSlice,
        AqueousSpeciesActivityCurve,
        AqueousTabulatedActivityIteration,
        KineticAqueousSpecies,
        KineticAqueousSpeciesDefinition,
        KineticSolidPhase,
        KineticSolidReaction,
        CompetingSolidKineticInterval,
        CompetingSolidKineticLedger,
        CompetingSolidSaturationInterval,
        CompetingSolidSaturationKinetics,
        SolidSaturationRateLaw,
        CellwiseCompetingSolidRateInterval,
        CompetingSolidKineticTransport,
        CompetitiveSolidEquilibriumTransport,
        FlangeContactFieldRequest,
        FlangeComplianceReductionRequest,
        FlangeComplianceReductionHistoryRequest,
        SurfaceScaleKineticInterval,
        CallerSurfaceScaleKinetics,
        CallerScaleCoverageKinetics,
        LayeredScaleDiffusionLimit,
        ScaleTransportLayer,
        ScaleLayerHistoryBinding,
        LayeredScaleHistoryStackTransport,
        LayeredScaleHistorySeriesTransport,
        ScaleLimitedSurfaceFlux,
        ScaleHistoryTransportLink,
        ScaleHistoryTransportSeriesLink,
        ScaleLimitedElectrochemicalHistory,
        ScaleLimitedElectrochemicalHistorySegment,
        CreviceGeometryTransportCampaign,
        CreviceTransportRecessionFeedback,
        CreviceRateSupport,
        CreviceSpecies,
        CreviceSpeciesInventoryHistory,
        CreviceSpeciesRateInterval,
        CreviceNernstProfile,
        CreviceWallShearExposure,
        NernstDrivenButlerVolmerHistory,
        CreviceMixedPotentialReaction,
        CreviceMixedPotentialHistory,
        CreviceElectrochemicalInventoryIntegration,
        CreviceLumpedExchangeReactionHistory,
        CreviceAqueousKineticNetwork,
        CreviceKineticInterval,
        CreviceKineticReaction,
        CreviceKineticSpecies,
        CreviceKineticTerm,
        CreviceApertureHistoryRefinement,
        ElementalComponent,
        WetCO2PhaseHistoryHandoff,
        ElectrochemicalMetalLossHistory,
        MetalDissolutionReactionMapping,
        ElectrochemicalWallThicknessHistory,
        ElectrochemicalWallThicknessScenario,
        ElectrochemicalWallThicknessScenarioEnvelope,
        ElectrochemicalCreviceGeometryHistory,
        ReactionCellVolumeAllocation,
        ExternalCreviceSolverHistory,
        ChemistryBoundaryStage,
        SpeciesHandoff,
        ChemistryBoundaryLink,
        ElectrochemicalChemistryBoundaryAudit,
        SpeciesComposition,
        StoichiometricTransferTerm,
        SpeciesTransferRule,
        ExcludedSpecies,
        Wco2SpeciesTransferAuditRequest,
        CreviceElectrolyteVolumeKnot,
        CreviceInitialSpeciesInventory,
        CreviceElectrochemicalCompositionHistory,
        CreviceCompositionToMassActionHistory,
        AqueousMassActionToNernstHistory,
        CT110ProviderFile,
        CT110Source,
        CT110WeldCorrosionObservation,
        CT110WeldCorrosionDataset,
        Co2HenrySolubilityRecord,
        CoolPropCo2FugacityRequest,
        CoolPropCo2MixtureFugacityRequest,
        MixtureCo2FugacityHistory,
        PureCo2FugacityHistory,
        FixedFugacityCarbonateScenario,
        FixedFugacityCarbonateEnsemble,
        FixedFugacityCarbonateEquilibrium,
        FixedFugacityCarbonateHistory,
        MaterialCorrosionRateContrast,
        CouponLoss,
        FaradayLoss,
        CouponLossWithUncertainty,
        CorrosionRateObservation,
        CorrosionRateSampleSummary,
        CorrosionRateJointScenario,
        CorrosionRateModelOutputWallLossScenario,
        CorrosionRateProjectionRow,
        SimulationRateWallLossScenario,
        CorrosionRateQuantileForecast,
        UnresolvedWetCo2CompilationRow,
        WetCo2SimulationGridRow,
        WetCo2SimulationGridSummary,
        AquaSolDBCo2SolubilityObservation,
        AquaSolDBCo2SolubilityQuery,
        AquaSolDBFixedFugacityComparisonInput,
        WetCo2LiteratureEvidenceRow,
        WetCo2LiteratureFieldMap,
        WetCo2LiteratureFieldComparison,
        WetCo2LiteratureCrosswalkAudit,
        WetCo2SimulationSourceMatch,
        WetCo2SiObservation,
        AtmosphericCorrosionObservation,
        AtmosphericFirstYearFitRow,
        AtmosphericFirstYearModel,
        AtmosphericFirstYearFit,
        AtmosphericFirstYearPrediction,
        AtmosphericScenario,
        AtmosphericScenarioEnsemble,
        BurstPressureComparison,
        BurstPressureComparisonRow,
        TabulatedCrackGrowthCurve,
        TabulatedGrowthRateQuery,
        FcgrCsvImportRequest,
        FcgrCsvImportResult,
        FcgrImportedRow,
        FcgrWorkbookSheetSelection,
        FcgrWorkbookImportRequest,
        FcgrWorkbookImportedPoint,
        FcgrWorkbookCurveResult,
        FcgrWorkbookImportResult,
        TabulatedGrowthLoadBlock,
        TabulatedCrackGrowth,
        TabulatedCrackGrowthCurveFamily,
        TabulatedCurveFamilyGrowth,
        CrackGrowthUncertaintySample,
        CrackGrowthUncertaintyDesignLevel,
        CrackGrowthScenario,
        CrackGrowthScenarioManifestRow,
        CrackGrowthScenarioEvaluation,
        TabulatedCrackGrowthUncertainty,
        TabulatedCrackGrowthUncertaintyConvergence,
        TabulatedCrackGrowthScenarioEnsemble,
        TabulatedCrackGrowthScenarioReduction,
        PolarizationCurve,
        ChronoamperometryWindowSummary,
        PolarizedElectrode,
        MixedPotential,
        MixedPotentialEquilibrium,
        FailureAssessmentCurve,
        FailureAssessmentPoint,
        FailureAssessment,
        FADHistoryProviderReceipt,
        FADAssessmentHistoryKnot,
        FADAssessmentHistoryRequest,
        FADFaultTreeProbabilityInput,
        FADFaultTreeBindingRequest,
        FADFaultTreeEventBinding,
        ComponentTotalInventory,
        CreviceComponentSolidPartitionRequest,
        CyclicResponseSeries,
        CyclicResponseRelativeError,
        FatigueLifeRmsle,
        DynamicModulusDropEndpoint,
        PressureTemperatureEnvelopeKnot,
        PressureTemperatureOperatingPoint,
        PressureTemperatureEnvelope,
        SobolRequest,
        SobolDesign,
        SobolInputBatch,
        SobolEvaluations,
        WaveformEnergy,
        MeasuredWeldEnergy,
        MeasuredPipeOvality,
        PipeMembraneTestPressure,
        ReferenceEnergyMass,
        CorrelationBasis,
        CarbonIndexTerm,
        CarbonIndexResponse,
        CarbonEquivalentRecipe,
        PipingDisplacementAllowance,
        WeldCoolingCorrelation,
        FluxMoistureHydrogen,
        CouplingPressure,
        ThreadConnectionPressure,
        WeldPowerTravel,
        WaveformEnergyUncertainty,
        TubePressureKnot,
        TubePressureStressHistory,
        TubeBundleLameStressHistory,
        SobolReport,
        RegistrySensitivityConfiguration,
        TabularExportProvenance,
        HydrogenPermeationSignalCalibration,
        HydrogenTdsSignalCalibration,
        HydrogenKineticTrap,
        HydrogenSlabFlowMultiplierFit,
        FaultTreeAssessment,
        FaultTreeBasicEvent,
        LatticeBoundary,
        HydrogenSlab,
        HydrogenFiniteCylinder,
        HydrogenTrapThermalRates,
        ThermallyActivatedFrequency,
        HydrogenDissociativeSurfaceRates,
        ThermallyActivatedSurfaceFlux,
        HydrogenDetectorObservation,
        HydrogenTrapPopulation,
        HydrogenThermalRateFit,
        GuidedWavePairFeatures,
        GuidedWaveReferenceEnsemble,
        RiskCostComponent,
        InspectionActionRiskCandidate,
        InspectionActionExpectedLossComparison,
        InspectionDispositionOutcomeBranch,
        InspectionDispositionDecisionTree,
        PolicyStageCostComponent,
        InspectionPolicyStage,
        InspectionPolicyPath,
        MultiPeriodInspectionPolicyEvaluation,
        FinitePolicyState,
        InitialPolicyStateProbability,
        FinitePolicyObservationProbability,
        FinitePolicyDecisionRule,
        FinitePolicyAction,
        FinitePolicyTransitionProbability,
        FinitePolicyDecisionEpoch,
        FiniteInspectionPolicyPathGeneration,
        PolicyObservationLabel,
        PolicyCalibrationAction,
        PolicyObservationCalibrationRecord,
        PolicyTransitionCalibrationRecord,
        FinitePolicyProbabilityCalibration,
        PolicyResourceUsage,
        MultiPeriodInspectionPolicyCandidate,
        PolicyResourceConstraint,
        MultiPeriodInspectionPolicyComparison,
        InspectionForecastPoint,
        ThresholdInspectionSchedule,
        PulseEchoCalibrationObservation,
        PulseEchoSoundSpeedFit,
        VisualExaminationArea,
        VisualSurfaceIndication,
        VisualSurfaceExamination,
        SurfaceExaminationArea,
        SurfaceIndication,
        LiquidPenetrantExamination,
        MagnetizationPass,
        MagneticParticleExamination,
        RadiographicImageIndication,
        RadiographicImageQualityRecord,
        RadiographicExamination,
        PhasedArrayProbe,
        PhasedArrayWedge,
        PhasedArrayBeamLaw,
        EncodedPhasedArrayFrame,
        PhasedArrayIndication,
        PhasedArrayExamination,
        MlNdtFlawMetadata,
        MlNdtImageLabel,
        MlNdtBatchAudit,
        TofdProbePair,
        EncodedTofdFrame,
        TofdDiffractionPick,
        TofdIndication,
        TofdExamination,
        EddyCurrentProbe,
        EddyCurrentReferenceFeature,
        EddyCurrentReferenceStandard,
        EncodedEddyCurrentScan,
        EddyCurrentIndication,
        EddyCurrentExamination,
        EddyCurrentDicondeRecord,
        FabestLcfMemberAudit,
        FabestLcfTableAudit,
        FabestLcfExperimentAudit,
        FabestLcfArchiveAudit,
        NumericMatVariableRecord,
        LocalPittingMatRecord,
        SeccmArchiveMemberRecord,
        SeccmArchiveAudit,
        SeccmChronoamperometryTrace,
        RectilinearFieldMetadata,
        PlanarAffineCoordinateTransform,
        RectilinearFieldSamplingRequest,
        RectilinearFieldSamplingResult,
        PipelineIliFeature,
        PipelineIliWorkbookAudit,
        EscapeLeakTraceRecord,
        EscapeLeakDatasetAudit,
        PressureDecayLeakSeriesRecord,
        PressureDecayLeakReadAuthorization,
        PressureDecayLeakArchiveAuditRequest,
        PressureDecayLeakSample,
        PressureDecayLeakDatasetAudit,
        CathodicProtectionCurveRecord,
        CathodicProtectionDatasetAudit,
        CathodicProtectionReadAuthorization,
        CathodicProtectionArchiveAuditRequest,
        CathodicProtectionSample,
        FindleyLifeCycleBlock,
        FindleyMinerHistoryRequest,
        CreviceTransportCompositionBridge,
        WetCo2SimulationWallLossScenario,
        WetCo2SimulationWallLossEnvelopeRequest,
        ElasticJointLoadKnot,
        ElasticJointLoadHistoryRequest,
        CreviceCellSpeciationRecord,
        CreviceSpeciationKnot,
        CreviceLocalSpeciationLedgerRequest,
        CreviceMassActionProjectionCell,
        CreviceMassActionProjectionKnot,
        CreviceLocalMassActionProjectionRequest,
        CreviceLocalExternalActivityProjectionRequest,
        CorrosionRateHistoryKnot,
        CorrosionRateThicknessHistoryRequest,
        CorrosionFaultTreeBindingRequest,
        CorrosionFaultTreeEventBinding,
        CorrosionFaultTreeProbabilityInput,
        CreviceFaradaicFaultTreeBindingRequest,
        CreviceFaradaicFaultTreeEventBinding,
        CreviceFaradaicFaultTreeProbabilityInput,
        GalvanizedPolarizationReadAuthorization,
        GalvanizedPolarizationArchiveAuditRequest,
        GalvanizedPolarizationSample,
        GasketLeakageRateThresholdEvents,
        CoatingAdhesionGroupRecord,
        CoatingAdhesionDatasetAudit,
        AEWaveformRecord,
        AECoordinateRecord,
        ControlledAEDatasetAudit,
        TribologyMetadataFileAudit,
        TribologyMetadataDatasetAudit,
        HydrogenFatigueSeries,
        HydrogenFatigueGrowthPoint,
        HydrogenFatigueWorkbookAudit,
        MflMagnetizer,
        MflSensorArray,
        MflReferenceFeature,
        MflReferenceStandard,
        MflMagneticFieldCheckpoint,
        EncodedMflScan,
        MflIndication,
        MflExamination,
        PulseEchoThicknessCalibration,
        CreepLifeModel,
        ReferenceCapacity,
        BulgingFactorTable,
        ProfileCapacityCorrosionScenario,
        ProfileCapacityRateFieldScenario,
        MaterialDesignation,
        DesignationAlias,
        ChemistryRecord,
        ChemistryRequirements,
        CreepFatigueInteractionEnvelope,
        CreepFatigueInteractionPoint,
        CreepFatigueInteractionResult,
        StrainLifeBlock,
        StrainLifeCampaign,
        StrainLifeBlockResult,
        StrainLifeCampaignResult,
        CreepHistoryInterval,
        CreepHistoryRequest,
        CreepHistoryResult,
        CreepFatigueCampaign,
        CreepFatigueCampaignResult,
        TangentExpansionTable,
        ThermalExpansionResult,
        ThermalStressPropertyEvidence,
        ThroughWallThermalStress,
        SubsetReplicateRequest,
        SubsetReplicateResult,
        SubsetReplicateTask,
        SubsetReplicateTaskResult,
        FadEnvelope,
        FadPoint,
        TubeLayout,
        TubeCondition,
        ElasticJointLoad,
        InsulationSurfaceRequest,
        CalibratedDamageInterval,
        CalibratedDamageHistory,
        CriticalPlaneSwtLife,
        CriticalPlaneFsLife,
        ContinuousPlaneFsLifeBound,
        CriticalPlaneCyclePair,
        CriticalPlaneCyclePairDamage,
        CriticalPlaneIntervalOverlapPairing,
        ClosedTensorCycle,
        ClosedTensorWorkLife,
        CallerMultiaxialDamageRequest,
        CallerStatefulMultiaxialDamageRequest,
        MultiaxialFatigueLawProfile,
        OrderedTensorCycleBlock,
        MultiaxialCycleBlockReceipt,
        CriticalPlaneContinuousBound,
        CriticalPlaneProjectedRainflow,
        CriticalPlanePiecewiseLinearTimeHistory,
        RestrictedTransportRequest,
        FireThermalResponse,
        ButlerVolmerReaction,
        MassActionReaction,
        MassActionNetwork,
        ElectrochemicalTransport,
        ConcentrationKineticLaw,
        SequenceCrackGrowth,
        SequenceGrowthState,
        PartialMetalDissolutionHistory,
        DissolutionSelection,
        NetMetalBoundarySelection,
        CarbonateReactionConstants,
        CarbonateBoundarySelection,
        CarbonateTransportBoundary,
        ElectrolyteSpecies,
        Co2CorrosionCampaign,
        EquilibriumReactiveTransport,
        PrecipitatingAqueousSpecies,
        SingleSolidEquilibrium,
        CompetitiveAqueousSpecies,
        CompetitiveSolidPhase,
        CompetitiveSolidEquilibrium,
        LossRateFeature,
        LogRateInteraction,
        CalibratedConditionLossLaw,
        LossCondition,
        ConditionLossRateAssessment,
        ConditionLossInterval,
        ConditionLossHistory,
        PlanarSlitGeometry,
        PlanarSlitApertureHistory,
        PlanarSlitEndpointVelocityPath,
        PlanarSlitHydraulicFlow,
        PlanarSlitHydraulicHistory,
        PlanarSlitTransientHydraulicHistory,
        CreviceHydraulicStageRHSRequest,
        FixedKineticCell,
        CreviceCellwiseNucleationKineticHistoryRequest,
        CreviceBDFNucleationOperatorSplitRequest,
        HydraulicFlowObservationRun,
        CreviceHydraulicParameterFitRequest,
        GasketCompressionPoint,
        ProvenanceWeldConstituent,
        WeldDilutionUncertainty,
        BoltForceChangePoint,
        NonlinearBoltGasketJoint,
        NonlinearGasketJoint,
        GasketPronyBranch,
        GasketViscoelasticMaterial,
        GasketViscoelasticJointHistoryRequest,
        GasketViscoelasticHistoryRequest,
        GasketBackbonePoint,
        NonlinearGasketMaxwellBranch,
        NonlinearGasketViscoelasticMaterial,
        NonlinearGasketViscoelasticJointHistoryRequest,
        FlangeNonlinearContactFieldRequest,
        FlangePronyBranch,
        FlangeViscoelasticContactHistoryRequest,
        RosenthalPointSource3D,
        RosenthalCoolingIntervalLink,
        CoolingInterval,
        CoolingIntervalBranch,
        CoolingIntervalBatch,
        CoolingIntervalSensorBatch,
        CoolingIntervalSensorBranch,
        CoolingIntervalSensorTrace,
        FlangeNonlinearViscoelasticContactHistory,
        GasketLeakageCalibrationRow,
        GasketLeakageCalibrationMap,
        GasketLeakageMapFit,
        GasketLeakageFitObservation,
        GasketLeakageFitDiagnostics,
        GasketContactStateGridSweep,
        ExternalContactStateGridQuery,
        ExternalContactStateGridResponse,
        GasketLeakageHistory,
        GasketLeakageNodePressureEnvelope,
        GasketLeakageRateEnvelope,
        PlanarScaleDiffusionReactionHistory,
        ScaleDiffusionReactionInterval,
        ScaleReactionDemandInterval,
        PlanarScaleReactionDemandBalance,
        ExternalFlangeComplianceBinding,
        GasketLeakageCorrelatedScenario,
        GasketLeakageCorrelatedScenarioEnvelope,
        GasketLeakageWeightedScenarioMoments,
        GasketContactPressureScreen,
        GasketContactPressureWindowEvents,
        GasketLeakageBoxNode,
        GasketLeakageBoxEnvelope,
        GasketLeakageScenarioExposure,
        GasketFiniteScenarioDependence,
        GasketLeakageScenarioRateInterval,
        UnilateralNonlinearGasketJointHistoryRequest,
        ShearNormalLifeCurvePoint,
        ShearNormalStrainLifeCalibration,
        KandilBrownMillerLifeCalibration,
        CriticalPlaneFindleyStressHistory,
        FindleyParameterLifePoint,
        CriticalPlaneFindleyCalibratedLife,
        FsLifeCalibration,
        SwtLifeCalibration,
        MultiaxialLifeCampaign,
        MultiaxialLifeScenario,
        MultiaxialLifeScenarioEnvelope,
        MultiaxialWeightedLifeScenarioMoments,
        InceGlinkaGSACalculation,
        ScaleReactantIntervalSupply,
        ScaleLimitingReactantInventory,
        ScalePrecipitationInventoryBudget,
        ScaleLimitedMetalDissolutionPathway,
        ScaleDiffusionMetalLossBound,
        GSALifeCurvePoint,
        InceGlinkaGSACurveLife,
        AdaptiveCycleBlockDamageRequest,
        CycleBlockLawParameter,
        IntegerCycleDamageBlock,
        DeisMatrixMember,
        ZenodoDeisArchiveAuditRequest,
        ZenodoDeisArchiveManifest,
        DeisAdjacentColumnPairView,
        ZenodoDeisDepositorConditionSummary,
        Ti12Mo5HfProviderCondition,
        Ti12Mo5HfArchiveAudit,
        Ti12Mo5HfArchiveAuditRequest,
        Ti12Mo5HfAESECRequest,
        Ti12Mo5HfAESECProvenance,
        Ti12Mo5HfAESECRow,
        Ti12Mo5ZrWorkbookRequest,
        Ti12Mo5ZrWorkbookProvenance,
        Ti12Mo5ZrRawRow,
        AqueousSolidPhaseCandidateEnumeration,
        SaturationHistoryKnot,
        SaturationHistoryEventRequest,
        SaturationHistoryAssessmentBinding,
        Ti12Mo5ZrMassBalanceRequest,
        Ti12Mo5ZrPenetrationPoint,
        Ti12Mo5ZrMassBalanceResult,
        RemainingThicknessRequest,
        RemainingThicknessKnot,
        RemainingThicknessHistory,
        Ti12Mo5ZrComplexEISRequest,
        Ti12Mo5ZrComplexEISPoint,
        Ti12Mo5ZrOCPWindowRequest,
        FlangeDiagnosticCriterion,
        ExternalFlangeDiagnosticScreenRequest,
        CycleBlockResultSummaryRequest,
        SampledStressInvariantHistory,
        CreviceSteadyWallSinkRequest,
        PitzerSaltFiniteScenarioEnvelope,
        PitzerSaltSaturationIndex,
        CreviceTransientWallSinkRequest,
        MultiaxialTensorWorkCycle,
        GasketContactTransitionBrackets,
        GasketContactTransitionRefinement,
        ExternalContactStateQuery,
        ExternalContactStateResponse,
        ElectrochemicalWallFluxScheduleRequest,
        MetroPT3ArchiveAuthorization,
        MetroPT3ArchiveAuditRequest,
        MetroPT3Row,
        SpatialReactionInterval,
        SpatialMassActionReaction,
        SpatialPiecewiseMassAction,
        WetCo2MatchedContrastRequest,
        FiniteCyclePlane,
        CycleBlockFeatureBinding,
        TensorCycleBlockFeatureInput,
        CycleBlockFeatureHandoffRequest,
        FadEnvelopeAssessment,
        TubeBundleInventory,
        AssessmentResult,
        EventProbability,
        Evidence,
        RunContext,
        OperatingHistory,
        Co2MixtureFugacityHistory,
        PSADynaMeanStreamFugacityRow,
        PSADynaMeanStreamFugacityBatch,
        LocalTensorHistory,
        ActionEventProbabilityEvaluation,
        FaultTreeActionEventInput,
        FaultTreeActionResultLineage,
        FaultTreeInspectionRiskCampaignReport,
        MonitoringAssessmentRecord,
        HydrogenTransportHistory,
        HumanReliabilityEstimateRecord,
        PipelineAssessmentRecord,
        HelprLifeCriteriaRecord,
        CavitationHistory,
        JointEventDistribution,
        GaussianMeanShiftImportanceSampling,
        MorrowStrainLife,
        SWTStrainLife,
        SubsetSimulationRequest,
        SubsetSimulationLevel,
        SubsetSimulationResult,
        ContinuousTimeMarkovChain,
        PiecewiseContinuousTimeMarkovChain,
        ThicknessObservation,
        BayesianLinearThicknessUpdate,
        LinearThicknessStateSpaceUpdate,
        GaussianThicknessPosteriorSampleDesign,
        LinearThicknessFirstPassageSample,
        SampledLinearThicknessFirstPassage,
        MaterialRecord,
        FlawRecord,
        InspectionRecord,
        WeldProcedureRecord,
        HeatTreatmentRecord,
        PropertyQuery,
        DesignPropertyTable,
        ParameterProfile,
        WorkflowStep,
        ThermoRequest,
        Rule,
        SatisfactionGate,
        HydrogenBakeoutSlab,
        Api581WallFlawMaterialState,
        Api581InspectionLineage,
        Api581DamageExchangeRecord,
        CompositionComponent,
        ProcessStateBasis,
        IntegrityEventBasis,
        ReleaseScenarioBasis,
        RequestedConsequenceModel,
        ConsequenceScenarioHandoff,
        ConsequenceQuantity,
        ConsequenceStageResult,
        ConsequenceScenarioResultRecord,
        ExchangeEndpoint,
        ExchangeCompatibilityCheck,
        ExchangeFieldDecision,
        ExchangeCompatibilityReceipt,
        PinnedPofMethodSelectionRequest,
        PinnedProviderEvidence,
        PinnedExternalSourceTerm,
        PinnedProviderRequestOptions,
        PinnedProviderRequestEnvelope,
        ExternalSchemaAuditRecord,
        Api581PinnedSchemaValidationReport,
        PinnedSchemaValidationIssue,
        PinnedProviderRequestValidationReport,
        PinnedSchemaPathFinding,
        PinnedSchemaValidationReport,
        SpecificationDesignation,
        SpecificationAlias,
        SpecificationProfile,
        SpecificationAliasResolution,
        CertificateUnitRule,
        CertificateRequirement,
        CertificateMeasurementRecord,
        MaterialCertificateEvidence,
        CertificateReconciliationInput,
        ReconciledEvidenceRow,
        CertificateReconciliationReport,
        SCCScreeningFact,
        SCCRuleCondition,
        SCCScreeningRule,
        SCCMechanismProfile,
        UserDefinedSCCScreening,
        SurfaceInspectionProcedure,
        ExaminedSurfaceRegion,
        ProfileSurfaceIndication,
        CallerIndicationGroup,
        NumericAcceptanceRule,
        ProhibitedClassRule,
        CallerAcceptanceProfile,
        SurfaceIndicationAssessment,
        AcceptanceRuleEvaluation,
        SurfaceIndicationAssessmentResult,
        PODCampaignObservation,
        PODCampaignRequirementProfile,
        PODCampaignAuditRequest,
        PODCampaignFinding,
        PODCampaignAuditReport,
        CapacitySurfaceAxis,
        RemainingStrengthSurface,
        FlawGeometrySample,
        CallerStrengthCriterion,
        RemainingStrengthEvaluationInput,
        InterpolatedStrengthSample,
        RemainingStrengthEvaluationReport,
        CompatibilityFact,
        CompatibilityMaterial,
        CompatibilityLayer,
        CompatibilityServiceEnvironment,
        NumericEnvelopeRule,
        IdentityEnvelopeRule,
        CallerWeldCompatibilityProfile,
        WeldCompatibilityAssessment,
        CompatibilityRuleFinding,
        WeldCompatibilityAssessmentResult,
        LeakCampaignStateIdentity,
        ReferenceLeakCampaignPoint,
        BlankBackgroundObservation,
        DetectionCapabilityEvidence,
        LeakCampaignQualityCriterion,
        LeakCampaignAcceptanceProfile,
        LeakTestCampaignQualityAssessment,
        StructuralMeshReceipt,
        StructuralResultFieldReceipt,
        StructuralDiagnosticEvidence,
        StructuralProviderResultReceipt,
        RequiredStructuralField,
        StructuralDiagnosticCriterion,
        StructuralAcceptanceProfile,
        StructuralAcceptanceFinding,
        StructuralAcceptanceReport,
        AssemblyBoltPreload,
        FlangeFaceAlignmentObservation,
        GasketAssemblyMeasurement,
        JointThermalPressureCycle,
        JointLeakageObservation,
        CallerGasketCompressionRecoveryEnvelope,
        CallerBoltedJointProfile,
        BoltedJointAssemblyAssessment,
        JointAssemblyRuleFinding,
        BoltedJointAssemblyAssessmentResult,
        ImagingReferenceFeature,
        ImagingReferenceStandard,
        ImagingReferenceVerification,
        ImagingAcquisitionEvidence,
        ImagingQualityCriterion,
        ImagingCampaignAcceptanceProfile,
        ImagingCampaignQualityAssessment,
        ImagingCampaignQualityReport,
        CcpsNativePlumeSettings,
        CcpsNativePlumeProviderReport,
        ElectrodeMaterialCouple,
        LocalEnvironmentFact,
        LocalEnvironmentExposureState,
        LocalEnvironmentHistoryCriterion,
        LocalEnvironmentHistoryAssessment,
        LocalEnvironmentFinding,
        LocalEnvironmentHistoryReport,
        MaterialStateIdentity,
        MediaComponentConcentration,
        MaterialExposureInterval,
        MaterialPropertyObservation,
        CallerEnvironmentEnvelope,
        PropertyEnvelopePoint,
        CallerPropertyRule,
        CallerMaterialStateProfile,
        MultiEnvironmentMaterialAssessment,
        MaterialProfileFinding,
        MultiEnvironmentMaterialAssessmentResult,
        ElectromagneticReferenceFeature,
        ElectromagneticReferenceStandard,
        ElectromagneticAcquisitionConfiguration,
        ElectromagneticReferenceCheck,
        EncodedElectromagneticScanEvidence,
        ElectromagneticQualityCriterion,
        ElectromagneticCampaignAcceptanceProfile,
        ElectromagneticCampaignQualityAssessment,
        ElectromagneticCampaignQualityReport,
        Api581NumericFrequencySettings,
        Api581NumericFrequencyReport,
        HighTemperatureExposureInterval,
        HighTemperatureMeasurementEvidence,
        HighTemperatureMeasurementCriterion,
        HighTemperatureCallerProfile,
        HighTemperatureHistoryAssessment,
        HighTemperatureFinding,
        HighTemperatureHistoryReport,
        CoatingQualityMeasurement,
        CoatingCureHeatInterval,
        CallerCoatingMetricRule,
        CallerCoatingCampaignProfile,
        CoatingCampaignAssessment,
        CoatingCampaignFinding,
        CoatingCampaignAssessmentResult,
        WaveArrayElement,
        WaveAcquisitionConfiguration,
        WaveReferenceSourceCheck,
        WaveAcquisitionRecord,
        WaveQualityCriterion,
        WaveCampaignAcceptanceProfile,
        WaveCampaignQualityAssessment,
        WaveCampaignQualityReport,
        WallThicknessReplicate,
        WallToleranceCallerProfile,
        WallToleranceAssessment,
        WallToleranceReplicateFinding,
        WallToleranceReport,
        OverlayDepositionPass,
        OverlayMeasurement,
        OverlayHeatInterval,
        CallerOverlayCriterion,
        CallerOverlayProfile,
        OverlayCladdingCampaign,
        OverlayFinding,
        OverlayCladdingCampaignResult,
        FractureSpecimenGeometry,
        FatiguePrecrackEvidence,
        CallerValidityFlag,
        FractureToughnessSpecimenRecord,
        FractureToughnessCriterion,
        FractureToughnessCallerProfile,
        FractureToughnessCampaignAssessment,
        FractureToughnessCampaignReport,
        ProductionJointRecord,
        ProductionCycleInterval,
        ProductionJointMeasurement,
        CallerProductionCriterion,
        CallerBrazingBondingProfile,
        BrazingBondingProductionCampaign,
        CampaignFinding,
        BrazingBondingCampaignResult,
        ImpactSpecimenIdentity,
        ImpactMachineConfiguration,
        ImpactReportedResult,
        ImpactTestRecord,
        ImpactMetricCriterion,
        ImpactCampaignCallerProfile,
        ImpactTestingCampaign,
        HandlingObservation,
        OrderedHandlingEvent,
        TemporarySupportEvidence,
        ErectionMeasurement,
        TransportErectionCriterion,
        TransportErectionCallerProfile,
        TransportErectionCampaignAssessment,
        TransportErectionCampaignReport,
        HardnessTestSubject,
        HardnessTestConfiguration,
        HardnessReferenceBlockEvidence,
        HardnessReading,
        HardnessCampaignCallerProfile,
        HardnessTestingCampaign,
        ProductionWeldIdentity,
        WeldCouponSpecimen,
        WeldTestMeasurement,
        CallerWeldTestCriterion,
        CallerProductionWeldTestProfile,
        ProductionWeldTestCampaign,
        WeldTestFinding,
        ProductionWeldTestCampaignResult,
        TabularFieldMapping,
        TabularImportProfile,
        TabularRowFinding,
        TabularImportReport,
        ManufacturingHeatTreatment,
        ManufacturedProductEvidence,
        ProductSampleEvidence,
        ProductQualityObservation,
        CastingForgingQualityCriterion,
        CastingForgingCallerProfile,
        CastingForgingQualityCampaignAssessment,
        CastingForgingQualityCampaignReport,
        PreparationEvent,
        CleanlinessMeasurement,
        CleanlinessCriterion,
        CallerCleanlinessProfile,
        SurfaceCleanlinessCampaign,
        SurfaceCleanlinessFinding,
        SurfaceCleanlinessResult,
        TensileSpecimenIdentity,
        TensileMachineConfiguration,
        TensileReportedResult,
        TensileTestRecord,
        TensileMetricCriterion,
        TensileCampaignCallerProfile,
        TensileOffsetYieldCampaign,
        BondedAssemblyGeometry,
        BondProcessEvent,
        BondedAssemblyEvidence,
        BondedLayerSample,
        BondedLayerObservation,
        BondedLayerCriterion,
        BondedLayerCallerProfile,
        BondedLayerIntegrityCampaignAssessment,
        BondedLayerIntegrityCampaignReport,
        ChemicalComponent,
        ChemicalBatch,
        CleaningEvent,
        CleaningMeasurement,
        WasteDisposition,
        ChemicalCleaningCriterion,
        ChemicalCleaningProfile,
        ChemicalCleaningCampaign,
        ChemicalCleaningResult,
        ChemicalCleaningBathHistory,
        GasketNominalContactPressureRequest,
        LH2DTNodeStateHistory,
        LH2DTNodeThermoPoint,
        WangBrownReviewedExcursionParameter,
        CMSX6LISReadAuthorization,
        CMSX6LISColumnValue,
        CMSX6LISTypedRow,
        CMSX6LISReadRequest,
        ExtendedDebyeHuckelSpecies,
        ExtendedDebyeHuckelActivityInput,
        ReplicaServiceInterval,
        ReplicaAcquisitionConfiguration,
        ReplicaCampaignObservation,
        ReplicaCampaignField,
        ReplicaObservationCriterion,
        ReplicaCampaignCallerProfile,
        ReplicaMetallographyCampaign,
        WeldHardnessSubject,
        WeldHardnessTestConfiguration,
        WeldHardnessPoint,
        WeldHardnessTraverse,
        HardnessRegionCriterion,
        WeldHardnessCallerProfile,
        WeldHardnessMappingCampaignAssessment,
        WeldHardnessMappingCampaignReport,
        RepairIdentity,
        ExcavationEvidence,
        RepairEvent,
        RepairObservation,
        RepairWeldingCriterion,
        RepairWeldingProfile,
        RepairWeldingCampaign,
        RepairWeldingResult,
        PreservationSystemIdentity,
        PreservationCampaignFact,
        StoragePreservationEvent,
        PreservationFactCriterion,
        StoragePreservationCallerProfile,
        StoragePreservationCampaign,
        TestWaterCircuitIdentity,
        TestWaterHistoryEvent,
        TestWaterAnalyticalResult,
        TestWaterSample,
        TestWaterCriterion,
        TestWaterCallerProfile,
        TestWaterQualityCampaignAssessment,
        TestWaterQualityCampaignReport,
        CertificateCoverageRecord,
        CertificateCampaign,
        SpecificationAliasQuery,
        SpecificationProfileMaterialBinding,
        SpecificationAliasProfileSetAudit,
        CUIScopeIdentity,
        CUIAccessInspectionRepairEvent,
        CUIAccessCoverageRegion,
        CUIObservation,
        CUICampaignCriterion,
        CUICallerProfile,
        UnderInsulationCampaignAssessment,
        UnderInsulationCampaignReport,
        CUIEvidenceReceipt,
        NistCorrDataArchiveAudit,
        AllowablePropertyTableRecord,
        AllowablePropertyQueryRecord,
        AllowablePropertyProviderAudit,
        GalvanicEnvironment,
        PartialDissolutionObservation,
        GalvanicElectrodeEvidence,
        ElectricalConnection,
        GalvanicCouplingAssessment,
        ResistanceComponent,
        ResistiveGalvanicConnection,
        ResistiveGalvanicCoupling,
        ExternalPressureConvergenceEvidence,
        ExternalPressureReceiptCriterion,
        ExternalPressureCampaignCallerProfile,
        ExternalPressureCampaignAssessment,
        ExternalPressureCampaignReport,
        RectilinearThicknessMap,
        CarbonateActivityConstants,
        CarbonateAlkalinitySpeciation,
        DaviesActivityCoefficientInput,
        DaviesActivitySpecies,
        SITActivityCoefficientInput,
        SITInteraction,
        SITSpecies,
        OttoElectrolyteObservation,
        ResidualStressProviderQualification,
        DeclaredResidualStressSupport,
        ResidualStressEvidenceRecord,
        ResidualStressEvidenceAssessment,
        PhaseFractionContrastAssessment,
        PhaseFractionContrastObservation,
        PhaseFractionContrastRequirement,
        PhaseFractionCovariance,
        PhaseFractionLinearTerm,
        PhaseLabelMapMetadata,
        PhasePixelLabel,
        PhaseFractionMapRow,
        PhaseLabelMapAreaFractionResult,
        OxfordEbsdPhaseLabelReadRecord,
        PhaseMapClusterStatistics,
        PhaseMapInterfaceLength,
        PhaseMapTopologySummary,
        CoqtelArchiveAuditRequest,
        CoqtelElectrochemistryRow,
        CoqtelReadAuthorization,
        ThermalRodArchiveAuditRequest,
        ThermalRodObservationRow,
        ThermalRodReadAuthorization,
        CrackArrestArchiveAuditRequest,
        CrackArrestObservationRow,
        CrackArrestReadAuthorization,
        GuidedWaveArchiveAuditRequest,
        GuidedWaveReadAuthorization,
        GuidedWaveSampleRow,
        CarbonateActivityCoefficientRecord,
        CallerSpeciesActivityRecord,
        CarbonateKspKnotRecord,
        FixedFugacityCarbonateScaleKnot,
        FixedFugacityCarbonateScaleKinetics,
        CeitFieldArchiveAuditRequest,
        CeitFieldObservationRow,
        CeitFieldReadAuthorization,
        ZenodoDeisMatrixAuditRequest,
        ZenodoDeisMatrixRow,
        ZenodoDeisReadAuthorization,
        CorrosionMetricsArchiveAuditRequest,
        CorrosionMetricObservationRow,
        CorrosionMetricsReadAuthorization,
        CreviceSpatialMassActionWorkflow,
        InceGlinkaCycleGroup,
        InceGlinkaGSAMinerCampaign,
        FractureToughnessArchiveAuditRequest,
        FractureToughnessObservationRow,
        FractureToughnessReadAuthorization,
        AtmosphericArchiveAuditRequest,
        AtmosphericCorrosionObservationRow,
        AtmosphericReadAuthorization,
        MultiaxialInvariantLimitScreen,
        MultiaxialSinesMeanLimitScreen,
        PapadopoulosPlaneShearQuadrature,
        PapadopoulosP2FiniteSampleScreen,
        DangVanShearSystem,
        DangVanFiniteSampleScreen,
        WangBrownTemporalExcursion,
        CreviceWallSinkRateHistoryRequest,
        CreviceWallSinkRateObservations,
        CreviceWallSinkArrheniusCalibrationRequest,
        CreviceApertureDisplacementFlowRequest,
        CreviceSolidVolumeInventoryRequest,
        CreviceDepositionApertureHistoryRequest,
        CreviceDepositionVolumeKnot,
        CreviceLocalSolidSaturationRequest,
        CreviceExternalActivitySolidSaturationRequest,
        CreviceSaturationExposureHistoryRequest,
        CreviceSaturationHistoryKnot,
        CreviceDepositionTransportGeometryRequest,
        SampledShearPathArea,
        PrincipalStressAxisRotation,
        J2PragerStrainHistory,
        PapadopoulosP1ShearSystem,
        PapadopoulosP1FiniteIntegralScreen,
        PapadopoulosP1Calibration,
        PapadopoulosP1CalibratedLife,
        PapadopoulosP1CycleBlock,
        PapadopoulosP1MinerBlocks,
        CarpinteriSpagnoliPlane,
        CarpinteriSpagnoliFiniteScreen,
        CarpinteriSpagnoliLife,
        PeriodicTensorFourierReconstruction,
        PeriodicFourierTensorWork,
        FourierWorkLifeCycle,
        FourierTensorWorkLife,
        PeriodicTensorFourierRates,
        CreviceCalibratedWallSinkHistoryRequest,
        CreviceCalibratedWallFluxRequest,
        CreviceSpeciesWallRateHistory,
        CreviceMultispeciesWallFluxRequest,
        CreviceWallSinkGroupCVRequest,
        CreviceKineticSolidVolumeHistoryRequest,
        CreviceLocalSaturationKnot,
        CreviceSaturationIntervalRateRequest,
        CreviceSolidInventoryGeometryRemapRequest,
        CreviceWallFluxInventoryHistoryRequest,
        WetCo2TwoFilmTransferRequest,
        WetCo2TwoFilmTransferHistoryRequest,
        WetCo2TwoFilmTransferKnot,
        WetCo2LiquidSideMassTransferRequest,
        WetCo2FiniteLiquidTransferInterval,
        WetCo2FiniteLiquidTransferHistoryRequest,
        WetCo2CarbonateAlkalinityRequest,
        WetCo2FiniteGasLiquidInterval,
        WetCo2FiniteGasLiquidHistoryRequest,
        WetCo2GasSideMassTransferRequest,
        WetCo2ParallelTransferZone,
        WetCo2ParallelTransferRequest,
        WetCo2ReactiveFilmTransferRequest,
        WetCo2CondensateStateRequest,
        ZrAlloyReadAuthorization,
        ZrAlloyWorkbookAuditRequest,
        ZrAlloyWorkbookRow,
        CT110ReadAuthorization,
        CT110CorrosionRateRow,
        CT110WorkbookAuditRequest,
        ContactResponseQuery,
        ContactResponseReceipt,
        GasketContactRootLocalization,
        ElasticJointToFlangeContactHistory,
        GeometryAwareAqueousSpecies,
        GeometryAwareReactionDefinition,
        CreviceGeometryAwareAqueousChemistryContract,
        SolidCoupledSpecies,
        SolidPhaseInventoryBasis,
        CallerSolidReactionExtent,
        CreviceGeometryAwareSolidDepositionContract,
        WetCo2VariableCondensateInterval,
        WetCo2VariableCondensateHistoryRequest,
        WetCo2FiniteGasVariableLiquidInterval,
        WetCo2FiniteGasVariableLiquidHistoryRequest,
        DangVanFiniteParameterLifeCurve,
        WangBrownParameterLifeFit,
        CarbonateBoundaryPartitionUse,
        CarbonateTransportBoundaryHistoryKnot,
        WetCo2CarbonateTransportBoundaryHistoryRequest,
        Co2starWallConsumptionMapping,
        WetCo2WallReactionCoupledHistoryRequest,
        MultiBoltFlangeContactInfluenceRequest,
        MultiBoltFlangeContactInfluenceOutput,
        GasketBoltPlanarPosition,
        GasketContactNodePlanarPosition,
        GasketJointSpatialResultantBalance,
        BoltFatigueCurve,
        GasketBoltCyclicDamage,
        CircumferentialContactNode,
        GasketCircumferentialContactContinuity,
        CreviceComponentDiffusionSupport,
        CreviceComponentDiffusionInterval,
        CreviceComponentDiffusionHistory,
        WetCo2ReactantFilmRecord,
        WetCo2TransportLimitedMixedPotentialRequest,
        WetCo2FiniteGasMultispeciesHistoryRequest,
        WetCo2SpeciesFluxInterval,
        MultiaxialCrosslandProportionalLimitScreen,
        MultiaxialDeviatoricStressPathVariation,
        SinesParameterLifePoint,
        MultiaxialSinesParameterLife,
        SinesLifeCalibrationTest,
        MultiaxialSinesLifeFit,
        J2ArmstrongFrederickStrainHistory,
        WallWaterSaturationPoint,
        LumpedWallCondensationInterval,
        WetCo2LumpedWallThermalCondensationRequest,
        WetCo2SimultaneousScaleInterval,
        WetCo2ScaleCorrosionSimultaneousHistoryRequest,
        CreviceSpatialReactionBranch,
        CreviceSpatialOhmicMixedPotentialRequest,
        CreviceSpatialDissolutionBranchMapping,
        CreviceSpatialMetalLossRequest,
        CreviceTransportConstraintBinding,
        CreviceLocalEquilibriumKnot,
        CreviceTransportLocalMassActionRequest,
        CreviceIonicReactiveSpecies,
        CreviceIonicReactionTerm,
        CreviceIonicReaction,
        CreviceIonicReactiveTransportRequest,
        BoltProofStrengthPoint,
        BoltMaterialStrengthBasis,
        GasketBoltNominalStrengthScreen,
        GasketPressureInventoryDecay,
        McDiarmidTensorState,
        McDiarmidCandidatePlane,
        McDiarmidCriticalPlaneLimitScreen,
        McDiarmidIndexLifePoint,
        McDiarmidLifeCurve,
        McDiarmidCycleBlock,
        McDiarmidMinerCampaign,
        GasketPolarContactMap,
        GasketRadialOpenPathScreen,
        GasketCompressionLoop,
        GasketCompressionHysteresisEnergy,
        TemperatureCompressionCurve,
        GasketTemperatureCompressionCurveTransfer,
        TemperatureJointBolt,
        TemperatureJointSector,
        TemperatureJointLoadStep,
        GasketTemperatureCompressionJointHistory,
        ComponentThermalExpansionRecord,
        GasketThermoelasticExpansionJointHistory,
        JointLoadCovarianceCoordinate,
        GasketJointEquilibriumLocalCovariance,
        PairedLifeCalibrationPoint,
        MultiaxialCalibrationTransferAudit,
        GasketBoltTighteningOperation,
        GasketBoltPreloadSequenceRedistribution,
        WetCo2CylindricalScalePhase,
        WetCo2ScalePhaseLineInventory,
        WetCo2CylindricalGeometryKnot,
        WetCo2CylindricalScaleGeometryHistory,
        WetCo2CylindricalGeometryCoupledHistory,
        GasketCompressionCurveObservation,
        GasketCompressionCurveMonotoneFit,
        GasketFEFieldSelection,
        GasketFEContactLocation,
        GasketFENormalizedFieldArray,
        GasketFESupportObservation,
        GasketFEContactSnapshot,
        ExternalGasketFEFieldImportRequest,
        TensorComponentBinding,
        GasketFEVonMisesCallerLimitScreen,
        WetCo2CylindricalSpeciesBoundary,
        WetCo2CylindricalElectrodeKnot,
        WetCo2CylindricalTransportMixedPotential,
        WetCo2TransientSpecies,
        WetCo2WallElement,
        WetCo2TransientWallReaction,
        WetCo2TransientInitialSpecies,
        WetCo2TransientSpeciesBoundary,
        WetCo2ReactionExtentRate,
        WetCo2TransientTransportKnot,
        WetCo2CylindricalTransientTransport,
        WetCo2CylindricalActivityProductTerm,
        WetCo2CylindricalPhaseActivityKnot,
        WetCo2CylindricalWallSaturationScaleKinetics,
        WetCo2CylindricalScaleKineticsGeometryHandoff,
        ReferenceMultiaxialLifeCurvePoint,
        MultiaxialPowerLawLifeTransfer,
        WetCo2LayerSpeciesDiffusivity,
        WetCo2SolutionSpeciesDiffusivity,
        WetCo2CylindricalMultilayerTransportKnot,
        WetCo2CylindricalMultilayerTransportResistance,
        WetCo2DiffusionLimitedSolidReactant,
        WetCo2DiffusionLimitedBulkSpecies,
        WetCo2DiffusionLimitedBulkKnot,
        WetCo2CylindricalDiffusionLimitedScaleGrowth,
        WetCo2CylindricalPhaseGrowthCampaign,
        WetCo2CylindricalScaleRecessionFeedback,
        WetCo2ScaleReactionKnot,
        WetCo2AqueousScalePhase,
        WetCo2CylindricalAqueousScaleSinkFeedback,
        WetCo2StageActivityProductTerm,
        WetCo2StageActivityKnot,
        WetCo2StageKineticPhase,
        WetCo2CylindricalStageKineticScaleFeedback,
        WetCo2StageSpeciationProductTerm,
        WetCo2StageSpeciationKineticPhase,
        WetCo2CylindricalStageSpeciationScaleFeedback,
        WetCo2FiniteGasStageSpeciationProductTerm,
        WetCo2FiniteGasStageSpeciationKineticPhase,
        WetCo2CylindricalFiniteGasStageSpeciationFeedback,
        WetCo2CylindricalFiniteGasStageGeometryFeedback,
        CreviceNernstBranchMap,
        CreviceFaradaicBranchMap,
        CreviceFaradaicSpatialChemistryRequest,
        MagnesiumFspSccReadAuthorization,
        MagnesiumFspSccWorkbookCell,
        MagnesiumFspSccWorkbookRow,
        MagnesiumFspSccAuditRequest,
        ExplosiveWeldFatigueReadAuthorization,
        ExplosiveWeldFatigueWorkbookCell,
        ExplosiveWeldFatigueWorkbookRow,
        ExplosiveWeldFatigueAuditRequest,
        ExplosiveWeldFatigueColumnMapping,
        ExplosiveWeldFatigueWorksheetMapping,
        ExplosiveWeldFatigueMappedImportRequest,
        ExplosiveWeldFatigueObservationField,
        ExplosiveWeldFatigueMappedObservationRow,
        AISI1018ReadAuthorization,
        AISI1018FileMapping,
        AISI1018InventoryRequest,
        AISI1018InventoryItem,
        WetCo2CylindricalCoupledScaleGeometryReplay,
        CcpsReleaseHistoryInterval,
        CcpsReleaseHistorySource,
        CcpsDenseSubstance,
        CcpsDenseAtmosphere,
        CcpsDenseReceptor,
        CcpsReleaseHistorySettings,
        CcpsReleaseHistoryRequestEnvelope,
        MetastablePittingMeasurementRow,
        MetastablePittingReadAuthorization,
        MprDecodedRecord,
        ScaleAnodicBranch,
        ScaleCathodicReactantBranch,
        ScaleDiffusionElectrodeKnot,
        WetCo2ScaleDiffusionElectrodeHistory,
        CoCrCorrosionReadAuthorization,
        CoCrWorkbookCell,
        CoCrCorrosionWorkbookRow,
        CoCrWorksheetManifest,
        CoCrWorkbookManifest,
        AHSS1300PermeationReadAuthorization,
        AHSS1300WorkbookCell,
        AHSS1300PermeationWorkbookRow,
        AHSS1300WorksheetManifest,
        AHSS1300WorkbookAuditRequest,
        Polarization316LRawRow,
        Polarization316LReadAuthorization,
        Polarization316LArchiveAuditRequest,
        WetCo2MetalToScaleYield,
        WetCo2MovingScaleInterval,
        WetCo2ScaleCorrosionMovingGeometryHistoryRequest,
        GasketPressureThreshold,
        GasketContactDistributionStatistics,
        CrosslandProportionalBlock,
        CrosslandProportionalMinerCampaign,
        WetCo2TransientCarbonateInterval,
        WetCo2TransientCarbonateHistoryRequest,
        GasketContactSubthresholdExposure,
        GasketPronyTemperatureShiftLaw,
        GasketTemperatureShiftedPronyHistory,
        GasketPronyRelaxationObservation,
        GasketPronyRelaxationTest,
        GasketPronyRelaxationSpectrumFit,
        WetCo2GasFilmCondensationInterval,
        WetCo2GasFilmCondensationHistoryRequest,
        FiniteGasWaterExchangeInterval,
        FiniteGasWaterCondensationHistoryRequest,
        CreviceElectroneutralSpecies,
        CreviceElectroneutralDiffusionRequest,
        CreviceActivityGradientSpecies,
        CreviceActivityGradientFluxRequest,
        CreviceActivityTransportSpecies,
        CreviceActivityCorrectedTransportRequest,
        CreviceActivityRateSpecies,
        CreviceActivityRateTerm,
        CreviceActivityRateReaction,
        CreviceActivityRateRequest,
        CreviceActivityReactiveSpecies,
        CreviceActivityReactiveTerm,
        CreviceActivityReactiveReaction,
        CreviceActivityReactiveTransportRequest,
        CreviceRepassivationThresholdKnot,
        CreviceOperatingPotentialKnot,
        CreviceRepassivationMarginHistoryRequest,
        CreviceRepassivationExcursionDurationRequest,
        CreviceEquilibriumAqueousSpecies,
        CreviceCompetingSolidPhase,
        CreviceCompetingSolidEquilibriumRequest,
        CreviceCellActivitySolidInput,
        CreviceSpatialActivitySolidFixedPointRequest,
        CreviceChemistryKnot,
        CreviceSpatialChemistryTransportRequest,
        CreviceSpatialChemistryApertureFixedPointRequest,
        CreviceCurrentCarryingNernstPlanckRequest,
        CreviceCurrentCarryingApertureFeedbackRequest,
        CreviceCurrentBranchMetalMapping,
        CreviceCurrentCarryingExtentMetalLossRequest,
        FormatePackerReadAuthorization,
        FormatePackerWorkbookCell,
        FormatePackerWorkbookRow,
        FormatePackerWorkbookAuditRequest,
        WetCo2ScaleShearKnot,
        WetCo2CylindricalShearLimitedScaleRemoval,
        WetCo2CylindricalHydraulicKnot,
        WetCo2CylindricalSteadyHydraulics,
        WetCo2CylindricalHydraulicsToScaleRemoval,
        WetCo2CylindricalLiquidDiffusivityKnot,
        WetCo2CylindricalLiquidTransferCapacityHistory,
        WetCo2CylindricalLiquidConcentrationKnot,
        WetCo2CylindricalExternalLiquidExchange,
        WetCo2CylindricalFiniteLiquidTransferInventory,
        WetCo2FiniteLiquidWallExchange,
        WetCo2FiniteInventorySaturationScaleGeometry,
        WetCo2LumpedElectrochemicalSpecies,
        WetCo2LumpedElectrochemicalInitialInventory,
        WetCo2LumpedElectrochemicalVolumeKnot,
        WetCo2LumpedElectrochemicalReaction,
        WetCo2LumpedElectrochemicalInterval,
        WetCo2LumpedElectrochemicalExternalExchange,
        WetCo2FiniteInventoryElectrodeMixedPotential,
        WetCo2SpatialElectrochemicalKnot,
        WetCo2CylindricalSpatialMixedPotential,
        WetCo2AqueousIon,
        WetCo2NeutralSolidFormulaProposals,
        ReactiveTransportSpecies,
        ReactiveTransportTerm,
        ReactiveTransportReaction,
        CreviceNeutralReactiveTransportRequest,
        AZ31BCorrosionFatigueReadAuthorization,
        AZ31BCorrosionFatigueWorkbookCell,
        AZ31BCorrosionFatigueWorkbookRow,
        AZ31BCorrosionFatigueAuditRequest,
        WetCo2CylindricalBVWallRecession,
        CreviceActivityTransportPhaseApertureRequest,
        MDEAEISReadAuthorization,
        MDEAEISCell,
        MDEAEISPointRow,
        MDEAEISFolderAuditRequest,
        MDEAEISComplexPoint,
        MDEAEISComplexConversionRequest,
        X80SCCReadAuthorization,
        X80SCCWorkbookCell,
        X80SCCWorkbookRow,
        X80SCCDirectoryAuditRequest,
        WetCo2GeometryFixedPointRequest,
        InternalCorrosionReadAuthorization,
        InternalCorrosionWorkbookCell,
        InternalCorrosionWorkbookRow,
        InternalCorrosionWorkbookAuditRequest,
        CreviceActivityTransportSequentialApertureCampaign,
        VariableAreaCreviceActivityReactiveTransportRequest,
        CoolPropPureWaterSinglePhaseStateRequest,
        CreviceAqueousComponentLedgerRequest,
        ConstraintRoleAssignment,
        ConservedAqueousComponent,
        ComponentSpeciesCoefficient,
        SpeciesCellAmount,
        SpeciesFaceTransfer,
        InitialSpeciesAmount,
        CreviceClosedBatchAqueousEquilibriumRequest,
        CellAqueousEquilibriumTemplate,
        ComponentInventoryByCell,
        SpeciesFaceDiffusivity,
        ExternalReservoirElementChange,
        ExternalReservoirComponentChange,
        ElectrochemicalSourceReaction,
        ElectrochemicalSourceExtentSchedule,
        IonicFaceCurrentSchedule,
        CellSolidPhaseSet,
        CellDynamicSolidGeometry,
        SolidPhaseGeometryMap,
        CreviceComponentStateBDFRequest,
        CreviceBDFInitialSolidInventory,
        CreviceBDFKineticPhaseSet,
        CapacitiveCellCurrentSchedule,
        CreviceHydraulicComponentAdvection,
        CreviceDynamicHydraulicAdvection,
        CreviceMovingVolumeContinuityRequest,
        CreviceMovingVolumeHydraulicHistoryRequest,
        HandoffPhaseGeometry,
        CreviceComponentStateSegmentHandoffRequest,
        CreviceSegmentGeometry,
        CreviceComponentStateSegmentTransitionRequest,
        NucleationSaturationInterval,
        CreviceMolarNucleationLaw,
        EvidenceBoundSaturationGrowthLaw,
        CreviceNucleationKineticHistoryRequest,
        CreviceCurrentCarryingCellBinding,
        CreviceCurrentCarryingComponentStateBinding,
        CreviceDoubleLayerChargeHistoryRequest,
        CreviceDoubleLayerBDFBindingRequest,
        DynamicDoubleLayerPolarizationBranch,
        CreviceDynamicDoubleLayerFaradaicHistoryRequest,
        DynamicBranchReactionMap,
        CreviceDynamicDoubleLayerBDFBindingRequest,
        SCCCrackVelocityLaw,
        SCCCrackVelocityHistoryRequest,
        SCCFaultTreeProbabilityInput,
        SCCFaultTreeBindingRequest,
        SCCFaultTreeEventBinding,
    )
    registry = default_registry()
    contracts = complete_export_contracts(contracts, registry)
    name_counts = Counter(contract.__name__ for contract in contracts)
    filenames = [contract_schema_filename(contract, name_counts) for contract in contracts]
    if len(filenames) != len(set(filenames)):
        raise ValueError("public schema output filenames are not unique")
    for contract, filename in zip(contracts, filenames, strict=True):
        path = target / filename
        payload = json.dumps(contract.model_json_schema(), ensure_ascii=False, indent=2)
        if not path.exists() or path.read_text(encoding="utf-8") != payload:
            path.write_text(payload, encoding="utf-8")
    # Remove only the four legacy outputs that previously collided and were overwritten.
    for name in ("HardnessTestConfiguration", "Criterion", "Profile", "Result"):
        legacy = target / f"{name}.json"
        if name_counts[name] > 1 and legacy.exists():
            legacy.unlink()
    index = write_schema_index(target, contracts, name_counts, registry)
    print(
        f"Exported {len(contracts)} public contract schemas; indexed {index['registered_model_count']} registered API inputs"
    )


if __name__ == "__main__":
    main()
