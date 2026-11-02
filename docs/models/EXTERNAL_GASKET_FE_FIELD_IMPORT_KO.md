# 외부 FE 가스켓 접촉·응력 결과 가져오기

## 목적 및 경계

`integration.external_gasket_fe_field_import`는 이미 외부 구조/FE solver가 계산해 receipt에 고정한 결과 배열을 검증하고 gasket spatial-contact 출력 규약에 맞춰 전달합니다. 이 모듈은 FE 해석을 실행하거나 재현하지 않습니다. 수치해석기마다 다른 파일 포맷은 caller/provider parser가 공용 계약으로 변환해 제공해야 합니다.

한 개 이상의 정렬된 snapshot을 입력할 수 있습니다. 각 snapshot은 FE receipt, load case ID, solver step ID, 정확한 시간 바인딩, field 선택별 정규화 값 및 선택적 support 조건 기록으로 구성합니다. 모든 snapshot은 같은 asset/location/physical scope, component, provider·solver revision과 exact mesh digest를 가져야 하며, 시간이 엄격히 증가해야 합니다.

## 명시적으로 받는 FE 결과 필드

선택 필드는 receipt에 실제로 존재하는 `field_id`, `quantity_id`, 정확한 quantity definition, 단위, node/element/face 결과 위치 및 component 순서에 일치해야 합니다.

- `gasket_normal_contact_pressure`: 스칼라 `Pa`
- `gasket_normal_contact_force`: 스칼라 `N`
- `gasket_contact_gap`: 스칼라 `m`
- `gasket_compression`: 스칼라 `m`
- `gasket_stress_tensor`: 사용자가 선언한 component 순서의 6성분 `Pa`

모든 선택 필드는 한 snapshot에서 같은 결과 위치 체계와 mapping을 사용합니다. 각 provider location은 정확히 하나의 caller `contact_node_id`에 연결됩니다. 셀/face 식별자는 외부에서 명시적으로 mapping할 수 있지만, 이 API가 인접 node로 자동 보간·평균하거나 공간좌표 근접값으로 대응하지 않습니다. 현 계약은 integration-point 데이터 또는 복수 FE 결과를 한 field로 평균내는 작업을 지원하지 않습니다.

압력은 실제 단위 `Pa`, 힘은 `N`, gap·compression은 `m`만 받습니다. 응력 텐서는 선언 component 순서 그대로 보존합니다. Von Mises 등가응력, principal stress, 코드 응력강도 또는 acceptance를 계산하지 않습니다.

## Contact 결과 배선

각 contact location에는 caller tributary area와 원주 좌표가 필요합니다. provider normal force field가 있으면 해당 힘을 보존합니다. force field가 없고 pressure field가 있을 때에만 `pressure × caller tributary_contact_area_m2`를 계산해 lumped contact force를 생성합니다. 이 곱은 FE solver가 계산한 면적 적분과 동등하다고 자동 가정하지 않으며, tributary area mapping과 projection basis에 대한 별도 검토가 필수입니다.

pressure field 없이 force만 제공되면 `force / area`를 평균 접촉압력으로 계산합니다. 둘 다 제공되면 둘 다 원자료 값으로 출력하고, 자동으로 서로 대체하거나 일치 판정에 사용하지 않습니다. 출력 `response_field`는 기존 gasket contact/spatial resultant 출력에서 사용하는 `node_id`, `contact_force_N`, `mean_contact_pressure_Pa`, `contact_area_m2`, `contact_gap_m`, `gasket_compression_m`, `gasket_stress_components_Pa` 필드를 사용합니다. 한 snapshot 입력은 `node_ids`와 `gasket_contact_area_m2`를 기존 contact result input 이름으로 보존하므로, 이후 중앙 consumer가 import model ID를 허용하면 `gasket_joint_spatial_resultants`의 contact 쪽 field로 연결할 수 있습니다.

여러 snapshot history는 정확한 시간 knot마다 원래 solver step ID, receipt digest, field record digest, normalized array digest와 support record를 보존합니다. 시간 보간을 하지 않습니다. 다중 시점 결과를 joint resultant에 전달할 때는 같은 exact time의 결과만 별도로 선택해야 합니다.

## Receipt, digest 및 support data

각 field의 raw provider array content digest는 FE result field receipt와 같아야 합니다. 이 API는 caller가 parser에서 정규화한 수치 배열, provider location ID 순서, component ID 순서 및 raw array digest를 묶어 `normalized_values_sha256`을 다시 계산합니다. 따라서 원래 파일/solver receipt, field parser output, normalized data 사이 lineage가 분리되어 남습니다.

solver step에서 실제 시간으로의 대응도 별도 digest/Evidence-bound record입니다. 그 record는 provider ID/revision, analysis ID, load case, step ID 및 `time_s`를 묶습니다. mesh/field coordinate frame과 asset/location/physical scope가 receipt에 연결되지 않거나 배열 shape, unit, location, component 또는 digest가 다르면 입력이 거부됩니다.

