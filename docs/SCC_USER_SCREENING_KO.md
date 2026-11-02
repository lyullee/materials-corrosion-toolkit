# 사용자 정의 SCC 조건 선별

`degradation.chloride_scc_user_screening`, `degradation.ammonia_scc_user_screening`,
`degradation.alkaline_scc_user_screening`은 사용자가 작성·버전관리하는 사실(fact)과 조건(rule)을 실행하는
확장 API다. 내장 SCC 개시 임계값이나 허용 한계는 없다. 사용자 규칙을 바꾸면 profile version 및 설정/source
digest도 함께 바꾸어야 한다.

## 입력 구성

- 각 fact는 환경·재료·응력 영역 중 하나이며, 숫자/기술자/참거짓 타입을 명시한다.
- 알려진 숫자는 정확한 unit token과 기록 digest·근거를 가진다. 규칙과 토큰이 다르면 변환을 시도하지 않고
  해당 조건을 `unknown`으로 남긴다.
- 미확정 fact는 값을 비우고 사유를 기록한다. 무효 fact는 계산을 `needs_data`로 만들며, 확인하지 못한
  재료·환경·응력 조건을 안전한 결과로 추정하지 않는다.
- rule 내부 condition은 모두 만족해야 그 rule이 `met`이다. rule이 여러 개면 하나라도 만족하는 경우
  선별 결과는 `potentially_applicable`이다.
- profile은 mechanism, provider/revision, configuration/source digest, unknown policy와 근거를 보존한다.
  `indeterminate`는 unknown을 미결로 유지하고, `screen_in`은 확인되지 않은 사실을 보수적으로 선별에
  포함한다. 두 정책 모두 실제 균열을 관측했다는 뜻은 아니다.

각 평가에서 환경·재료·응력 근거, fact 정의/단위/digest, profile과 unknown policy, 선별 전용 경계를 각각
검토했다고 선언해야 한다. 규칙은 적용 당시의 가설로 관리하고, 출처와 변경 이력을 사용자가 보존한다.

## Python API

다음은 합성 검토 예제를 실행하는 경로다. 실제 재료 승인 또는 현장 평가 입력으로 사용하지 않는다.

```python
import json
from pathlib import Path

from matintegrity import evaluate
from matintegrity.contracts import RunContext

model_id = "degradation.chloride_scc_user_screening"
example = json.loads(Path("examples/model_inputs.json").read_text(encoding="utf-8"))["models"][model_id]
context = RunContext(
    asset_id=example["asset_id"],
    location_id=example["location_id"],
    time_basis="caller-declared SCC screening snapshot",
)
result = evaluate(model_id, example, context)
print(result.status, result.values["screening_outcome"])
```

세 mechanism의 실행 가능한 예제는 같은 JSON 파일에 있다. 출력은 `potentially_applicable`,
`not_indicated` 또는 `indeterminate`를 낼 수 있다. 모든 경우에 `screening_only=True`,
`qualification_outcome="not_evaluated"`가 유지된다.

## 기술적 한계와 검증 경계

이 모듈은 환경/재료/응력 facts에 대해 caller-authored 논리식을 평가할 뿐이다. SCC 민감도, 균열 발생,
균열성장률, 잠복시간, 잔여수명, POD, 파손확률, FTA 기초사건 확률 또는 규격 합격을 계산하지 않는다.
단위 변환·조건 간 보간·상관관계 추론·unknown 자동 대체는 하지 않는다. 서로 다른 시편과 source group을
자동 독립 표본으로 해석하지 않는다.

회귀 입력은 [계산기 예제](../examples/model_inputs.json)의 세 합성 profile과
`tests/test_scc_rule_screening.py`의 논리 경계 사례를 따른다. 실제 자료 검증에는 material condition,
열처리/용접·잔류응력, 염화물/암모니아/알칼리 화학, 온습도, 노출 시간, 물리 시편 계층과 관측 결과를 함께
보존한 독립 calibration/holdout 근거가 필요하다. 공개 Mendeley 304L 자료는 별도 권리·워크북 수식·시편
구조 감사가 끝나기 전 이 계산기의 calibration data가 아니다.
