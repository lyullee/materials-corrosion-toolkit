"""Read a pinned local ML-NDT clone without executing or redistributing provider content."""

from __future__ import annotations

import hashlib
import json
import math
import re
import uuid
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import Field, field_validator, model_validator

from .contracts import Contract

ML_NDT_DATASET_ID = "ml-ndt-augmented-phased-array"
ML_NDT_PINNED_REVISION = "6fb6aee456e64add656d1beb4e414639b13df278"
ML_NDT_PROVIDER_SHAPE = (256, 256, 100)
ML_NDT_PROVIDER_DTYPE = "UInt16"
ML_NDT_EXTENSIONS = frozenset({".bins", ".meta", ".jsons", ".labels"})
MAX_SIDECAR_BYTES = 4 * 1024 * 1024

_META = re.compile(
    r"^\s*(?P<dtype>UInt16)\s*,\s*(?P<rows>[1-9]\d*)\s*x\s*(?P<columns>[1-9]\d*)\s*x\s*(?P<images>[1-9]\d*)\s*$"
)


class MlNdtFlawMetadata(Contract):
    """One provider JSON flaw object with its original text fields intact."""

    schema_version: Literal["matintegrity.ml_ndt_flaw_metadata.v1"] = "matintegrity.ml_ndt_flaw_metadata.v1"
    raw_fields: dict[str, str]
    source_flaw_size_value: float | None = None
    equivalent_flaw_size_value: float | None = None
    augmentation_factor_value: float | None = None

    @field_validator("raw_fields")
    @classmethod
    def text_fields_only(cls, value: dict[str, str]):
        if not value or any(not key or not isinstance(item, str) for key, item in value.items()):
            raise ValueError("ML-NDT flaw metadata must contain nonempty string fields")
        return value


class MlNdtImageLabel(Contract):
    """Provider classification/size labels aligned to one image in a batch."""

    schema_version: Literal["matintegrity.ml_ndt_image_label.v1"] = "matintegrity.ml_ndt_image_label.v1"
    image_index: int = Field(ge=0)
    provider_hit_label: Literal[0, 1]
    provider_equivalent_size_value: float = Field(ge=0)
    metadata_equivalent_size_value: float | None = Field(default=None, ge=0)
    label_metadata_size_match: bool
    flaws: tuple[MlNdtFlawMetadata, ...]
    augmentation_status: Literal["provider_augmented"] = "provider_augmented"
    physical_specimen_identity: Literal["not_resolved_per_image"] = "not_resolved_per_image"
    physical_flaw_identity: Literal["not_resolved_per_image"] = "not_resolved_per_image"


class MlNdtBatchAudit(Contract):
    """Immutable audit of one four-file ML-NDT batch."""

    schema_version: Literal["matintegrity.ml_ndt_batch_audit.v1"] = "matintegrity.ml_ndt_batch_audit.v1"
    dataset_id: Literal["ml-ndt-augmented-phased-array"] = ML_NDT_DATASET_ID
    repository_revision: str = Field(pattern=r"^[a-f0-9]{40}$")
    revision_basis: Literal["caller_verified_local_clone"] = "caller_verified_local_clone"
    provider_partition: Literal["training", "validation"]
    batch_uuid: str
    source_filenames: dict[str, str]
    source_sha256: dict[str, str]
    source_bytes: dict[str, int]
    dtype_token: Literal["UInt16"]
    rows: int = Field(gt=0)
    columns: int = Field(gt=0)
    image_count: int = Field(gt=0)
    byte_order_status: Literal["not_declared_by_meta"] = "not_declared_by_meta"
    storage_order: Literal["provider_code_c_order"] = "provider_code_c_order"
    labels: tuple[MlNdtImageLabel, ...]
    metadata_size_mismatch_count: int = Field(ge=0)
    physical_source_scope: Literal["provider_reported_one_pipe_three_cracks"] = (
        "provider_reported_one_pipe_three_cracks"
    )
    qualification: Literal["augmented_images_not_independent_physical_specimens"] = (
        "augmented_images_not_independent_physical_specimens"
    )

    @model_validator(mode="after")
    def aligned_batch(self):
        if str(uuid.UUID(self.batch_uuid)).upper() != self.batch_uuid:
            raise ValueError("batch UUID must use the canonical provider uppercase form")
        if len(self.labels) != self.image_count:
            raise ValueError("ML-NDT label count must equal the declared image count")
        if tuple(row.image_index for row in self.labels) != tuple(range(self.image_count)):
            raise ValueError("ML-NDT image indices must preserve contiguous provider order")
        return self


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _data_root(path: str | Path) -> Path:
    root = Path(path).resolve()
    candidate = root / "data" if (root / "data").is_dir() else root
    if not candidate.is_dir():
        raise ValueError("ML-NDT local clone or data directory does not exist")
    return candidate


