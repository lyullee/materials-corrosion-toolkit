# 외부 가스켓 FE 응력 텐서의 von Mises caller-limit screen

## 목적 및 입력

`integration.gasket_fe_von_mises_caller_limit_screen`은 `integration.external_gasket_fe_field_import`가 전달한 외부 FE 응력 텐서 성분을 재사용해 각 선언 위치·시각의 3D von Mises 등가응력을 계산하고, caller가 명시한 단일 재료상태·온도별 scalar threshold와 비교합니다. 이 모듈은 FE solver를 실행하거나 stress recovery를 수행하지 않습니다.

입력 FE result는 computed `AssessmentResult`여야 하며 원본 전체 digest, asset, location, joint, physical scope, provider component, tensor coordinate frame 및 stress field binding이 일치해야 합니다. tensor component ID와 Cartesian `xx, yy, zz, xy, yz, zx`의 의미는 caller가 명시적으로 bijection mapping합니다. 단위는 `Pa`여야 합니다.

caller limit 레코드는 material condition, 정확한 temperature, asset/joint/scope, limit 및 출처/revision/record ID를 digest에 결합합니다. 이에 대응하는 Evidence는 같은 source ID, limit digest, 사용권 ID를 포함해야 합니다. 이 값은 코드 allowable로 간주하지 않으며 단순 caller-defined 비교 한계입니다.

## 계산 및 출력

각 가져온 대칭 stress tensor를 해당 caller mapping 순서로 재배열하고 deviatoric stress `s`를 구합니다. 기존 J2 stress helper의 invariant 구현을 재사용해 아래 정의의 등가응력 scalar를 계산합니다.

```text
sigma_vm = sqrt(3/2 * s_ij * s_ij)
margin = caller_limit - sigma_vm
utilization = sigma_vm / caller_limit
```

각 location·step별 imported tensor, 등가응력, caller threshold, signed margin, utilization, threshold 관계를 반환합니다. 최대 등가응력 위치·시간은 witness로 표시합니다. `all_locations_at_or_below_caller_limit`는 오직 이 입력 유한 집합에 대한 비교 결과이며 해석 수용 또는 설계 승인 결과가 아닙니다.

## 한계

- 입력은 importer가 그대로 보존한 symmetric six-component stress tensor입니다. 좌표변환, element-to-node extrapolation, averaging/smoothing, stress linearization, hot-spot extraction 또는 mesh refinement 판단은 하지 않습니다.
- equivalent stress는 일반적인 J2/von Mises scalar입니다. 이 API는 이를 가스켓 고유의 실패 법칙, seating 기준, 항복 판정 또는 fatigue criterion으로 지정하지 않습니다.
- caller threshold는 하나의 재료 조건과 고정 온도에 대해서만 적용합니다. 온도 외삽, material transfer, 제조 lot 차이, hardening history, creep, damage 또는 safety factor는 추론하지 않습니다.
- 증분 불확실도, 결과 분포, failure probability, code-based stress category/allowable, sealing acceptance, structural qualification 및 material qualification은 포함하지 않습니다.
- upstream receipt 검증은 배열/field lineage와 명시된 단위를 확인할 뿐 FE 계산 자체의 verification/validation을 증명하지 않습니다.

## 독립 참고자료

- Idaho National Laboratory, MOOSE Framework, `RankTwoScalarTools`: deviatoric tensor로부터 von Mises scalar를 계산하는 일반적인 J2 invariant 정의를 참고합니다. [공식 API 문서](https://mooseframework.inl.gov/releases/moose/2021-05-18/source/utils/RankTwoScalarTools.html)
- “Development of VUMAT and VUHARD Subroutines for Simulating the Dynamic Mechanical Properties of Additively Manufactured Parts,” *Materials*, 15(1), 2022. J2 second deviatoric invariant과 von Mises yield relation 설명을 참고합니다. [PubMed Central](https://pmc.ncbi.nlm.nih.gov/articles/PMC8746190/)

위 자료의 문장, 수치 사례 또는 FE 결과는 복사하지 않았습니다. limit 값, 재료 정의 및 결과 해석은 caller-owned inputs입니다.

## API 계약

- 모듈: `matintegrity.models.gasket_fe_von_mises_caller_limit_screen`
- 모델 ID: `integration.gasket_fe_von_mises_caller_limit_screen`
- 스키마: `matintegrity.gasket_fe_von_mises_caller_limit_screen.v1`
- 입력: `GasketFEVonMisesCallerLimitScreen`
- 성분 매핑: `TensorComponentBinding`
- 평가기: `evaluate_gasket_fe_von_mises_caller_limit_screen(request)`
- source ID: `imported_gasket_fe_stress_tensor_components_and_frame`, `three_dimensional_j2_von_mises_equivalent_stress_invariant`, `caller_material_condition_temperature_and_equivalent_stress_limit`
- importer가 제공하는 field ID·array digest 및 FE receipt lineage를 그대로 연결해야 합니다. 이 API는 별도 solver artifact/parser를 요구하지 않습니다.
