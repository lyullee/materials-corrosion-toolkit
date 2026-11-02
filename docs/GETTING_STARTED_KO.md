# 재료·부식 툴킷 상세 사용 설명서

## 1. 무엇을 선택하는가

이 프로젝트의 사용 단위는 문자열 `model_id`로 선택하는 Python API다. 부식속도만 계산할 수도 있고, 수용액 평형·물질전달·전극반응·두께 손실·구조 평가를 별도의 계약으로 연결할 수도 있다. 모든 기능을 켜는 단일 자동 판정 프로그램은 아니다.

먼저 [README](../README.md)의 63개 핵심 계산군에서 목적을 찾는다. 이어 [전체 API 설명서](MODULE_DIRECTORY_KO.md)에서 해당 모델의 입력·출력·전제조건을 확인한다. 명칭이 비슷하더라도 물리 범위가 다를 수 있다. 예를 들어 평균 두께 손실과 최대 국부 침투, 안정화 변형률–수명과 균열전파 수명, 포화 증기압과 실제 혼합물 퓨가시티는 서로 바꾸어 쓸 수 없다.

## 2. 설치와 버전 기록

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install "materials-corrosion-toolkit[science,thermo]==0.1.0a1"
python -m matintegrity.cli models
```

기본 기능만 쓰려면 extras를 생략한다. 기본 설치에는 NumPy·Pydantic·Pint가 필요하고 과학 계산·파일 형식·CoolProp은 해당 기능의 선택 의존성이다. 실제 배포 이름은 `materials-corrosion-toolkit`, import와 CLI 이름은 `matintegrity`다. 기존 API 이름을 유지하기 위한 의도적인 구분이다.

평가별로 Python 버전, 설치한 배포 버전, 단위 API 버전, 관련 라이브러리 버전, 사용한 Git commit/tag 또는 배포 파일 SHA-256을 기록한다. 예전 검증 영수증은 당시 소스·환경의 근거이며 새 환경의 자동 재검증을 대신하지 않는다.

## 3. 입력 계약을 읽는 방법

```python
from matintegrity.registry import default_registry

registry = default_registry()
definition = registry.describe("corrosion.coupon_loss")
print(definition["input_schema"])
print(definition["output_units"])
print(definition["assumptions"])
print(definition["runtime_dependencies"])
```

`input_schema.properties`는 최상위 필드, `required`는 반드시 제공해야 할 필드다. `minimum`, `exclusiveMinimum`, `enum`, `const`, `minItems`, `pattern` 등을 확인한다. 중첩 객체의 `$ref`는 `$defs`에 연결된다. 스키마에 표시하기 어려운 필드 간 일관성 검사는 Python validator가 추가로 수행한다.

필드가 숫자이면 숫자로 제공한다. `"100"` 같은 문자열을 임의로 숫자로 바꾸거나, 빠진 단위를 자동으로 추정하지 않는다. 일부 모델은 엄격한 tuple 계약을 사용하므로 Python 객체를 직접 구성할 때와 JSON을 읽을 때의 차이에 주의한다. 파일·HTTP로 받은 JSON은 `registry.run_json()`을 권장한다.

입력 필드 이름의 SI 단위와 설명을 우선한다. mm와 m, MPa와 Pa, 시간(hour)과 초, 사이클과 반전수, 수소 원자 몰수와 분자 몰수, 공학 전단변형률과 텐서 전단변형률은 같은 값이 아니다. 표준상태와 압력 기준도 별도 입력 의미다.

## 4. 단위 계산을 실행하고 보관하기

```python
from pathlib import Path
from matintegrity import evaluate
from matintegrity.contracts import RunContext

context = RunContext(
    asset_id="demonstration-asset",
    location_id="demonstration-coupon",
    time_basis="elapsed seconds",
)
result = evaluate(
    "corrosion.coupon_loss",
    dict(mass_loss_kg=0.001, exposed_area_m2=0.01,
         density_kg_m3=1000.0, duration_s=100.0),
    context,
)
assert result.status == "computed"
assert abs(result.values["mean_penetration_m"] - 0.0001) < 1e-15
Path("coupon_result.json").write_text(result.model_dump_json(indent=2), encoding="utf-8")
```

이 값은 설명을 위해 만든 합성 입력이다. 재료 밀도나 부식속도 추천값이 아니며 실측 자료로 표시해서는 안 된다. `values`만 잘라서 저장하지 말고 입력, 단위, 문맥, 근거, 상태, 해시를 포함한 전체 결과를 보관한다.

## 5. JSON 입력과 결과 복원

```python
import json
from matintegrity.contracts import AssessmentResult

payload = json.dumps(dict(mass_loss_kg=0.001, exposed_area_m2=0.01,
                          density_kg_m3=1000.0, duration_s=100.0))
