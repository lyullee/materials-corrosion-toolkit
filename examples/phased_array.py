"""Build an encoded phased-array record directly with Python objects."""

from matintegrity.contracts import Evidence
from matintegrity.models.phased_array import (
    EncodedPhasedArrayFrame,
    PhasedArrayBeamLaw,
    PhasedArrayExamination,
    PhasedArrayProbe,
    PhasedArrayWedge,
    phased_array_acquisition_summary,
)

record = Evidence(
    source_id="user-paut-record",
    origin="user_declared",
    citation="replace with the controlled acquisition record",
)
probe = PhasedArrayProbe(
    probe_id="probe-a",
    role="pulse_echo",
    element_count=4,
    element_pitch_m=0.001,
    element_width_m=0.0008,
    center_frequency_Hz=5.0e6,
    element_layout_basis="replace with controlled probe datasheet",
    evidence=[record],
)
wedge = PhasedArrayWedge(
    wedge_id="wedge-a",
    probe_id="probe-a",
    wedge_material_id="polymer-a",
    wedge_longitudinal_velocity_m_s=2300.0,
    nominal_exit_point_offset_m=0.01,
    mounting_orientation="replace with controlled orientation record",
    evidence=[record],
)
law = PhasedArrayBeamLaw(
    law_id="law-a",
    transmit_probe_id="probe-a",
    receive_probe_id="probe-a",
    refracted_angle_rad=0.7,
    refracted_wave_mode="longitudinal",
    focus_distance_m=0.02,
    first_transmit_element=0,
    transmit_element_count=4,
    transmit_delay_s=[0.0, 1.0e-8, 2.0e-8, 3.0e-8],
    first_receive_element=0,
    receive_element_count=4,
    receive_delay_s=[0.0, 1.0e-8, 2.0e-8, 3.0e-8],
    law_generation_basis="replace with controlled focal-law export",
)
frame = EncodedPhasedArrayFrame(
    frame_id="frame-0",
    encoder_position_m=0.0,
    beam_law_id="law-a",
    data_sha256="a" * 64,
    sample_count=1024,
    sample_interval_s=1.0e-8,
    transmit_event_count=1,
    receive_channel_count=4,
    amplitude_encoding="signed-int16",
    time_zero_basis="replace with controlled acquisition clock",
)
examination = PhasedArrayExamination(
    examination_id="paut-001",
    procedure_id="user-paut-procedure",
    procedure_revision="1",
    physical_scope_id="weld-22",
    material_condition_id="steel-weld-condition-a",
    acquisition_mode="sectorial",
    specimen_wave_velocity_m_s=5900.0,
    specimen_wave_velocity_basis="replace with reviewed material calibration",
    encoder_id="encoder-1",
    encoder_direction="increasing",
    probes=[probe],
    wedges=[wedge],
    beam_laws=[law],
    frames=[frame],
    probe_and_wedge_identity_reviewed=True,
    material_velocity_reviewed=True,
    beam_law_reviewed=True,
    encoder_calibration_reviewed=True,
    acquisition_calibration_reviewed=True,
    frame_identity_reviewed=True,
    indication_mapping_reviewed=True,
    negative_result_reviewed=True,
    evidence=[record],
)

print(phased_array_acquisition_summary(examination).model_dump_json(indent=2))
