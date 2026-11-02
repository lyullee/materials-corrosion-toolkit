"""Observed metallographic point-count descriptors with unresolved labels retained."""

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract
from ..registry import ModelSpec
from .engineering_correlations import SOURCE_ID, CorrelationRequest


class PhasePointCountField(Contract):
    field_id: str = Field(min_length=1)
    image_id: str = Field(min_length=1)
    image_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    coordinate_frame_id: str = Field(min_length=1)
    grid_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    physical_specimen_id: str = Field(min_length=1)
    total_test_points: int = Field(ge=1, le=1_000_000_000)
    phase_counts: dict[str, int] = Field(min_length=1, max_length=100)
    unresolved_points: int = Field(ge=0, le=1_000_000_000)

    @model_validator(mode="after")
    def counts_close(self):
        if any(not key.strip() or value < 0 for key, value in self.phase_counts.items()):
            raise ValueError("phase count labels must be nonblank and counts nonnegative")
        if sum(self.phase_counts.values()) + self.unresolved_points != self.total_test_points:
            raise ValueError("classified and unresolved counts must equal all test points")
        return self


class PhasePointCountSummary(CorrelationRequest):
    survey_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    phase_definition_id: str = Field(min_length=1)
    counting_procedure_revision_id: str = Field(min_length=1)
    phase_ids: tuple[str, ...] = Field(min_length=1, max_length=100)
    fields: tuple[PhasePointCountField, ...] = Field(min_length=1, max_length=10000)
    point_identity_and_nonoverlap_reviewed: bool

    @model_validator(mode="after")
    def exact_identity(self):
        for ids in (self.phase_ids, tuple(row.field_id for row in self.fields)):
            if len(set(ids)) != len(ids) or any(not key.strip() for key in ids):
                raise ValueError("phase and field identities must be unique and nonblank")
        if any(set(row.phase_counts) != set(self.phase_ids) for row in self.fields):
            raise ValueError("every field must explicitly count every declared phase; missing is not zero")
        if any(row.physical_specimen_id != self.physical_specimen_id for row in self.fields):
            raise ValueError("all fields must retain the same physical specimen identity")
        # Exact duplicate image/grid records cannot be counted twice under another field ID.
        records = [(row.image_sha256, row.grid_record_sha256) for row in self.fields]
        if len(set(records)) != len(records):
            raise ValueError("duplicate image/grid sampling records cannot be pooled")
        return self


def phase_point_count_summary(x: PhasePointCountSummary) -> Calculation:
    def describe(total, counts, unknown):
        return dict(
            total_test_points=total,
            phase_counts=counts,
            unresolved_points=unknown,
            observed_phase_point_fractions={key: value / total for key, value in counts.items()},
            phase_fraction_identification_bounds={
                key: [value / total, (value + unknown) / total] for key, value in counts.items()
            },
        )

    fields = [
        dict(
            field_id=row.field_id,
            image_id=row.image_id,
            image_sha256=row.image_sha256,
            coordinate_frame_id=row.coordinate_frame_id,
            grid_record_sha256=row.grid_record_sha256,
            **describe(row.total_test_points, dict(row.phase_counts), row.unresolved_points),
        )
        for row in x.fields
    ]
    values = dict(
        survey_id=x.survey_id,
        physical_specimen_id=x.physical_specimen_id,
        material_condition_id=x.material_condition_id,
        phase_definition_id=x.phase_definition_id,
        counting_procedure_revision_id=x.counting_procedure_revision_id,
        field_summaries=fields,
    )
    if not x.point_identity_and_nonoverlap_reviewed:
        return Calculation(
            status="needs_data",
            values=values,
            notes=("Point identity and nonoverlap require review before pooled counting.",),
        )
    total = sum(row.total_test_points for row in x.fields)
    unknown = sum(row.unresolved_points for row in x.fields)
    counts = {key: sum(row.phase_counts[key] for row in x.fields) for key in x.phase_ids}
    values["pooled_point_summary"] = describe(total, counts, unknown)
    return Calculation(
        status="needs_data" if unknown else "computed",
        values=values,
        notes=(
            "Pooled counts weight each counted point equally; field fractions are not averaged with equal field weights.",
            "Identification bounds assign all unresolved points to or away from each phase separately; they are not simultaneous confidence intervals.",
            "Observed point fractions do not establish representative volume fractions, independent fields, FN conversion, phase identification validity, corrosion resistance or acceptance.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "testing.phase_point_count_summary",
            PhasePointCountSummary,
            phase_point_count_summary,
            {"field_summaries": "structured_record", "pooled_point_summary": "structured_record"},
            (
                "Caller phase labels and immutable image/grid records; same physical specimen and reviewed nonoverlap.",
            ),
            (SOURCE_ID,),
            qualification="user_model",
        )
    ]
