# 수용액 탄산계 알칼리도 종분포

`chemistry.carbonate_alkalinity_speciation`은 사용자가 검토한 pH, 총알칼리도, 온도별 평형상수와 활동도계수로 수용액의 `H+`, `OH−`, `HCO3−`, `CO3²−`, `CO2*` 농도를 계산한다. `CO2*`는 용존 비이온화 이산화탄소 종을 뜻한다. 이 계산은 wet-CO2 부식률·수명·합격 여부를 내지 않으며, 가스-액 평형이나 가스 압력도 계산하지 않는다.

## 수식과 계약

활동도 pH에서 수소 활동도를 `aH = 10^(−pH)`로 둔다. 입력 평형상수는 표준상태 `1 mol/L`로 정규화한 무차원 활동도 상수이며, gamma 항은 호출자가 공급한다.

```text
[H+]  = aH / gamma_H+ × c°
[OH−] = Kw / aH / gamma_OH− × c°
r     = [CO3²−] / [HCO3−]
      = K2 × gamma_HCO3− / (gamma_CO3²− × aH)
[HCO3−] = (AT − [OH−] + [H+]) / (1 + 2r)
[CO3²−] = r × [HCO3−]
aHCO3− = gamma_HCO3− × [HCO3−] / c°
[CO2*] = aH × aHCO3− / K1 × c°
```

여기서 `c° = 1 mol/L`, `AT`는 입력 총알칼리도(`mol/L`), 대괄호는 몰농도다. 결과에는 계산된 종으로 재구성한 알칼리도와 입력값의 잔차가 함께 들어간다. 잔차가 호출자가 선언한 허용값보다 크면 계산 결과를 `out_of_scope`로 돌린다.

이 계약에서 사용하는 활동도계수와 평형상수는 `1 mol/L` 농도 표준상태와 일관되도록 호출자가 공급해야 한다. `chemistry.davies_activity_coefficients`의 출력은 `1 mol/kg water` 몰랄 표준상태이므로 그대로 연결하지 않는다. 일관된 용액 조성·밀도 및 표준상태 변환을 외부 근거로 검토하고 나서 gamma를 제공해야 한다. 자동 변환 경로는 제공하지 않는다.

입력 계약은 시료·설비 위치, 측정 및 평형상수 제공자·버전·설정 및 레코드 digest, 증거, 알칼리도 불확도와 활동도·온도·종 정의 검토 gate를 보존한다. `CarbonateActivityConstants.activity_standard_state`는 `molarity_1_mol_L`로 고정되며, `activity_standard_state_reviewed`가 true여야 계산을 진행한다. 평형상수 온도와 시료 온도는 기본적으로 일치해야 하며 모델은 온도 외삽을 하지 않는다. 선언된 총알칼리도 expanded uncertainty는 pH·평형상수·활동도계수를 고정한 상태에서 종별 선형식으로 정확히 전달하고, 원 불확도 기준을 결과에 유지한다. 이 값은 확률이 아니며 pH·상수·모델 불확도는 포함하지 않는다.

## 유효 범위와 금지된 해석

- 알칼리도는 탄산계와 물의 `H+`/`OH−` 항이 지배한다고 검토한 경우에만 적용한다. 암모니아, 붕산, 인산염, 유기산 등 다른 완충 성분이 의미 있으면 이 모델은 해당 시료를 설명하지 않는다.
- pH 활동도 기준, 평형상수 활동도 기준, 활동도계수 및 용존 `CO2*` 정의를 입력 제공자가 명시해야 한다. 이 모듈은 이온강도 보정이나 평형상수를 자체 생성하지 않는다.
- `CO2*`를 Henry 법칙, fugacity, 유체 압력, 수화/기상 상평형과 연결하지 않는다. 이런 값은 조건에 맞는 별도 물성·가스상태 공급자가 제공해야 한다.
- 용존 종 농도를 부식률, 전기화학 반응속도, 스케일, 국부부식, 균열성장, 수명, 구조 적합성 또는 확률로 변환하지 않는다.

이 범위는 [USGS의 advanced carbonate speciation method 설명](https://water.usgs.gov/water-resources/memos/memo.php?id=2098)이 다루는 활동도·pH·온도·다른 산염기 성분의 영향과 일치하도록 제한했다. 여기의 API와 문장은 독립적으로 작성했으며, 상수값이나 데이터 표를 내장하지 않는다.

## 실행

```python
import json
from pathlib import Path

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

model_id = "chemistry.carbonate_alkalinity_speciation"
example = json.loads(Path("examples/model_inputs.json").read_text(encoding="utf-8"))["models"][model_id]
result = default_registry().run_json(
    model_id,
    json.dumps(example),
    RunContext(
        asset_id=example["asset_id"],
        location_id=example["location_id"],
        time_basis="caller-reported sample time",
    ),
)
print(result.status, result.values)
```

이 입력은 API 형식 설명용 합성 사례다. 물성표와 측정값은 사용자가 출처·권한·조건을 확인해 제공해야 한다. JSON Schema는 `docs/schemas/CarbonateAlkalinitySpeciation.json`과 `docs/schemas/CarbonateActivityConstants.json`에서 확인한다.
