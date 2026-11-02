"""Missing external evidence must not be converted into a passing calculation."""

import json

import pytest
from pydantic import ValidationError

from matintegrity.atmospheric_typed_rows import AtmosphericReadAuthorization
from matintegrity.corrosion_rate_history import CorrosionRateThicknessHistoryRequest


@pytest.mark.parametrize("origin", ["synthetic", "user_declared", "model_prediction", "open_dataset"])
def test_unmeasured_thickness_cannot_impersonate_a_measured_baseline(origin):
    # These are authored numerical placeholders, never experimental observations.
    evidence = dict(
        source_id="authored-placeholder", origin=origin, citation="Synthetic contract rejection test"
    )
    payload = dict(
        history_id="toy",
        asset_id="toy",
        location_id="toy",
        material_id="toy",
        material_condition_id="toy",
        physical_scope_id="toy",
        time_basis="elapsed seconds",
        knots=[
            dict(knot_index=i, time_s=float(i), corrosion_rate_m_s=1e-6, evidence=[evidence])
            for i in range(2)
        ],
        baseline_thickness_m=0.01,
        baseline_evidence=evidence,
        required_thickness_m=0.005,
        required_thickness_evidence=evidence | dict(origin="user_declared"),
        ordered_history_reviewed=True,
        rate_source_mapping_reviewed=True,
        piecewise_linear_rate_reconstruction_reviewed=True,
        uniform_area_average_loss_reviewed=True,
        material_condition_and_location_reviewed=True,
        finite_support_no_extrapolation_reviewed=True,
    )
    with pytest.raises(ValidationError, match="baseline thickness evidence must be measured"):
        CorrosionRateThicknessHistoryRequest.model_validate_json(json.dumps(payload))


@pytest.mark.parametrize(
    "field",
    ["computational_use_authorized", "underlying_observation_use_authorized", "local_only_authorized"],
)
@pytest.mark.parametrize("missing", [True, False])
def test_atmospheric_authorization_is_never_implied(field, missing):
    payload = dict(
        attribution="Contract check only; no observation access",
        computational_use_authorized=True,
        underlying_observation_use_authorized=True,
        local_only_authorized=True,
    )
    if missing:
        del payload[field]
    else:
        payload[field] = False
    with pytest.raises(ValidationError) as error:
        AtmosphericReadAuthorization.model_validate_json(json.dumps(payload))
    assert field in str(error.value)
