# Davies 수용액 활동도 계수

`chemistry.davies_activity_coefficients`는 사용자가 제공한 완전한 수용액 이온 목록에서 이온세기와 전하 잔차를 계산하고, Davies 근사에 따라 전하를 띤 종의 활동도 계수를 계산한다. 이 기능은 탄산계 화학 및 수용액 모델에 공급할 수 있는 구성요소다. CO₂ 기체 용해, Henry 평형, 전기화학 전류 또는 부식률은 계산하지 않는다.

## 입력과 계산

각 용존 종의 몰랄농도 `m_i`(mol/kg water)와 전하수 `z_i`를 입력한다. 입력 목록이 이온세기를 결정할 만큼 완전한지 검토하고, 전기적 중성 잔차가 사용자가 지정한 공차를 만족하는지 확인한다.

`I = 0.5 Σ(m_i z_i²)`로 이온세기를 구한다. 전하종의 활동도 계수는

`log10(γ_i) = -A z_i² [sqrt(I)/(1 + sqrt(I)) - 0.3 I]`

로 계산한다. `A`는 온도·용매에 해당하는 제공자 값을 호출자가 근거와 함께 공급해야 한다. 코드가 `A`를 임의의 온도 상관식으로 추정하지 않는다. 활동도는 몰랄 표준상태 1 mol/kg water 기준의 무차원 값 `γ_i m_i/(1 mol/kg)`으로 반환한다.

입력 `ionic_strength_limit_mol_kg`는 최대 0.5 mol/kg water까지만 허용한다. 실제 이온세기가 선언 한도보다 크면 외삽하지 않고 `out_of_scope`를 반환한다. 이는 Davies 근사가 해당 정도까지 활용될 수 있다는 USGS 수문지구화학 문서의 논의를 보수적인 최대 경계로 사용한 것이다 ([USGS WSP 2254](https://pubs.usgs.gov/wsp/wsp2254/pdf/wsp2254a.pdf)). 더 농축된 염수에는 검토된 SIT/Pitzer 계열 모델이나 사용자 공급 모델이 필요하다. USGS PHREEQC 3 문서는 charged species의 Davies 선택지와 uncharged species의 별도 처리를 기술한다 ([USGS PHREEQC 3 문서](https://water.usgs.gov/water-resources/software/PHREEQC/documentation/phreeqc3-html/phreeqc3-50.htm)). 이 계산은 중성종 활동도계수를 별도 모델링하는 대신 gamma=1을 명시적인 제한 관례로 둔다.

전하가 0인 종은 명시적인 단순 관례로 `γ=1`을 둔다. 이는 중성 용질의 염석 효과를 다루는 중성종 모델이 아니다. 이 모델의 `dimensionless_activity`는 1 mol/kg water 기준이다. 탄산 알칼리도 계산기는 `activity_standard_state=molarity_1_mol_L`과 `c°=1 mol/L`로 농도수지를 쓰므로 Davies의 gamma와 activity를 그대로 전달하지 않는다. molality↔molarity 및 활동도 표준상태 변환, 용액 조건·밀도·농도 기준이 일관되게 정의되고 독립 검토되기 전에는 두 모델의 수치를 결합하지 않는다. 이 패키지는 그런 변환을 자동 수행하지 않는다.

## API 사용

```python
import json
from pathlib import Path

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

model_id = "chemistry.davies_activity_coefficients"
payload = json.loads(Path("examples/model_inputs.json").read_text(encoding="utf-8"))["models"][model_id]
result = default_registry().run(
    model_id,
    payload,
    RunContext(asset_id="synthetic", location_id="synthetic", time_basis="API contract check"),
)
```

다른 등록 계산기와 실행 context·근거·해시를 묶으려면 `default_registry().run("chemistry.davies_activity_coefficients", payload, context)`를 쓴다. `examples/model_inputs.json`에는 검토 절차를 설명하기 위한 합성 예가 있다.

## 검증 경계

핸드 계산식, 전하 불균형, 사용자가 낮춘 적용 상한, 상한 0.5 초과, 누락 검토와 중복 종 ID를 회귀 사례로 둔다. 해당 회귀는 HPC `batch59-davies-activity-coefficients`로 실행하도록 등록한다. 수학·계약 테스트가 성공하더라도 A 제공자 값의 정확성, 종목록 완전성, 고염수 적합성이나 실제 부식 예측을 입증하지 않는다.
