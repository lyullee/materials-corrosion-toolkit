# 침전 유래 간극 이력과 크리비스 수송 geometry 연결

## 목적

`crevice_deposition_aperture_history` 결과의 셀별 면적 평균 등가 간극 이력을 기존 `CreviceGeometryTransportCampaign`이 받는 planar-slit geometry-history 계약으로 변환한다. 입력은 이미 계산된 침전 고체 체적과 geometry를 사용하며, 여기서는 새로운 침전/유동 물리식을 풀지 않는다.

이 연결을 통해 caller는 다음 operator-split 흐름을 구성할 수 있다.

1. 셀별 고체 inventory를 solid volume per reference area로 변환한다.
2. reviewed face count와 coverage geometry에서 면적 평균 remaining gap을 계산한다.
3. 이 module에서 slit cell/face cross sections와 wall-area density를 만들어 `geometry_history` 및 digest를 얻는다.
4. `geometry_history`와 `geometry_history_sha256`를 `CreviceGeometryTransportCampaign` 입력에 전달하고 정확한 동일 knot에서 각 fixed-geometry transport interval을 계산한다.

이 체인은 순차 계산이다. 고체 침전과 수송을 동시에 결합한 moving-boundary solver를 뜻하지 않는다.

## 입력/출력

Python 모듈: `matintegrity.crevice_deposition_transport_geometry`

- 입력 계약: `CreviceDepositionTransportGeometryRequest`
- 평가 함수: `evaluate_crevice_deposition_transport_geometry()`
- ModelSpec 함수: `specifications()`
- 모델 ID: `integration.crevice_deposition_transport_geometry`
- source ID: `caller_deposition_aperture_to_transport_geometry_mapping`

입력은 `CreviceDepositionApertureHistoryRequest`, 해당 계산의 전체 결과와 SHA-256, downstream geometry 식별자, transport reference cross section, transport 반응 broad face 수(1 또는 2), 그리고 다섯 review gate를 포함한다. Gate는 mean gap을 수송 셀 전체 aperture로 쓰는 것, reference area basis, face-area interpolation, reactive wall area mapping, sequential operator split을 검토한다.

결과의 `geometry_history`는 다음 필드를 포함한다: `geometry_id`, `status`, `cell_count`, `cell_widths_m`, `length_m`, `transverse_width_m`, `reference_cross_section_m2`, `reactive_broad_face_count`, `geometry_states`. 각 state에는 aperture, cell/face cross section, volume, wall area density, upstream source knot와 digest가 기록된다. `geometry_history_sha256`는 이 객체 자체의 canonical digest이며 campaign 입력에 그대로 전달한다.

geometry history는 최소 2개, 최대 5,001개 knot를 지원하고 셀은 최대 2,000개다. 시계는 0에서 시작해야 하며 이후 엄격히 증가해야 한다. downstream campaign은 모든 geometry knot가 transport output clock에 포함되는지, reference cross section와 grid이 일치하는지 별도로 확인한다.

## Geometry mapping

각 셀 단면적은 `cell_aperture_m * transverse_width_m`이다. cell volume은 해당 단면적과 축방향 셀 길이의 곱이다. 내부 face 단면적은 이웃 cell center 사이 선형 보간으로 만들고 양 끝은 가장 가까운 cell 단면적을 사용한다. Reactive broad wall area는 `face_count * transverse_width * cell_length`; wall area density는 이 면적을 cell volume으로 나눈 값이다.

입력된 `transport_reference_cross_section_m2`는 고체 체적 기준 면적과 같다고 자동으로 가정하지 않는다. downstream transport 요청의 reference area와 같도록 caller가 직접 정렬해야 한다. 반응 벽 면 수 역시 deposition side count와 같다고 자동 설정하지 않으므로 각각 검토한다.

## 제한

이 bridge는 이전 단계에서 계산한 면적 평균 aperture를 수송 셀의 균일 aperture로 사용한다. 부분 coverage의 분포, 덩어리/다공성 scale, 접착, 표면 거칠기, 각 벽의 비대칭을 복원하지 않는다. 시간 구간 중 geometry 변화는 downstream campaign의 operator split 규칙을 따른다. 압력-유량, transient momentum, phase kinetics, solid redistribution, 수송과 geometry의 동시 수렴, 부식률 또는 위험도를 이 모듈이 계산하지 않는다.
