"""Caller-owned component material profiles without imposed piping or rating quantities."""

from pydantic import Field, model_validator

from ..component_matching import material_membership_findings, required_attribute_findings
from ..contracts import Calculation, Contract
from ..registry import ModelSpec
from .engineering_correlations import SOURCE_ID, CorrelationRequest


class ComponentMaterialRequirement(Contract):
    component_role: str = Field(min_length=1)
    allowed_material_condition_ids: tuple[str, ...] = Field(min_length=1)
    required_attributes: dict[str, str]
    minimum_count: int = Field(default=1, ge=0)
    maximum_count: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def explicit_rule(self):
        if len(set(self.allowed_material_condition_ids)) != len(self.allowed_material_condition_ids) or any(
            not s.strip() for s in self.allowed_material_condition_ids
        ):
            raise ValueError("allowed material-condition identities must be unique and nonblank")
        if any(not k.strip() or not v.strip() for k, v in self.required_attributes.items()):
            raise ValueError("required attribute labels must be nonblank")
        if self.maximum_count is not None and self.maximum_count < self.minimum_count:
            raise ValueError("component count bounds must be ordered")
        return self


class MaterialClassComponentRecord(Contract):
    component_id: str = Field(min_length=1)
    component_role: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    material_condition_id: str | None = Field(default=None, min_length=1)
    attributes: dict[str, str | None]
    source_id: str = Field(min_length=1)
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class ComponentMaterialClassAssessment(CorrelationRequest):
    class_id: str = Field(min_length=1)
    class_revision: str = Field(min_length=1)
    governing_requirement_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    service_id: str = Field(min_length=1)
    allowed_service_ids: tuple[str, ...] = Field(min_length=1)
    requirements: tuple[ComponentMaterialRequirement, ...] = Field(min_length=1, max_length=1000)
    components: tuple[MaterialClassComponentRecord, ...] = Field(max_length=10000)
    profile_authority_and_component_mapping_reviewed: bool

    @model_validator(mode="after")
    def exact_roles_and_scope(self):
        for values in (
            self.allowed_service_ids,
            tuple(r.component_role for r in self.requirements),
            tuple(r.component_id for r in self.components),
        ):
            if len(set(values)) != len(values) or any(not s.strip() for s in values):
                raise ValueError("service, role and component identities must be unique and nonblank")
        if any(r.physical_scope_id != self.physical_scope_id for r in self.components):
            raise ValueError("every component must belong to the declared physical scope")
        return self


def component_material_class_assessment(x: ComponentMaterialClassAssessment) -> Calculation:
    base = {
        "class_id": x.class_id,
        "class_revision": x.class_revision,
        "governing_requirement_id": x.governing_requirement_id,
        "physical_scope_id": x.physical_scope_id,
        "service_id": x.service_id,
    }
    if x.service_id not in x.allowed_service_ids:
        return Calculation(
            status="out_of_scope", values=base, notes=("Service is outside the caller class profile.",)
        )
    if not x.profile_authority_and_component_mapping_reviewed:
        return Calculation(
            status="needs_data",
            values=base,
            notes=("Profile authority and component role mapping require review.",),
        )
    rules = {r.component_role: r for r in x.requirements}
    findings = []
    for component in x.components:
        rule = rules.get(component.component_role)
        if rule is None:
            missing, mismatched = ["component_role_rule"], []
        else:
            missing, mismatched = material_membership_findings(
                component.material_condition_id, rule.allowed_material_condition_ids
            )
            a, b = required_attribute_findings(component.attributes, rule.required_attributes)
            missing.extend(a)
            mismatched.extend(b)
        findings.append(
            {
                "component_id": component.component_id,
                "component_role": component.component_role,
                "source_id": component.source_id,
                "record_sha256": component.record_sha256,
                "missing_fields": missing,
                "mismatched_fields": mismatched,
                "outcome": "not_satisfied" if mismatched else "unknown" if missing else "satisfied",
            }
        )
    counts = []
    for role, rule in rules.items():
        count = sum(r.component_role == role for r in x.components)
        counts.append(
            {
                "component_role": role,
                "observed_count": count,
                "minimum_count": rule.minimum_count,
                "maximum_count": rule.maximum_count,
                "below_minimum": count < rule.minimum_count,
                "above_maximum": rule.maximum_count is not None and count > rule.maximum_count,
            }
        )
    missing = any(r["missing_fields"] for r in findings) or any(r["below_minimum"] for r in counts)
    mismatch = any(r["mismatched_fields"] for r in findings) or any(r["above_maximum"] for r in counts)
    return Calculation(
        status="needs_data" if missing else "computed",
        values=base
        | {
            "declared_component_class_outcome": "not_satisfied"
            if mismatch
            else "unknown"
            if missing
            else "satisfied",
            "component_findings": findings,
            "role_counts": counts,
        },
        notes=(
            "Exact caller material-condition and attribute labels with explicit component multiplicity; no pressure rating or corrosion allowance is invented for unrelated components.",
            "A declared profile match is not material equivalence, compatibility, pressure-temperature capacity, pump/valve performance, certification or production acceptance.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("component class asset and location must match the run context")

    return [
        ModelSpec(
            "materials.component_material_class_assessment",
            ComponentMaterialClassAssessment,
            component_material_class_assessment,
            {"component_findings": "structured_record", "role_counts[].observed_count": "count"},
            (
                "Caller profile authority, physical scope, service and component role mapping are explicit; exact labels only.",
            ),
            (SOURCE_ID,),
            qualification="user_model",
            context_validator=same_identity,
        )
    ]