def _canonical_uuid(value: str) -> str:
    try:
        canonical = str(uuid.UUID(value)).upper()
    except ValueError as exc:
        raise ValueError(f"invalid ML-NDT batch UUID: {value!r}") from exc
    if value != canonical:
        raise ValueError(f"ML-NDT batch UUID is not in canonical provider form: {value!r}")
    return canonical


def _batch_files(data_root: Path, partition: str) -> dict[str, dict[str, Path]]:
    if partition not in {"training", "validation"}:
        raise ValueError("ML-NDT partition must be training or validation")
    directory = data_root / partition
    if not directory.is_dir():
        raise ValueError(f"missing ML-NDT provider partition: {partition}")
    batches: dict[str, dict[str, Path]] = {}
    for path in directory.iterdir():
        if path.is_symlink() and path.suffix in ML_NDT_EXTENSIONS:
            raise ValueError(f"symbolic ML-NDT batch members are not supported: {path.name}")
        if not path.is_file() or path.suffix not in ML_NDT_EXTENSIONS:
            continue
        batch_uuid = _canonical_uuid(path.stem)
        files = batches.setdefault(batch_uuid, {})
        if path.suffix in files:
            raise ValueError(f"duplicate ML-NDT batch member: {path.name}")
        files[path.suffix] = path
    for batch_uuid, files in batches.items():
        missing = ML_NDT_EXTENSIONS - files.keys()
        if missing:
            raise ValueError(f"incomplete ML-NDT batch {batch_uuid}: missing {sorted(missing)}")
    return batches


def list_ml_ndt_batches(
    path: str | Path,
    *,
    repository_revision: str,
    require_pinned_revision: bool = True,
) -> dict:
    """Inventory complete batch quartets without opening binary image payloads."""
    if require_pinned_revision and repository_revision != ML_NDT_PINNED_REVISION:
        raise ValueError("ML-NDT local clone revision does not match the pinned source")
    if not re.fullmatch(r"[a-f0-9]{40}", repository_revision):
        raise ValueError("ML-NDT repository revision must be a full lowercase commit hash")
    root = _data_root(path)
    partitions = {}
    for partition in ("training", "validation"):
        batches = _batch_files(root, partition)
        partitions[partition] = [
            {
                "batch_uuid": batch_uuid,
                "filenames": {suffix.removeprefix("."): files[suffix].name for suffix in sorted(files)},
                "source_bytes": {
                    suffix.removeprefix("."): files[suffix].stat().st_size for suffix in sorted(files)
                },
            }
            for batch_uuid, files in sorted(batches.items())
        ]
    return {
        "dataset_id": ML_NDT_DATASET_ID,
        "repository_revision": repository_revision,
        "revision_basis": "caller_verified_local_clone",
        "partitions": partitions,
        "batch_count": sum(len(rows) for rows in partitions.values()),
        "qualification": "augmented images are not independent physical specimens or flaws",
    }


def _read_text(path: Path) -> str:
    if path.stat().st_size > MAX_SIDECAR_BYTES:
        raise ValueError(f"ML-NDT sidecar exceeds safety limit: {path.name}")
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"ML-NDT sidecar is not UTF-8 text: {path.name}") from exc


def _parse_meta(text: str) -> tuple[str, int, int, int]:
    match = _META.fullmatch(text)
    if match is None:
        raise ValueError("unsupported ML-NDT meta format")
    return (
        match.group("dtype"),
        int(match.group("rows")),
        int(match.group("columns")),
        int(match.group("images")),
    )


def _concatenated_json(text: str) -> list[dict]:
    decoder = json.JSONDecoder()
    records: list[dict] = []
    offset = 0
    while True:
        while offset < len(text) and text[offset].isspace():
            offset += 1
        if offset == len(text):
            return records
        try:
            record, end = decoder.raw_decode(text, offset)
        except json.JSONDecodeError as exc:
            raise ValueError("invalid concatenated ML-NDT JSON metadata") from exc
        if not isinstance(record, dict):
            raise ValueError("each ML-NDT metadata record must be a JSON object")
        records.append(record)
        offset = end


def _finite_nonnegative(value: str, *, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"ML-NDT {field} must be numeric text") from exc
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"ML-NDT {field} must be finite and nonnegative")
    return number


def _optional_number(fields: dict[str, str], name: str) -> float | None:
    return _finite_nonnegative(fields[name], field=name) if name in fields else None


def _parse_flaws(record: dict) -> tuple[MlNdtFlawMetadata, ...]:
    if set(record) != {"flaws"} or not isinstance(record["flaws"], list):
        raise ValueError("ML-NDT metadata record must contain only a flaws list")
    flaws = []
    for raw in record["flaws"]:
        if not isinstance(raw, dict) or any(not isinstance(key, str) for key in raw):
            raise ValueError("ML-NDT flaw metadata must be a JSON object with string keys")
        fields = {key: value for key, value in raw.items() if isinstance(value, str)}
        if len(fields) != len(raw):
            raise ValueError("ML-NDT flaw metadata values must remain provider strings")
        flaws.append(
            MlNdtFlawMetadata(
                raw_fields=fields,
                source_flaw_size_value=_optional_number(fields, "size"),
                equivalent_flaw_size_value=_optional_number(fields, "equivalent_flawsize"),
                augmentation_factor_value=_optional_number(fields, "factor"),
            )
        )
    return tuple(flaws)


