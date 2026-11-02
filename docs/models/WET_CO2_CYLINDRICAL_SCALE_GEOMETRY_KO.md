# Wet-CO₂ 원주형 관의 스케일·벽 형상 재구성

## 목적

`degradation.wet_co2_cylindrical_scale_geometry_history`는 이미 계산·검토된 금속 후퇴 이력과 Caller가
제공한 고체상별 길이당 물질량을 사용해 원형 관의 형상을 시간 절점마다 계산한다. 기존 평판형 스케일
두께를 그대로 관 내부로 옮기는 대신, 관형 단면의 면적·부피 보존 관계로 스케일이 차지하는 환형 영역을
정한다.

Python API:

- 요청: `matintegrity.wet_co2_cylindrical_scale_geometry.WetCo2CylindricalScaleGeometryHistory`
- 고체상 사양: `WetCo2CylindricalScalePhase`
- 절점별 재고: `WetCo2ScalePhaseLineInventory`, `WetCo2CylindricalGeometryKnot`
- 계산: `evaluate_wet_co2_cylindrical_scale_geometry_history(request)`
- Model ID: `degradation.wet_co2_cylindrical_scale_geometry_history`

## 독립 산술 정의

초기 관 외반경 Rₒ, 내반경 Rᵢ₀, 벽두께 t₀, 현재 caller 금속 후퇴 δ를 받는다. 이 모델은 외반경을
고정하고 강재 내면이 Rₛ=Rᵢ₀+δ로 이동한다고 둔다. 각 고체상 i의 길이당 몰수 Nᵢ [mol/m]와 몰부피
V̄ᵢ [m³/mol]로 길이당 scale 부피 V′ₛ=ΣNᵢV̄ᵢ [m²]를 계산한다.

```text
remaining_wall = R_o - R_s
bore_radius = sqrt(R_s² - V′_s / π)
scale_thickness_equivalent = R_s - bore_radius
bore_area = π × bore_radius²
bore_wetted_perimeter = 2π × bore_radius
scale_volume_on_segment = V′_s × segment_length
```

계산은 요청에 포함된 정확한 시간 절점에서만 수행한다. 고체상 inventory가 모두 0이면 scale 두께가 0인
기하 상태를 허용한다. 양의 scale 부피가 내경을 0 이하로 만들거나 금속 후퇴로 벽이 소진되면 해당 절점에서
`out_of_scope`를 반환하고 앞서 계산한 상태 prefix를 보존한다.

## 입력과 출처

- 초기 관 반경·벽두께·축방향 구간 길이와 digest에 결합된 geometry Evidence
- 시간 0부터 오름차순인 절점의 금속 후퇴 및 각 상의 길이당 몰수
- 그 순서와 값을 고정하는 SHA-256 및 history Evidence
- 고체상 ID별 caller 몰부피, provider revision, source record ID 및 Evidence
- 원주 방향 균일성·inventory 기준면과 단위를 검토했다는 caller 확인

새 관측값, 재료 표, wet-CO₂ 반응 속도식이나 외부 계산 코드는 사용하지 않는다. 계산 관계는 독립적인
원통 단면 기하·단위 환산에 한정된다. 출처 ID는 `caller_wet_co2_initial_cylindrical_pipe_geometry`,
`caller_wet_co2_wall_recession_and_scale_phase_inventory_history`,
`caller_wet_co2_scale_phase_molar_volume`이다. 각 Evidence가 참조하는 입력 데이터의 사용권한은 호출자가
별도로 확인해야 한다.

## 제한과 연결 경계

- 축대칭 원형 관, 고른 원주 방향 금속 후퇴, 치밀하고 축방향으로 균일한 스케일 환형을 가정한다.
- 금속 후퇴량과 상별 몰재고는 외부 계산·실측에서 제공한다. 이 API가 용해전류, 반응속도, 침전·용해,
  chemistry coupling을 계산하지 않는다.
- 상별 부피는 합산만 한다. 각 상의 방사방향 순서, 층간 공극, 다공도, 균열, 박리, 거칠기와 보호도는
  추론하지 않는다.
- 관 유량, 압력손실, 난류 질량전달, 열전달을 계산하거나 입력 geometry를 downstream solver에 자동
  전달하지 않는다. 결과는 geometry handoff이며 호출자가 후속 적용을 검토해야 한다.
- 절점 사이 보간·시간 적분을 하지 않는다. 부식속도, 잔여수명, 사건확률, 수용기준, 물리 qualification을
  산출하지 않는다.

## 개발·검증 상태

이 API의 코드와 계약 문서만 작성했다. 테스트, package build, 외부 solver 계산 또는 실측 검증을 수행하지
않았으며, geometry 질량보존 산식의 현장 적합성을 확인했다는 의미는 아니다.
