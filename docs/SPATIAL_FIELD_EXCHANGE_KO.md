# 검토된 직교 공간장 교환·표본화

`matintegrity.spatial_fields`는 큰 2차원 수치 배열을 JSON 안에 복제하지 않고, 별도로 전달된 배열을 검토된 메타데이터와 SHA-256으로 결속한다. 서로 다른 영상·표면형상·응력·변형률·두께 격자를 연결할 때 좌표나 정합을 추측하지 않는 것이 목적이다.

## 공개 계약

- `RectilinearFieldMetadata`: 물리 시편, source group, 원자료와 배열·결측 mask 해시, 물리량·단위·해석 근거, 좌표계·축·좌표 근거, 관측 시점과 결측 의미를 보존한다. 배열 shape은 반드시 `(y축 길이, x축 길이)`다.
- `PlanarAffineCoordinateTransform`: query 좌표를 source field 좌표로 직접 보내는 검토된 2차원 affine 변환이다. 좌표계 방향, 변환 근거와 `registration_reviewed=True`를 명시해야 한다.
- `RectilinearFieldSamplingRequest`: 점 ID와 좌표 순서, `nearest` 또는 `bilinear`, 지원영역 밖과 결측 support의 `reject` 또는 `return_missing` 정책을 고정한다.
- `RectilinearFieldSamplingResult`: 실제 source-frame 좌표, 값 또는 명시적 결측 상태, 사용한 배열·mask 해시와 변환 근거를 반환한다.

`numeric_array_digest`는 배열의 dtype, shape, C-order 바이트를 함께 해시한다. dtype 변경이나 reshape도 다른 입력으로 취급한다. `sample_rectilinear_field`는 배열과 Boolean 결측 mask의 shape·해시·유한값을 확인하고 요청한 점만 표본화한다.

```python
import numpy as np

from matintegrity.spatial_fields import (
    RectilinearFieldMetadata,
    RectilinearFieldSamplingRequest,
    numeric_array_digest,
    sample_rectilinear_field,
)

values = np.array([[0.10, 0.12], [0.14, 0.16]])
missing = np.zeros(values.shape, dtype=bool)
metadata = RectilinearFieldMetadata(
    field_id="scan-01-height",
    physical_specimen_id="coupon-01",
    source_group_id="campaign-01",
    source_sha256="a" * 64,
    array_sha256=numeric_array_digest(values),
    missing_mask_sha256=numeric_array_digest(missing),
    quantity_name="surface_height",
    quantity_unit="m",
    quantity_basis="reviewed instrument export",
    coordinate_frame_id="stage-frame-01",
    coordinate_basis="reviewed stage coordinates",
    observation_clock="exposure day 2",
    x_coordinates_m=(0.0, 0.001),
    y_coordinates_m=(0.0, 0.001),
    value_shape=(2, 2),
    missing_value_meaning="True marks unavailable source support",
)
request = RectilinearFieldSamplingRequest(
    query_id="q-01",
    query_frame_id="stage-frame-01",
    point_ids=("centre",),
    x_coordinates_m=(0.0005,),
    y_coordinates_m=(0.0005,),
    interpolation="bilinear",
    outside_support_policy="reject",
    missing_support_policy="reject",
    interpolation_review_basis="bilinear interpolation accepted for this field",
)
result = sample_rectilinear_field(values, missing, metadata, request)
```

## 의도적인 중지 조건

좌표계가 다르면 호출자가 검토한 direct transform을 제공해야 한다. 배열 크기, index 범위, 변수명이나 그림의 유사성으로 scale·이동·회전을 자동 추정하지 않는다. 같은 좌표계라고 선언한 경우에도 불필요한 변환은 받지 않는다. 지원영역 밖이나 결측 source support는 정책에 따라 즉시 거절하거나 숫자 대신 상태와 `None`을 반환한다.

이 인터페이스는 정합 품질, 보간법의 물리적 타당성, 측정 불확실성이나 공간분해능을 인증하지 않는다. 임계값으로 pit을 분할하거나 깊이 부호를 정하지 않으며, 두 시점 차이·성장률·전이확률·POD·잔여수명·합격판정을 만들지 않는다. 그런 해석은 별도의 검토된 공급자와 독립 검증이 필요하다.

## AA7050 자료 적용 상태

현재 확보한 AA7050 Specimen 01의 morphology·strain·stress 배열은 shape이 서로 다르다. 공개 파일에서 좌표축·단위·높이 부호·시점 간 또는 물리량 간 정합 변환을 확정하지 못했으므로 이 인터페이스에 임의 좌표를 넣지 않는다. 이후 원 계측 좌표나 검토된 등록 근거가 확보되면 각 배열의 메타데이터와 transform을 별도 작성하고 해시로 결속한다. 이 API의 존재 자체는 해당 자료가 정합되었거나 물리 검증되었다는 뜻이 아니다.

전용 검사는 `tests/test_spatial_fields.py`에 있다. 공개 JSON Schema는 `scripts/export_schemas.py`로 다시 만든다.
