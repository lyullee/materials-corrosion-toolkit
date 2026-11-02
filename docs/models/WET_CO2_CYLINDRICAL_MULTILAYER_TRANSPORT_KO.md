# 원통형 다층 스케일의 방사 확산 저항

## 목적과 API

`integration.wet_co2_cylindrical_multilayer_transport_resistance`는 기존 cylindrical geometry 이력에 있는 상별 몰 재고를 지정된 방사 순서의 환형 상으로 해석하고, 각 상과 용액막의 확산저항을 직렬 합산한다.

- 입력: `WetCo2CylindricalMultilayerTransportResistance`
- knot 입력: `WetCo2CylindricalMultilayerTransportKnot`
- 실행: `evaluate_wet_co2_cylindrical_multilayer_transport_resistance(request)`
- catalog 명세: `specifications()`

각 knot는 geometry의 모든 시간점에 정확히 맞아야 한다. 각 상·용질 조합과 각 용액막 용질에 대해 양의 확산계수를 제공한다. 계수, 용액막 두께와 시간점을 묶은 digest는 사용 허가 정보가 있는 `Evidence`가 고정한다. 모든 확산계수는 knot별 piecewise constant로 사용된다.

## 계산식

강재 표면에서 보어 방향으로 상 층을 배치한다. 상별 선재고와 몰부피로 상의 부피/길이를 산정하고 환형 경계를 복원한다. 양의 경계 반지름이 유지되고 각 층을 모두 합친 반지름이 geometry의 보어 반지름과 일치해야 한다.

원통 반지름 `r_o`에서 `r_i`까지 확산계수 `D`가 일정한 층에 대해 로그형 방사 저항 항은 `ln(r_o/r_i)/D`다. 모든 상과 용액막 항을 합한 뒤 보어 반지름 `r_b`를 곱해 보어 면적 기준 저항 `R = r_b Σ ln(r_o/r_i)/D`를 계산하고, 전달계수는 `k = 1/R`로 반환한다. 상별 및 용액막별 기여도를 함께 출력한다.

## 범위 제한

이 모듈은 정상상태 1차원 원통 확산 저항만 계산한다. 입력 확산계수를 추정하지 않고 화학종의 농도, 반응, 전류, 부식률, 시간 적분을 계산하지 않는다. 층은 조밀하고 연속적이며 원주 전체를 덮고, 사용자가 지정한 방사 순서를 따른다고 가정한다. 다공도, 균열, 박리, 불균일 두께, 대류, 반응-확산 결합은 포함하지 않는다. 시간점 사이의 보간과 혼합전위 계산기로의 자동 전달도 제공하지 않는다.

## 출처·계보·검증 상태

출처 식별자는 `degradation.wet_co2_cylindrical_scale_geometry_history`, `caller_cylindrical_phase_solution_diffusivity_records`, `cylindrical_multilayer_radial_diffusion_resistance`다. 결과는 전체 입력/geometry/매 knot별 확산계수 기록 해시를 보존한다. 이는 선언된 입력과 수학적 해의 계보를 표시하며 물성의 실험적 타당성이나 데이터 사용 권리를 대신 입증하지 않는다.

코드와 이 문서를 추가했으며 검증은 수행하지 않았다. 후속 검증은 단일 용액막 한계, 단일 scale층 해석해, 동일 확산계수 층을 합친 동등층, 층 순서 변경에 따른 상별 기여 이동 및 0 inventory 상 처리, 보어 반지름 폐쇄/소진 거부, 입력 digest 위변조 거부를 다뤄야 한다.
