# 원통형 wet-CO₂ BV 금속 용출량에서 보어 반경으로의 exact-knot 전달

## 목적

`integration.wet_co2_cylindrical_bv_wall_recession`은 계산 완료된 `integration.wet_co2_cylindrical_spatial_mixed_potential` 결과의 반응 extent를 원소별 금속 용출량으로 환산하고, 그 누적 질량이 원통 관벽에서 차지하던 부피를 빼서 보어 반경 이력을 재구성합니다. 기존 공간 혼합전위 계산과 원통 scale geometry 입력을 digest로 결합해 동일 knot에서 계산값이 geometry 이력과 일치하는지 확인합니다.

## 기하 및 보존식

공간 혼합전위 모델은 원소 조성이 선언된 수용액 종과 반응별 stoichiometric coefficient, interval별 net reaction extent를 제공합니다. wall 원소 `e`의 반응당 용출 계수는 수용액 반응 조성에서 해당 원소가 순증가하는 양으로 계산합니다.

```text
yield[e, reaction] = sum(species_stoich * species_atoms[e])
release[e, interval] = sum(yield[e, reaction] * extent[reaction, interval])
mass_per_length = sum(cumulative_release[e] * atomic_molar_mass[e])
removed_area_per_length = mass_per_length / wall_density
r[k] = sqrt(r[0]^2 + removed_area_per_length / pi)
```

모든 inventory는 관축 길이 1 m당 값입니다. 따라서 `mass_per_length / density`는 단위 축 길이당 제거 체적이며, 원통의 정확한 annular volume identity `pi (r_k^2-r_0^2)`와 직접 연결됩니다. 구간마다 방출 원소 inventory를 누적한 뒤 반경을 계산합니다.

## 추적성과 거부 조건

- 원래 spatial 요청 전체 digest, 계산 결과 digest, nested geometry 요청 digest 및 자산·위치·시간축 lineage를 유지합니다.
- reaction ID 집합은 각 source interval의 exact left-knot BV branch 집합과 같아야 합니다.
- source 결과는 계산 완료 상태여야 하며 각 원소량은 해당 반응 조성식으로 다시 산출합니다.
- 반응 extent가 음수이거나 wall 원소 순유입이 생기는 경우, 용출 매핑이 없는 반응, 물질 조성 합이 1이 아닌 경우, 밀도·원소량이 관벽을 완전히 제거하는 경우는 범위 밖으로 처리합니다.
- 유도된 반경은 caller가 제공한 exact-knot geometry의 반경과 caller 오차한도 내에서 일치해야 합니다. 일치하지 않으면 원인을 숨기지 않고 해당 knot와 잔차를 반환합니다.

## 적용 한계

- 이 계산은 이미 수행한 spatial electrochemical history를 원통 반경에 연결하고 검토하는 one-way replay입니다. 새 반경으로 transport와 전극 반응을 재계산하는 반복 solver가 아닙니다.
- 시간 knots 사이의 geometry는 계산하지 않고, BV 환경변수와 reaction parameters는 선행 계산에서 사용한 caller calibration에 한정됩니다.
- 벽은 균일 조성·일정 밀도·축대칭·균일 침식으로 가정합니다. pit, 국부 부식, 방향성, scale로 인한 유효 단면 변화, 합금 선택 용출 또는 금속 재침적은 다루지 않습니다.
- net reaction extent가 비음수여도 반응식·전극 kinetic calibration이 물리적으로 타당하거나 재료가 자격평가되었다는 뜻은 아닙니다.
- 결과는 잔여 벽두께 안전성, 압력용기 코드 적합성, 부식수명 또는 신뢰도를 평가하지 않습니다.

## API 계약

- 모듈: `matintegrity.wet_co2_cylindrical_bv_wall_recession`
- 모델 ID: `integration.wet_co2_cylindrical_bv_wall_recession`
- 스키마: `matintegrity.wet_co2_cylindrical_bv_wall_recession.v1`
- 입력: `WetCo2CylindricalBVWallRecession`
- 평가기: `evaluate_wet_co2_cylindrical_bv_wall_recession(request)`
- 메타데이터: `specifications()`
- source ID: `computed_bv_alloy_element_release_to_cylindrical_recession`, `caller_calibrated_butler_volmer_reaction_set`, `caller_wet_co2_initial_cylindrical_pipe_geometry`
- Registry·schema·capability/source catalog 연결은 완료했습니다. 수치 검증과 package build는 보류 중입니다.