result = registry.run_json("corrosion.coupon_loss", payload, context)
restored = AssessmentResult.model_validate_json(result.model_dump_json())
assert restored.input_digest == result.input_digest
```

모델의 `asset_id`, `location_id`, clock/time basis가 입력 안에도 있으면 `RunContext`와 정확히 맞춰야 한다. 시간열의 행 수만 같다는 이유로 동시 관측이라고 추정하거나, 이름이 비슷하다는 이유로 동일 시편으로 연결하지 않는다.

## 6. 여러 계산을 연결하기

아래 예는 설명용 현재 두께에서 평균 손실을 뺀 뒤 일정 속도 예측에 전달하는 가장 작은 연결이다. 현장 계측·불확도·균일 손실 가정의 적합성은 별도로 필요하다.

```python
coupon = evaluate("corrosion.coupon_loss", dict(
    mass_loss_kg=0.001, exposed_area_m2=0.01,
    density_kg_m3=1000.0, duration_s=100.0), context)
if coupon.status != "computed":
    raise ValueError("선행 손실 계산이 완료되지 않았습니다")

initial_thickness_m = 0.010  # 이 예의 사용자가 선언한 설명용 초기값
forecast = evaluate("corrosion.uniform_forecast", dict(
    current_thickness_m=initial_thickness_m-coupon.values["mean_penetration_m"],
    required_thickness_m=0.006,
    rate_m_s=coupon.values["rate_m_s"],
    horizon_s=1000.0), context)
print(forecast.status, forecast.values)
```

실제 연결 API는 단순 숫자 외에 선행 `AssessmentResult`, 결과 해시, 물리 범위, 재료 상태, 위치, 시간 정렬, 좌표계, 단위 및 압력 기준의 명시적 일치를 요구할 수 있다. 값만 맞춘 자체 result dictionary를 만들어 선행 계산을 가장하지 않는다. 관련 계약은 [API](API_KO.md), [아키텍처](ARCHITECTURE_KO.md), [저장소 간 교환](CROSS_REPOSITORY_EXCHANGE_KO.md)에 있다.

## 7. 계수·물성·판정 기준 커스터마이징

사용자가 제공하는 계수와 테이블에는 출처, 적용 재료·환경·온도·하중 범위, 단위, 보정 자료, holdout 자료, 사용 권한이 필요하다. 모델이 요구하는 review flag는 실제로 확인한 범위에만 참으로 지정한다. 실행하려고 모든 flag를 켜는 것은 물리 검증이 아니다.

실험으로 보정한 계수와 공학적으로 선언한 가정은 `Evidence.origin`에서 구분한다. 사용 가능한 값은 계약별로 `measured`, `open_dataset`, `model_prediction`, `user_declared`, `synthetic` 등이지만, 일부 모델은 더 엄격하게 제한한다. 합성 숫자를 `measured`로 바꾸지 않는다.

규격이나 사내 기준은 권한을 가진 사용자가 선언하는 테이블·규칙·플러그인으로 제공한다. 툴킷의 계산 완료와 사용자 기준의 만족 여부는 별도 상태로 기록한다.

## 8. 외부 provider와 CoolProp

`describe()["runtime_dependencies"]`에 선언된 이름은 실제 Python 객체를 `runtime_dependencies={...}`로 주입한다. 요구하지 않은 dependency를 임의로 더 넣으면 거부될 수 있다. provider는 JSON 안의 코드나 문자열 표현식을 실행하는 방식이 아니다.

CoolProp 기능을 쓰려면 `thermo` extra를 설치하고, 물질 조성·상태변수·단위·상태 영역·라이브러리 버전을 기록한다. 임계점, 포화선, 두 상, 순물질과 혼합물의 차이를 확인한다. 임의로 상을 강제하여 유효하지 않은 상태를 통과시키지 않는다. 포화 상태의 내부 자기 일관성과 독립 실험 정확도는 구분한다.

## 9. 실패와 보류를 처리하는 방법

| 상황 | 처리 |
|---|---|
| 입력 `ValidationError` | 누락 필드·자료형·단위 의미·상호 정렬을 수정한다. 값을 추정해 채우지 않는다. |
| `needs_data` | 진단을 읽고 실제 근거·권한·선행 결과·의존성을 확보한다. |
| `out_of_scope` | 물리·보정·수치 범위를 확인하고 알맞은 모델을 선택한다. |
| `computed` | 가정과 결과 의미를 확인한다. 안전·규격 합격으로 자동 변환하지 않는다. |
| 해시·identity 불일치 | 실제 자료·버전·위치·시점이 맞는지 추적한다. 해시만 덮어써서 연결하지 않는다. |

NaN, 무한대, 누락 관측, 반대 부호, 범위 밖 테이블을 정상값으로 고치거나 자동 외삽하지 않는다. 결과가 수치적으로 수렴했다고 입력 물성·메커니즘이 참이 되는 것은 아니다.

## 10. 검증·연구 재개

[연구 재개 설명서](RESEARCH_CONTINUATION_KO.md)에서 시험 묶음과 분모를 확인한다. 단위 검사는 작은 해석해, 수지·불변량, 극단값, 연결 계약, 기존 결과 재실행을 서로 구분한다. 대규모 독립 계산은 case ID·입력 해시·seed·환경을 고정해 나누고 결과를 ID로 병합한다. 실험 비교는 시편과 source group 단위로 보정·holdout을 먼저 분리한다.

파일·원자료·토큰을 공개 저장소에 넣지 말고 [배포 경계](PREPUBLISH_CHECKS_KO.md)를 유지한다. 모델을 바꾸면 출력 의미·단위·적용 범위·시험·스키마·카탈로그·설명서·버전을 함께 검토한다.
