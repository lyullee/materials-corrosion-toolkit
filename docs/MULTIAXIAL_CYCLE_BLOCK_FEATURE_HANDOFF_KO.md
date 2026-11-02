# 다축 tensor cycle에서 integer cycle block으로 feature 전달

`integration.cycle_block_feature_handoff`는 caller가 제공한 닫힌 tensor cycle을 지정된 finite plane에서 요약하고, 선택한 scalar 값을 `integration.adaptive_cycle_block_damage`의 기존 `IntegerCycleDamageBlock.parameters`에 연결한다. block의 `cycle_count`는 이 대표 경로가 caller가 선언한 반복 집단을 대표한다는 해석에만 적용한다.

## 계산되는 관측 feature

응력 tensor는 고정 component order `[xx, yy, zz, xy, yz, zx]`로 해석한다. 지정 plane의 단위 법선 `n`과 unit shear direction `m`은 서로 직교해야 한다. 각 sample에서 `σ_n=n·σn`, `ε_n=n·εn`, `γ_nm=2m·εn`을 계산한다. engineering shear strain 입력이면 tensor로 바꿀 때 shear 성분을 절반으로 해석하고, tensor shear 입력이면 마지막 projection에 factor 2를 적용한다.

각 finite plane에 대해 sample extrema로 normal stress max/min/range, normal strain range/amplitude, resolved engineering shear strain range/amplitude를 반환한다. 시간 재구성, 주기 폐합, cycle counting, plane 최적화 또는 재료상수를 사용하지 않는다. parameter binding은 `(plane_id, feature_id) → (parameter_id, unit, value)`를 명시한다. selected plane feature 단위는 Pa 또는 dimensionless로 고정되어, 임의 단위 변환이나 법칙별 가중치는 이 handoff에서 적용하지 않는다.

## 계보와 downstream 연결

각 block은 source record ID/hash, representative cycle digest, finite-plane feature set과 mapping을 포함하는 canonical digest를 `IntegerCycleDamageBlock.source_sha256`로 받는다. 생성된 parameter list와 block payload에도 별도 digest가 부여된다. `bind_cycle_features_to_adaptive_request()`는 computed handoff `AssessmentResult`의 input/receipt/block digest와 material, physical scope, cycle-count basis, block order 및 identity를 다시 확인한 뒤 existing request에 block list를 넣는다. 최종 adaptive request 자체도 새 parameter values를 입력 digest에 포함한다. 이 해시들은 lineage/변경 감지이지 전자서명은 아니다.

## 범위

이 API는 fatigue criterion, damage rate, state transition, failure life, failure probability 또는 acceptance를 계산하지 않는다. downstream integer-cycle provider와 그 calibration, 사용권, 재료 적용성, damage/state law는 전부 caller 소유다. 각 block에는 대표로 선언한 tensor path 한 개가 적용되므로 cycle variability를 압축하거나 보수적으로 대표한다는 주장은 자동으로 생기지 않는다. closure tolerance는 요청에 명시하며 범위를 벗어난 cycle block에서 결과를 중단한다.

`examples/multiaxial_cycle_block_feature_handoff.py`는 합성 전단·normal feature를 parameter 이름으로 연결하는 wiring 예시다. 실측값, 수명 추정 또는 calibration을 포함하지 않는다.
