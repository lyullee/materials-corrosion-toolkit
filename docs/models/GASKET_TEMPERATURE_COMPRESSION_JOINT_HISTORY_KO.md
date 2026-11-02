# 온도별 가스켓 압축곡선을 결합한 볼트–가스켓 조립 이력

## 목적과 모델 ID

`integration.gasket_temperature_compression_joint_history`는 동일 strain knot의 두 caller 측정 가스켓 압축 loading 곡선 사이를 온도에 대해 선형 보간한 뒤, 여러 볼트와 접촉 섹터가 공유하는 축방향 opening을 각 하중·온도 knot에서 풉니다. 모든 볼트의 초기 체결력은 기준 상태에서 고정해 유지하고, caller bolt 강성·bolt 열 자유 길이 변화·gasket 섹터 열 자유두께 변화와 외부 분리 하중을 함께 적용합니다.

## 계산 관계

각 load step에서 온도 보간률을 계산하고 같은 압축 변형률 knot에서 응력을 구합니다. 공통 opening `o`에 대해 볼트 변위와 sector 압축을 계산합니다.

```text
bolt_extension_i = o - bolt_free_length_change_i
bolt_force_i = max(0, preload_i + axial_stiffness_i * bolt_extension_i)
sector_compression_j = initial_compression_j + gasket_free_thickness_change_j - o
sector_strain_j = sector_compression_j / initial_gasket_thickness
sector_force_j = interpolated_stress(T, sector_strain_j) * sector_area_j
residual(o) = sum(bolt_force) - sum(sector_force) - external_separating_force
```

각 knot의 residual이 caller opening 범위 안에서 0이 되도록 bounded bisection을 사용합니다. 최초 시간 knot는 열 변화와 외부 분리 하중이 0인 조립 기준점으로, bolt preload 합계와 그 온도에서의 sector 초기 gasket 힘 합계가 caller 허용오차 내에서 맞아야 합니다.

## Caller 입력과 검토

- 동일 specimen, material condition, loading branch와 변형률 grid를 가진 두 온도의 측정 stress–strain curves
- 볼트별 초기 체결력, 축강성, 응력면적과 knot별 free-length thermal shift
- sector별 초기 gasket compression, 접촉 면적 및 knot별 free-thickness shift
- 순서가 있는 knot별 온도·시간·외부 분리하중과 opening 해석 범위·수치 허용오차
- curve, geometry, preload, stiffness, 면적, thermal shifts의 공급자 ID/revision/digest/Evidence 및 사용권
- 공통 opening, 선형 온도 보간, 단방향 준정적 경로, 초기 힘 균형 및 compression-only/tension-only 가정 검토

각 knot의 온도는 두 측정 curve 사이에 있어야 하며, compression curve support 밖의 gasket strain이 나오면 외삽하지 않고 `out_of_scope`를 반환합니다.

## 적용 한계

- 각 시간 knot는 독립 준정적 force equilibrium입니다. 시각 사이 동적 응답, impact, 주파수 효과, relaxation/creep, 온도에 따른 기계 이력, hysteresis, 접촉 전이 시각을 계산하지 않습니다.
- flange를 rigid/common-opening assembly로 축약합니다. flange finite-element bending·국부 응력·bolting interaction beyond caller spring stiffness·원주/반경 접촉장 생성은 하지 않습니다.
- 가스켓 loading 응력만 온도 보간합니다. unloading curve, thermal expansion, geometry 변화 및 시험 조건 transfer는 caller free shifts와 review가 있어야 합니다.
- 출력은 조건부 bolt/sector 힘과 평균압력입니다. 누설률, 밀봉 수용기준, 재료 적합성, 코드 승인 및 qualification을 산출하지 않습니다.

## 독립 참고자료

- “Development of Test Equipment for Measuring Compression Characteristics of Sheet Gaskets at Elevated Temperature,” *Journal of High Pressure Institute of Japan* 46(6) (2008). [DOI: 10.11181/hpi.46.363](https://doi.org/10.11181/hpi.46.363)
- H. Willis and A. Fatemi, “An Experimental Investigation of Compressive Behavior of a Gasket Material,” SAE Technical Paper 930119 (1993). [DOI: 10.4271/930119](https://doi.org/10.4271/930119)

이 문헌은 온도 조건별 가스켓 압축 curve 측정과 압축 거동의 실험 배경만 제공합니다. 계산식·계수·curve 데이터는 참고자료에서 가져오지 않았으며 모든 물성은 caller가 별도로 공급해야 합니다.

## API 및 source ID

- Model ID: `integration.gasket_temperature_compression_joint_history`
- Schema: `matintegrity.gasket_temperature_compression_joint_history.v1`
- Evaluator: `evaluate_gasket_temperature_compression_joint_history(request)`
- Source IDs: `caller_gasket_temperature_bracket_loading_curves`, `caller_bolt_preload_stiffness_and_thermal_free_length`, `caller_gasket_sector_area_compression_and_thermal_free_thickness`, `quasi_static_parallel_bolt_gasket_force_equilibrium_with_temperature_curve_transfer`
