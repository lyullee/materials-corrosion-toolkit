# 원통형 wet-CO2 보어의 정상 단상 hydraulics

## 목적과 API

`integration.wet_co2_cylindrical_steady_hydraulics`는 이미 계산된 원통형 bore geometry와 caller의 단상 유량/유체 물성 기록으로 knot별 관내 평균유속, Reynolds 수, Darcy 마찰계수, 구간 압력손실, 벽 전단응력을 계산한다. wet-CO2 모델의 단상 관내 흐름에 대한 보조 기초량을 만들며 다상 CO2 부식 해석을 대신하지 않는다.

- 계약: `WetCo2CylindricalSteadyHydraulics`
- knot 계약: `WetCo2CylindricalHydraulicKnot`
- 평가 함수: `evaluate_wet_co2_cylindrical_steady_hydraulics`
- 카탈로그 명세: `specifications()`

유량은 부호 있는 체적유량이다. 밀도, 점도, 조도, 유량은 geometry 각 knot에 맞춰 정확히 제공하고, 각 묶음 record는 SHA256과 사용 허가 Evidence로 고정한다. geometry 결과도 원 요청의 digest를 검증한다. 단위 검산과 property provenance는 caller 책임이다. 현재 CoolProp 연동은 순수 물의 포화 수증기 fugacity API이며, 이 계산에 필요한 일반 유체 밀도·점도 속성 API를 제공하지 않으므로 자동 호출하지 않는다. CoolProp에서 독립 추출한 속성은 caller가 자체 provenance와 함께 입력할 수 있다.

## 식과 영역

보어 반지름을 `r`, 지름을 `D=2r`, 단면적을 `A=πr²`, signed 체적유량을 `Q`라 두면 평균 속도는 `u=Q/A`, Reynolds 수는 `Re=ρ |u| D/μ`다. Darcy–Weisbach 식으로 구간 압력손실 크기를 계산한다.

- 층류 `Re ≤ 2300`: Darcy factor `f_D=64/Re`
- 난류 `Re ≥ 4000`: caller의 상대조도에 대해 Colebrook–White implicit 식을 유한 반복/bisection으로 푼다.
- 전이 `2300 < Re < 4000`: 미지원 영역으로 구간 계산을 fail-closed 처리한다.

구간 압력손실은 `ΔP=f_D(L/D)ρu²/2`이며 부호는 흐름 방향을 따른다. 반환하는 signed 벽 전단응력도 흐름 방향을 양의 부호로 두고 `τ=f_Dρu²/8`의 크기에 방향 부호를 붙인다. 반전 흐름 knot에서도 평균 속도와 압력 부호를 보존한다.

## 제한

이 계산은 caller가 review한 단상, 원형 직관, 정상 완전발달 관내 흐름을 가정한다. 전이 Re 범위는 임의 보간하지 않는다. 액체/기체 동시 흐름, 용해 CO2 포함 혼합물 물성, 압축성, 상변화, 유체 가속, 고도 차, 곡관·밸브·축소 확대 손실, transient momentum, 침전으로 변하는 roughness를 다루지 않는다. 벽 전단응력은 단면 평균 흐름 기술량으로 scale 부착/박리 법칙이나 부식률이 아니다.

## 계보와 검증 상태

source IDs: `caller_wet_co2_cylindrical_geometry_result`, `caller_single_phase_density_viscosity_roughness_flow_record`, `darcy_weisbach_laminar_colebrook_pipe_flow`. 출력은 geometry result 해시와 knot별 caller property digest를 보존한다. 구현과 문서만 작성했으며 테스트/패키징/HPC 검증을 실행하지 않았다. 후속 검증에는 층류 Hagen–Poiseuille 일치, 난류 Colebrook residual, 유량 방향 반전 부호, 영유량, 조도/지름 경계, knot digest/geometry 불일치, 전이영역의 fail-closed, 단위 차원 및 pressure/shear 독립 재계산이 포함돼야 한다.
