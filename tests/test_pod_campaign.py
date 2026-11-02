from copy import deepcopy

from matintegrity.pod_campaign import PODCampaignAuditRequest, audit_pod_campaign


def payload():
    observations = []
    for index, size in enumerate((1, 2, 3, 4, 5, 6), start=1):
        observations.append(
            {
                "observation_id": f"o{index}",
                "specimen_id": f"s{index}",
                "flaw_size_m": size / 1000,
                "detected": index >= 4,
                "operator_id": "op-a" if index % 2 else "op-b",
                "procedure_id": "proc-1",
                "material_group": "steel",
                "geometry_group": "plate",
                "access_group": "surface-a",
                "is_blind": True,
            }
        )
    return {
        "campaign_id": "campaign-1",
        "observations": observations,
        "flaw_size_resolution_m": 0.001,
        "requirement_profile": {
            "profile_id": "user-profile",
            "revision": "1",
            "minimum_total_observations": 6,
            "minimum_hits": 2,
            "minimum_misses": 2,
            "minimum_distinct_flaw_sizes": 5,
            "minimum_observations_per_operator": 3,
            "required_operator_ids": ["op-a", "op-b"],
            "required_material_groups": ["steel"],
            "required_geometry_groups": ["plate"],
            "required_access_groups": ["surface-a"],
        },
    }


def test_complete_campaign_is_ready_and_deterministic():
    request = PODCampaignAuditRequest.model_validate(payload())
    first = audit_pod_campaign(request)
    second = audit_pod_campaign(request)
    assert first.status == "ready_for_model_fit"
    assert first.report_digest == second.report_digest
    assert first.qualification_claimed is False
    assert first.hit_count == first.miss_count == 3


def test_missing_coverage_and_repeated_specimen_are_explicit():
    value = deepcopy(payload())
    value["requirement_profile"]["required_material_groups"].append("nickel-alloy")
    value["observations"][1]["specimen_id"] = "s1"
    report = audit_pod_campaign(PODCampaignAuditRequest.model_validate(value))
    failed = {item.finding_id: item for item in report.findings if item.status == "not_satisfied"}
    assert report.status == "coverage_not_satisfied"
    assert failed["required_material_coverage"].observed == ["nickel-alloy"]
    assert failed["one_observation_per_specimen"].observed == ["s1"]


def test_nonblind_observation_fails_blind_design_gate():
    value = payload()
    value["observations"][0]["is_blind"] = False
    report = audit_pod_campaign(PODCampaignAuditRequest.model_validate(value))
    finding = next(item for item in report.findings if item.finding_id == "blind_design")
    assert finding.status == "not_satisfied"