선택 support data는 support ID, mesh node, translational/rotational DOF, prescribed displacement/rotation 및 선택적 reaction을 기록합니다. 각 행은 SI 단위 `m`, `rad`, `N`, `N*m`를 구분합니다. support set digest는 solver mesh digest, load case, step 및 모든 support row를 묶습니다. 이는 provider의 support metadata를 옮기는 것이며 경계조건의 구조적 타당성을 검증하지 않습니다.

## 실행 전 검토

1. provider parser가 결과 field의 실제 array ordering, raw SHA, unit token, result location, component 순서 및 coordinate frame을 보존하는지 확인합니다.
2. 접촉 위치 ID와 gasket patch ID를 1:1로 명시하고, tributary area 및 원주각의 geometry source/digest/license를 고정합니다.
3. receipt의 model/provider revision, mesh content digest, asset/location/scope, load case, selected field record를 확인합니다.
4. 각 solver step과 실제 시간의 대응, contact pressure/force 부호와 averaging basis, 필요 시 pressure-area-force 변환 적용성을 검토합니다.
5. 선택 optional support data는 별도 source/Evidence로 mesh/load step에 결합합니다. 모델 계산, 경계조건 또는 stress adequacy 검토로 오해하지 않습니다.

필요한 review flag 중 하나라도 false면 `needs_data`로 반환합니다. 잘못된 field binding이나 배열 shape/digest는 contract validation error이며, field interpolation이나 임의 단위 변환으로 고치지 않습니다.

## 적용 한계

- provider solver가 접촉·응력·support를 어떻게 계산했는지 이 어댑터가 검사하거나 재계산하지 않습니다. solver verification, mesh convergence, constitutive calibration, contact formulation 및 boundary adequacy는 별도 검증입니다.
- 공간 mapping은 선언된 배열 순서의 direct 1:1 mapping뿐입니다. node↔element 변환, face integration, interpolation, smoothing, component transform 및 stress recovery는 하지 않습니다.
- 압력×면적은 caller가 지정한 patch-average 압력과 tributary 면적을 사용하는 명시적 lumped projection입니다. pressure field의 정확한 적분값을 대신한다고 주장하지 않습니다.
- 응력 component를 그대로 전달할 뿐 응력강도, fatigue hot spot, pressure-vessel code stress, allowable comparison, material integrity 또는 sealing acceptance로 해석하지 않습니다.
- contact state(`closed`/`open`) 표시는 imported normal force가 양수인지 여부로 만든 field label이며 FE 접촉 알고리즘 독립 검증을 뜻하지 않습니다.
- history에는 receipt에 명시적으로 연결된 시간절점만 포함됩니다. 중간 이벤트, 숨은 multiple contact transition, 시간 보간 및 extrapolation을 계산하지 않습니다.
- output은 향후 downstream gasket spatial-resultant adapter를 위한 명시적인 field bundle입니다. 중앙 소비자 등록·형식변환이 완료되기 전에는 기존 `AssessmentResult` 소비 API에 그대로 전달하지 않아야 합니다.

## 독립 자료

- ASME V&V 10, *Standard for Verification and Validation in Computational Solid Mechanics*. 구조해석 모델의 verification/validation 구분을 참고합니다. [ASME 표준 페이지](https://www.asme.org/codes-standards/find-codes-standards/standard-for-verification-and-validation-in-computational-solid-mechanics)
- National Institute of Standards and Technology, “NIST Structural Mechanics Data Format” 및 재현 가능한 데이터/단위 교환 관련 공식 문서. 이 adapter의 raw receipt와 normalized-array lineage를 설계할 때 provider-neutral data exchange 배경만 참고합니다. [NIST Structural Mechanics](https://www.nist.gov/programs-projects/structural-mechanics)
- ASME Digital Collection, L. Zhu, A.-H. Bouzid, and J. Hong, “Numerical and Experimental Study of Elastic Interaction in Bolted Flange Joints,” *Journal of Pressure Vessel Technology*, 139(2), 2017. 별도 FE/시험 검증이 필요한 가스켓 flange 연성 해석의 배경만 참고합니다. [DOI: 10.1115/1.4035316](https://doi.org/10.1115/1.4035316)

이 참고자료의 문장, 결과, 표 또는 FE 데이터를 복사하지 않았습니다. 실제 provider solver 파일/array와 사용권은 caller가 확보하고 보존해야 합니다.

## API 계약

- 모듈: `matintegrity.models.external_gasket_fe_field_import`
- 모델 ID: `integration.external_gasket_fe_field_import`
- 스키마: `matintegrity.external_gasket_fe_field_import.v1`
- 입력: `ExternalGasketFEFieldImportRequest`
- FE field 선택: `GasketFEFieldSelection`
- normalized field array: `GasketFENormalizedFieldArray`
- snapshot: `GasketFEContactSnapshot`
- 평가기: `evaluate_external_gasket_fe_field_import(request)`
- 등록 metadata 함수: `specifications()`
- source ID: `caller_finite_element_gasket_field_receipt_and_normalized_arrays`, `caller_mesh_contact_location_area_and_coordinate_mapping`, `caller_solver_step_time_and_support_boundary_records`
- FE 실행, 중앙 registry/schema/catalog 생성, 계산 검증, package 작업은 포함하지 않습니다.
