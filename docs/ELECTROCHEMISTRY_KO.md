# 실측 분극 곡선과 갈바닉 전류

`corrosion.mixed_potential`은 사용자가 공급한 전극별 분극 곡선과 노출 면적을 조합한다. 서로 다른 곡선을 하나의 직선 저항으로 바꾸지 않고, 부호가 있는 전류의 보간 함수에서 전류 평형점을 찾는다. 초기 선형 모델 `corrosion.galvanic_linear`도 계속 제공하며, 그 모델의 저항·과전압 범위 조건을 별도로 따른다.

방법의 공개 근거는 [IUPAC 혼합 전위 정의](https://goldbook.iupac.org/terms/view/M03944)와 [Gamry의 순전류·부분 반응 설명](https://www.gamry.com/application-notes/corrosion-coatings/basics-of-electrochemical-corrosion-measurements/)이다. 코드와 아래 설명은 이 프로젝트에서 작성했다. 외부 구현·문장·그림·허용표를 포함하지 않는다.

## 계산하는 양

전극 `k`의 노출 면적을 `A_k`, 전위에 따른 양극 방향 양수 순전류 밀도를 `j_k(E)`라 하면 다음 식을 만족하는 공통 전위를 구한다.

\[
F(E)=\sum_k A_k j_k(E)=0.
\]

모든 곡선이 공유하는 전위 구간만 사용한다. 그 안의 모든 절점을 합치고 각 구간에서 부호가 있는 전류를 선형 보간한다. 각 구간의 전류 합도 직선이므로 전 구간을 조사해 고립된 근과 연속 영전류 구간을 보존한다. 전위만 같은 지점에서 전류 밀도의 크기를 비교하면 면적비를 반영할 수 없으므로, 면적을 곱한 전류를 먼저 합한다.

부호를 없앤 `log(abs(j))`를 보간하면 음극·양극 전류의 상쇄와 0 부근의 의미가 달라진다. 이 API는 부호를 보존한 `j(E)`를 사용한다. 측정 지점 사이의 세부 형상이나 관측 불확실성은 이 보간만으로 검증되지 않는다.

출력 전류는 **외부 회로로 이동하는 전극의 순전류**다. 한 전극에서도 금속 산화와 환원 반응이 동시에 일어날 수 있다. 따라서 순전류가 0이어도 금속 용출이 0이라고 결론 내리지 않는다. `total_positive_net_current_A` 역시 전체 양의 순전류 합계이며 금속 용출 부분 전류를 뜻하지 않는다. 검토한 부분 반응·효율·원자가 근거 없이 이를 `corrosion.faraday`에 직접 연결하지 않는다.

## 입력 계약

| 계약 | 주요 내용 |
|---|---|
| `PolarizationCurve` | 곡선·표면 상태·프로토콜·전해질·전위 기준·온도·점 ID·V·A/m²·부호 관례·근거 |
| `PolarizedElectrode` | 실제 계산 전극 ID, 사용자가 공급한 노출 면적 m², 대응 곡선 |
| `MixedPotential` | 2~32개 전극, 물리 적용 조건 검토, 절대/상대 전류 잔차 허용치 |
| `MixedPotentialEquilibrium` | 전위·지원 구간·전극별 부호 전류·잔차·기울기·수치 품질 |

곡선당 2~20,000점, 합계 100,000점까지 받는다. 각 곡선은 원래 순서대로 전위가 엄격히 증가하는 한 가지 분기여야 한다. 왕복 스캔·히스테리시스·중복 전위를 정렬하거나 평균해 단일 곡선으로 만들지 않는다. 분기 선택·반복 시험·표면 변화의 해석은 사용자의 명시적 전처리와 근거로 남긴다.

점 ID는 원 행을 찾을 수 있도록 고유하게 유지한다. 같은 재료의 대표 곡선을 다른 전극에 재사용할 수 있지만 새 독립 실험을 추가한 것은 아니다. 계산 전극 ID는 서로 달라야 한다. 근거의 `Evidence.sha256`에는 대응 관측 파일의 해시를 보존할 수 있다.

`reference_electrode_id`, `electrolyte_id`, `temperature_K`는 곡선에 미확정 값을 `None`으로 보존할 수 있다. 계산 시에는 모두 선언돼 있고 서로 같아야 한다. 같은 기준 전극 계열 이름만으로 농도·온도·교정 차이를 지우지 않는다. SHE·Ag/AgCl·SCE 사이의 전위 변환은 자동 수행하지 않으며, 검토한 변환 공급자가 입력 값과 근거를 먼저 준비한다.

`current_convention="unreviewed_signed_net"`은 원 부호를 읽었지만 양극 방향을 확인하지 못한 상태다. 계산에는 `anodic_positive_net`이 필요하다. 전류/전류 밀도와 A/cm²/A/m²를 구분하며, 기존 공개 데이터 로더는 해당 원자료의 A/cm²를 A/m²로 변환한다.

## 적용 조건과 상태

다음 네 선언을 명시적으로 받는다. 선언은 적용 근거를 기록하는 장치이며 시험·물리 검증을 대신하지 않는다.

- `quasi_steady_reviewed`: 스캔·표면 변화·용량성 전류를 검토해 해당 곡선의 준정상 전달을 허용했는지
- `negligible_ohmic_drop_reviewed`: 전극 사이 및 전해질의 전압 강하를 무시할 근거가 있는지
- `condition_compatibility_reviewed`: 온도·전해질·유동·노출·표면 이력의 조합이 적절한지
- `anodic_positive_reviewed`: 순전류의 양극 양수 관례를 확인했는지

분포된 용액 전위, 유의한 배선/전해질 저항, 시간에 따른 표면 변화, 국부 반응·확산장과 분리되지 않은 용량성 응답은 별도 모델이 필요하다. 유체 물성은 필요한 경우 CoolProp 공급자로 준비할 수 있지만, 유체 상태만으로 분극 곡선·기준 전극 변환·금속 손상을 생성하지 않는다.

| 상태 | 해석 |
|---|---|
| `computed` | 공통 지원 구간에서 수치적으로 해상된 고립근 하나를 얻고 잔차 기준을 만족 |
| `needs_data` | 미검토 조건/부호·누락 메타데이터·여러 근·영전류 구간·소거로 미해상된 근 |
| `out_of_scope` | 조건 불일치·공통 구간 없음·구간 안의 근 없음·표현 불가능한 수치 범위 |

여러 근이면 `equilibria`에 모두 남기고 대표 `mixed_potential_V`는 비운다. 기울기가 양수인 근만 임의 선택하지 않는다. 평탄 구간의 양 끝을 별개의 고립근으로 중복 보고하지 않는다. 연속 영전류 판정은 부동소수점으로 표현한 보간 함수의 판정이며 정확한 물리 연속 평형의 증명이 아니다.

`slope_diagnostic`은 양쪽 전류 합의 기울기를 `positive`, `negative`, `mixed_or_tangent`, `support_boundary`로 구분한다. 양의 용량만 있는 단순 동적 식에서는 양의 기울기가 복원 방향을 주지만 실제 안정성에는 추가 상태와 시간 모델이 필요하다. 이 API는 동적 안정성을 인증하지 않는다. 지원 끝점의 근도 표시하며 구간 밖의 동작은 외삽하지 않는다.

면적 곱·정규화·최종 잔차를 검사하고 큰 전류 상쇄에 비해 평형의 변화가 해상되지 않으면 `cancellation_limited`로 보존한다. 잔차 허용치는 선언한 절대값과 전극 전류 크기에 대한 상대값을 합친다. 잔차 통과는 입력 곡선의 정확성, 보간 오차나 구조 적합성의 통과를 뜻하지 않는다.

## Python과 다른 모듈 연결

```python
import json
from pathlib import Path
from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

inputs = json.loads(Path("examples/model_inputs.json").read_text(encoding="utf-8"))["models"]["corrosion.mixed_potential"]
result = default_registry().run_json(
    "corrosion.mixed_potential", json.dumps(inputs),
    RunContext(asset_id="authored", location_id="couple", time_basis="static response"),
)
print(result.status, result.values["mixed_potential_V"])
```

`examples/galvanic_coupling.py`는 원자료·네트워크 없이 실행하는 합성 예제다. JSON 또는 `models.electrochemistry`의 타입으로 사용하며, 일반 Python 입력에서는 엄격한 `Evidence`/하위 계약을 만들고 JSON 입력은 `model_validate_json` 또는 `run_json`으로 읽는다. 결과에는 원 입력·모델 판본·문맥·근거 ID·내용 해시가 남는다.

모니터링 모듈은 전위·순전류·수치 상태를 각각 전달하고, 부식 속도·수명·기간 고장확률로 이름을 바꾸지 않는다. 위험성 모듈에는 별도 용출·형상 성장·구조 한계·시간/불확실성 모델을 거쳐 사건 계약을 만든다. 현재 결과는 기간 확률 어댑터에 직접 들어갈 확률이 없다. 여러 저장소의 실제 수신은 `extension_requests/`의 요청과 별도 통합 검사를 따른다.

## 실제 공개 자료의 현재 경계

[고정 Zenodo 자료](https://doi.org/10.5281/zenodo.13886478)와 [공개 원 연구](https://doi.org/10.3390/met14090993)를 대조했다. 로컬 감사는 세 전해질의 24곡선·19,680점을 점/행 ID와 부호 그대로 읽는다. 공개 연구 6쪽의 방법에는 Ag/AgCl, 25°C, 0.1 mol/L 산 용액 두 종류·5% NaCl, 질소 사전 처리와 스캔 속도가 기술돼 있다. NaCl 백분율의 기준과 기준 전극 충전 용액은 검토한 방법에서 확정하지 않았다.

본문의 명목 끝 전위 1.0 V와 워크시트 끝 전위 약 0.502 V의 차이를 보존한다. 침지 깊이 1 cm를 실제 노출 면적 1 cm²로 바꾸지 않는다. 단일 전극의 순차 스캔을 실제 결합 시험으로 간주하지 않으며, 전해질 저항·준정상 전달·면적·기준 전위 일관성 검토가 남아 있다. 공개 표의 `Rp`도 면적 정규화가 확정되지 않았으므로 Stern–Geary 입력으로 자동 사용하지 않는다.

관측과 공개 연구 파일은 로컬 제외 경로에 둔다. 배포되는 감사 결과는 집계·해시·프로토콜 검토와 누락 조건이며 점별 관측·논문 문장·표·그림을 포함하지 않는다. CC BY 4.0 자료의 저자·DOI·이용조건은 데이터 카탈로그와 제3자 고지에 유지한다.

## 검증과 재현

합성 검사에는 선형 회로의 독립 해, 면적비, 서로 다른 절점, 세 전극 전류 보존, 다중/접선/끝점 근, 평탄 구간, 전위 기준 이동, 전류 척도 변화, 미검토/실패/수치 표현 한계가 포함된다. 비선형 비교는 `j_k=2*j0_k*sinh(k*(E-E0_k))`의 전류 합에서 직접 유도한 폐형식과 보간 격자 17·65·257·1025점을 비교한다. 마지막 전위 절대 오차는 약 `1.8e-9 V`, 전극 전류 최대 절대 오차는 약 `4.3e-10 A`였다. 이 특정 합성 함수의 오차이며 일반 격자 수렴률·실제 시험 정확도를 보장하지 않는다.

```powershell
python scripts/fetch_data.py --ids galvanized-polarization --include-optional
python scripts/inspect_polarization_data.py
python examples/galvanic_coupling.py
python scripts/validate_electrochemistry.py
python scripts/verify.py
```

`validation/electrochemistry_math.json`에 모델·검증 코드 해시, 합성 파라미터, 입력 digest, 격자별 오차와 환경을 기록한다. 실제 결합 실험·부분 반응 분리·물질 손실 비교·반복/기관 단위 독립 검증, 보간 불확실성·저항 및 동적 상태 결합은 후속 작업이다.
