# 원통형 스케일의 caller 보정 전단 제거 장부

## 목적과 API

`integration.wet_co2_cylindrical_shear_limited_scale_removal`은 기존 확산 제한 성장 장부에 caller가 보정한 전단응력 임계 제거 법칙을 후처리로 적용한다. 감사에서 남은 scale adhesion/morphology 범위 중 한 가지 한정된 제거 시나리오만 표현하며, 일반적인 박리 모델이라고 주장하지 않는다.

- 요청 계약: `WetCo2CylindricalShearLimitedScaleRemoval`
- 전단 Knot 계약: `WetCo2ScaleShearKnot`
- 실행: `evaluate_wet_co2_cylindrical_shear_limited_scale_removal(request)`
- 카탈로그 명세: `specifications()`

전단력은 caller가 각 geometry 시간점에 Wall shear stress로 공급한다. threshold `tau_c`, 속도 scale `v_c`, 지수 `n`을 함께 설정하고, law 전체 digest와 라이선스가 있는 Evidence를 붙인다. 같은 계산에는 선택 고체상, 정확히 일치하는 cylindrical geometry result, 그리고 앞 단계 diffusion-limited scale growth ledger가 필요하다.

## 계산 경로

caller가 정한 power law를 사용한다.

- `tau <= tau_c`: 제거 속도는 0
- `tau > tau_c`: `v_det = v_c (tau/tau_c - 1)^n`
- 선택 상의 몰부피를 이용해 `J_det = v_det / V_m`으로 면적당 몰 제거율을 계산한다.

시간 knot의 성장 ledger 증분을 먼저 더하고, 전단 제거율을 다음 knot까지 왼쪽 고정 속도로 적용한다. 축방향 단위 길이에 대한 요청 제거량은 `J_det × 2π r_b × Δt`다. 실제 제거량은 적용 시점의 상 재고보다 커질 수 없으며 재고가 소진되면 제거를 해당량에서 제한한다. 반환에는 요청/실제 제거량, 상 재고, 성장 증가량 및 입력 geometry 상 재고와의 차이가 들어간다.

## 가정과 제한

임계전단응력, 속도계수와 지수는 반드시 재료·scale·운전조건에 맞는 caller 보정자료로 입력해야 한다. 이 코드는 이들을 추론하거나 공개된 보편 상수로 제시하지 않는다. 결과는 보정법의 적합성을 확인하지 않으며, 부착력·기공·균열·박리 조각 크기·유체 난류·입자 충돌·scale 재부착·제거물 화학을 계산하지 않는다.

이 후처리는 성장률 계산을 교체하지 않으며, 제거된 scale을 유체나 재료 질량수지로 이동시키지 않는다. transport coefficient, saturation, kinetics, layer order 및 geometry를 재계산하지 않는다. 따라서 결과는 caller 지정 geometry 위의 operator-split inventory 진단이고, 부식/침식 수명·보호성능 또는 건전성 판정으로 해석할 수 없다.

## 계보 및 검증 상태

source IDs: `caller_cylindrical_diffusion_limited_scale_growth_ledger`, `caller_wall_shear_history`, `caller_calibrated_shear_scale_detachment_law`. geometry와 growth result 해시, 계수 record 해시 및 knot별 shear record 해시를 유지한다.

코드와 문서를 추가했으며 테스트·패키징·HPC 검증은 수행하지 않았다. 후속 검증에는 임계치 이하 무제거, 임계치 직상/고응력 응답, 지수 및 속도계수 차원성, 단계별 유한 재고 고갈 cap, 성장과 제거 순서, exact-knot/geometry digest mismatch, 축방향 단위길이 단위 점검이 포함되어야 한다.
