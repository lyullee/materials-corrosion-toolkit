# 경쟁 고체상 포화도 기반 caller kinetics

`chemistry.competitive_solid_saturation_kinetics`는 caller가 제공한 경쟁 고체상별 포화비 이력을 phase-specific precipitation/dissolution power law로 변환하고, 그 rate를 기존 `CompetingSolidKineticLedger`에 전달한다. 함수는 농도·활동도에서 포화도를 계산하지 않는다. 계약된 입력이 독립 계산에서 나온 경우 그 provider 및 configuration 식별 정보를 함께 고정한다.

## 입력

- `aqueous_species`와 `candidate_solid_phases`는 각 수용액 종의 charge·원소 조성과 각 중성 고체의 형성 양론을 정의한다. 기존 validator가 charge와 모든 선언 원소를 확인한다.
- `phase_rate_laws`는 모든 고체상에 정확히 하나씩 둔다. 각 상의 침전 및 용해 rate constant는 `mol/m3/s`, 반응차수는 무차원이다. 계수와 표준상태 convention은 caller calibration 및 source digest와 연결한다.
- 선택적으로 `rate_constant_reference_temperature_K`, `minimum_valid_temperature_K`, `maximum_valid_temperature_K`와 침전·용해별 `*_activation_energy_J_mol`을 함께 제공할 수 있다. 각 활성화에너지는 기준온도 계수에 대해 독립 Arrhenius 배율 `exp[-Ea/R (1/T - 1/Tref)]`을 적용한다. 하나 이상의 활성화에너지를 쓰면 기준온도, 기준온도를 포함하는 유효 온도 범위와 `arrhenius_parameter_applicability_reviewed=true`가 모두 필요하다. 다른 방향의 활성화에너지를 생략하면 해당 방향 rate constant는 온도 독립 caller 값으로 유지한다.
- 각 cell/interval 결과는 평가 온도, 선언 지원 범위와 양방향 유효 rate constant를 기록한다. 지원 범위 밖 계산, 지수 계산의 binary64 overflow 또는 양의 상수 underflow는 0으로 숨기지 않고 해당 kinetics 경로를 실패 처리한다.
- `intervals`는 0초부터 빈틈없이 이어지고 각 구간마다 전체 후보상에 대한 유한한 비음수 무차원 saturation ratio를 제공한다. 0은 activity product가 0인 한계 상태를 표현한다.
- 각 구간은 선택적으로 `temperature_K`를 지정할 수 있다. 생략 시 요청의 기본 온도를 사용하며, 입력한 경우 해당 구간의 포화비 기반 rate law에 적용한다. 구간 온도와 기본 온도 모두 caller가 추적·검토한 열 이력이어야 한다.
- 계수와 포화비는 각 구간에서 상수로 해석한다. `S > 1`에서는 `r = k_p (S - 1)^n_p`, `S < 1`에서는 `r = -k_d (1 - S)^n_d`, `S = 1`에서는 `r = 0`을 적용한다. 양의 rate는 침전, 음의 rate는 용해다.

## 계산과 출력

계산기는 상별 derived rate와 입력 포화비를 결과에 기록한 뒤, 그 rate를 기존 conservative kinetic ledger에 전달한다. ledger는 기존 고체 inventory를 초과하는 용해를 제한하고, 동시 침전량에는 공통 aqueous-resource factor를 적용한다. 적용 extent, 고체·수용액 inventory, 원소 및 전하 잔차는 ledger 결과에서 확인한다. 유한 범위를 벗어난 속도식은 완전 결과 대신 계산 prefix와 `out_of_scope`로 반환한다.

직접 Python API:

```python
from matintegrity.multiphase_kinetic_ledger import (
    CompetingSolidSaturationKinetics,
    evaluate_competing_solid_saturation_kinetics,
)

result = evaluate_competing_solid_saturation_kinetics(
    CompetingSolidSaturationKinetics.model_validate(input_record)
)
```

다른 모듈에서는 `ModelRegistry.run("chemistry.competitive_solid_saturation_kinetics", input_record, context)` 또는 `run_json()`을 사용할 수 있다. `examples/model_inputs.json`에는 합성 연결 예제를 둔다. 숫자는 알고리즘 연결 예시이며 재료 상수나 권장 계수가 아니다.

수송 endpoint별 포화도 callback이 필요할 때는 `models.aqueous_saturation_screening.build_transport_saturation_callback_from_activity_provider()`가 `AqueousSaturationScreen`의 Ksp/evidence 정의와 caller activity provider를 묶어 `solve_competing_solid_kinetic_transport()`와 호환되는 함수를 만든다. Activity provider에는 `provider_id`, `provider_revision`, `configuration_sha256` 속성을 붙이고 같은 ID·revision·digest를 factory 입력에 제공한다. Factory가 내는 `configuration_sha256`, `provider_id`, `provider_revision`을 saturation-mode transport contract에 복사한다. 이 adapter는 활동도에서 포화비까지만 계산하며 표준상태, 온도 적용범위 및 조성 activity model의 qualification은 caller 책임이다.

## 검토 항목 및 제한

필수 gate는 반응망의 양론/solution-volume basis, 포화비와 표준상태 해석, rate-law 단위·온도·지원 범위, 용해 우선 split, 계산 사용 권한이다. ratio 이력과 rate-law coefficients는 caller 책임이다. 온도 보정은 caller가 선택한 유효 Arrhenius 모델의 계수를 해당 온도에 전파하는 기능이며, 활성화에너지 추정이나 rate-law 적합·외삽 범위의 자격화가 아니다. 이 기능은 상평형/수용액 speciation, activity coefficient, 경쟁상 선택, supersaturation 발생, nucleation induction time, 시간 내 rate 변화, 침전 형태나 scale 보호성, corrosion rate를 계산하지 않는다. 외부 실측 또는 공개 데이터 기반 수치 검증도 아직 수행하지 않았다.

온도 관계는 기준온도 대비 속도상수 비를 쓰는 Arrhenius 정의에 따른다([IUPAC Gold Book, Arrhenius equation](https://goldbook.iupac.org/terms/view/A00446)). rate constants, 활성화에너지, 적용범위와 계산 사용 권한은 실제 적용에 앞서 caller가 검토·공급해야 한다.