def _parse_labels(text: str) -> list[tuple[int, float]]:
    labels = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        fields = line.split("\t")
        if len(fields) != 2 or fields[0] not in {"0", "1"}:
            raise ValueError(f"invalid ML-NDT label row {line_number}")
        labels.append((int(fields[0]), _finite_nonnegative(fields[1], field="equivalent label size")))
    return labels


def read_ml_ndt_batch(
    path: str | Path,
    partition: Literal["training", "validation"],
    batch_uuid: str,
    *,
    repository_revision: str,
    require_pinned_revision: bool = True,
) -> MlNdtBatchAudit:
    """Validate and audit one batch; binary bytes are hashed but not loaded into memory."""
    inventory = list_ml_ndt_batches(
        path,
        repository_revision=repository_revision,
        require_pinned_revision=require_pinned_revision,
    )
    del inventory
    canonical_uuid = _canonical_uuid(batch_uuid)
    files = _batch_files(_data_root(path), partition).get(canonical_uuid)
    if files is None:
        raise KeyError(f"ML-NDT batch not found in {partition}: {canonical_uuid}")
    dtype, rows, columns, image_count = _parse_meta(_read_text(files[".meta"]))
    if require_pinned_revision and (rows, columns, image_count) != ML_NDT_PROVIDER_SHAPE:
        raise ValueError("pinned ML-NDT batch shape differs from the reviewed provider format")
    expected_binary_bytes = rows * columns * image_count * np.dtype(np.uint16).itemsize
    if files[".bins"].stat().st_size != expected_binary_bytes:
        raise ValueError("ML-NDT binary size does not match the declared UInt16 shape")
    label_values = _parse_labels(_read_text(files[".labels"]))
    metadata = _concatenated_json(_read_text(files[".jsons"]))
    if len(label_values) != image_count or len(metadata) != image_count:
        raise ValueError("ML-NDT labels and JSON records must align with the declared image count")

    labels = []
    mismatch_count = 0
    for image_index, ((hit, equivalent_size), record) in enumerate(zip(label_values, metadata, strict=True)):
        flaws = _parse_flaws(record)
        metadata_sizes = [
            flaw.equivalent_flaw_size_value for flaw in flaws if flaw.equivalent_flaw_size_value is not None
        ]
        metadata_size = metadata_sizes[0] if len(metadata_sizes) == 1 else None
        matches = metadata_size is not None and math.isclose(
            equivalent_size, metadata_size, rel_tol=0.0, abs_tol=1e-12
        )
        mismatch_count += int(not matches)
        labels.append(
            MlNdtImageLabel(
                image_index=image_index,
                provider_hit_label=hit,
                provider_equivalent_size_value=equivalent_size,
                metadata_equivalent_size_value=metadata_size,
                label_metadata_size_match=matches,
                flaws=flaws,
            )
        )

    names = {suffix.removeprefix("."): files[suffix].name for suffix in sorted(files)}
    hashes = {suffix.removeprefix("."): _sha256(files[suffix]) for suffix in sorted(files)}
    sizes = {suffix.removeprefix("."): files[suffix].stat().st_size for suffix in sorted(files)}
    return MlNdtBatchAudit(
        repository_revision=repository_revision,
        provider_partition=partition,
        batch_uuid=canonical_uuid,
        source_filenames=names,
        source_sha256=hashes,
        source_bytes=sizes,
        dtype_token=dtype,
        rows=rows,
        columns=columns,
        image_count=image_count,
        labels=tuple(labels),
        metadata_size_mismatch_count=mismatch_count,
    )


def read_ml_ndt_image(
    path: str | Path,
    batch: MlNdtBatchAudit,
    image_index: int,
    *,
    byte_order: Literal["little", "big"],
) -> np.ndarray:
    """Read one copied image after an explicit byte-order decision and digest recheck."""
    if not 0 <= image_index < batch.image_count:
        raise IndexError("ML-NDT image index is outside the audited batch")
    files = _batch_files(_data_root(path), batch.provider_partition).get(batch.batch_uuid)
    if files is None:
        raise KeyError(f"audited ML-NDT batch is no longer present: {batch.batch_uuid}")
    binary = files[".bins"]
    if _sha256(binary) != batch.source_sha256["bins"]:
        raise ValueError("ML-NDT binary digest changed after the batch audit")
    dtype = np.dtype("<u2" if byte_order == "little" else ">u2")
    pixels = batch.rows * batch.columns
    with binary.open("rb") as stream:
        stream.seek(image_index * pixels * dtype.itemsize)
        data = np.fromfile(stream, dtype=dtype, count=pixels)
    if data.size != pixels:
        raise ValueError("ML-NDT binary ended before the requested image was complete")
    return data.reshape((batch.rows, batch.columns), order="C").copy()
