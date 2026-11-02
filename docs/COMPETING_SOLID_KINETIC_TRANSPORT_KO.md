# 경쟁 고체상 kinetics와 공간 수송의 operator-split 연동

`integration.competitive_solid_kinetic_transport`는 기존 `RestrictedTransportRequest`의 수용액 수송 계산과 `chemistry.competitive_solid_kinetic_ledger`의 상별 재고 갱신을 시간 순서로 조합한다. API 입력은 `CompetingSolidKineticTransport`이고 solver는 `solve_competing_solid_kinetic_transport()`다. reaction, tip/wall flux, activity와 time-varying advection callback은 Python에서 별도로 전달한다. Kinetics 입력은 기존의 명시 rate 방식이나 caller 포화도 provider와 phase-specific power law 방식 중 하나를 고른다.

## 시간별 실행

1. 각 transport 구간을 시작 시점 농도장에서 고정 geometry와 기존 boundary/reaction callbacks로 풀이한다.
2. 구간 끝 농도와 해당 cell의 고체 재고를 cell별 kinetics ledger의 초기 상태로 사용한다.
3. 그 구간에 대응하는 caller 제공 phase extent rates를 상별·cell별 상수 rate로 적용한다. rate는 `mol/m3/s`; 양수는 침전, 음수는 용해다.
4. 각 cell의 ledger 결과를 합쳐 다음 transport 구간 초기장, 상별 고체 재고, 누적 액상 생성·소비량을 구성한다.
5. 매 시간 knot에 aqueous inventory = initial inventory + cumulative transport source + cumulative kinetic source 잔차를 계산한다. 오차한계를 벗어나면 `computed`를 반환하지 않는다.

`kinetic_intervals`는 `transport.output_times_s`의 인접 knot와 정확히 일치해야 한다. 종 순서는 수송 입력과 같아야 하며, 각 고체상의 초기 재고와 매 interval rate는 각 셀에 값을 하나씩 제공해야 한다. 캠페인과 설비/시편 영역 식별자는 별도 `campaign_id`와 `physical_scope_id`로 제공한다. 중성 고체의 반응식이 종 ID, 원소 조성 또는 charge에 맞지 않으면 요청 validation에서 거절된다. 온도·provider revision·parameter/configuration 및 조성 데이터 digests는 결과에 남는다.

명시 rate 방식은 기존 `kinetic_intervals`를 그대로 사용한다. 포화도 방식은 `kinetic_intervals`를 비우고 `phase_rate_laws`에 각 고체상 법칙을 하나씩 선언한다. 요청에는 saturation provider ID·revision·configuration SHA-256과 표준상태 검토를 기록한다. Solver에 전달하는 callback 형식은 `saturation_ratios(global_time_s, cell_index, aqueous_concentration_mol_m3, solid_inventory_mol_m3_by_phase)`다. 농도 벡터의 species order는 `transport.species_ids`, 고체 재고 map은 반응망 phase ID를 따른다. callback은 모든 phase ID에 대한 finite nonnegative dimensionless saturation ratio를 반환하고, 함수 객체의 `configuration_sha256` 속성은 요청에 적힌 digest와 일치해야 한다.

기존 활동도 provider와 source-backed Ksp screen을 연결할 때는 `build_transport_saturation_callback_from_activity_provider()`를 사용할 수 있다. `AqueousSaturationScreen` template의 종 순서는 transport 종 순서와 같아야 하고, candidate solid IDs는 kinetic campaign phase IDs와 같아야 한다. 활동도 callback signature는 `(global_time_s, cell_index, temperature_K, local_concentration_tuple) -> {species_id: dimensionless_activity}`이며, provider 객체에는 선언한 `provider_id`, `provider_revision`, `configuration_sha256`, `activity_standard_state` 속성이 있어야 한다. 표준상태 문자열은 template과 정확히 같아야 하며, callback에는 template의 고정 온도가 전달된다. Saturation mode campaign은 같은 `saturation_activity_standard_state`와 `temperature_K`를 선언해야 하며 solver가 callback과 둘 다 정확히 대조한다. Factory는 template의 phase terms/Ksp/evidence/review를 그대로 보존하고 activity state별로 포화비를 재계산한다. 한 고체의 activity product에 0 activity 종이 포함되면 saturation ratio 0을 반환한다. 이 결정론적 kinetics 연결은 activity/Ksp의 비영 uncertainty bound를 rate로 전파하지 않으므로 그런 bounds가 든 template은 거절한다.

포화도 callback은 각 transport interval **종료 시각**에 수송을 마친 셀별 aqueous state와 현재 solid inventory를 받아 평가한다. 이 endpoint 상태로 만든 power-law rate를 해당 interval의 duration에 곱해 보존 kinetic ledger에 적용하고, 성공한 inventory는 다음 transport interval의 초기값이 된다. 이는 transport-then-kinetics 순서의 명시적 operator split이다. 각 셀의 포화비·driving distance·방향·rate를 결과에 남긴다. callback이 없거나 반환 종 집합·값·configuration digest가 계약과 다르면 해당 구간을 commit하지 않는다.

실패한 시간 구간은 이전에 완전히 끝난 knot들만 `computed_*_prefix`에 넣는다. 중간 cell failure는 해당 구간의 앞선 cell 계산을 `partial_step`에 보존하되 그 구간의 전체 aqueous/solid 상태를 commit하지 않고 다음 구간 실행을 중단한다. 따라서 부분적으로 성공한 cell 집합을 완전한 시공간 상태로 오인하지 않도록 한다.

## 연동 경계

이것은 transport 후 kinetics projection을 적용하는 operator split이다. 명시 rate 방식은 caller가 미리 산출한 rate를 받고, 포화도 방식은 구간 끝 chemistry 상태에서 계산한 saturation snapshot을 phase rate law에 연결한다. endpoint 상태의 rate를 그 interval duration에 적용하므로 splitting 및 rate 대표성 가정에 민감하다. kinetic update는 다음 transport 구간으로 전달되지만 solubility/equilibrium/활동도 변화, nucleation, phase morphology, moving boundary, pressure/flow 변화 또는 보호 scale의 전기화학 피드백을 자동으로 계산하지 않는다. 두 방식 모두 transport-then-kinetics 순서는 caller가 검토해야 하며 동시 chemistry/transport 해나 시간분할 오차 보장을 제공하지 않는다.

예제는 `examples/competing_solid_kinetic_transport.py`다. 예제 상수는 합성 wiring 값이며 실험·권장·보정 데이터가 아니다. 실행 및 독립 물리 검증은 별도 작업으로 남아 있다.
