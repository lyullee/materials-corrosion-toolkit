# 단일 전해질 Pitzer 평균 활동도

`chemistry.pitzer_single_salt_activity`는 하나의 전기중성 수용액 전해질에 대해 caller가 공급한 Pitzer interaction coefficients로 mean ionic activity coefficient, osmotic coefficient와 water activity를 계산한다. 기준식은 Pitzer의 전해질 상호작용 이론이며, β 및 Cφ 계수 그룹과 온도별 parameter 의존성은 [USGS PHREEQC PITZER 자료 형식](https://water.usgs.gov/water-resources/software/PHREEQC/documentation/phreeqc3-html/phreeqc3-37.htm)에 설명돼 있다. 방법 원전은 [Pitzer (1973), Part II](https://doi.org/10.1021/j100638a009)다.

## 입력·수식 범위

요청에는 단일 양이온/음이온 종, 전하, 전기중성 formula unit, salt molality, 온도, molality scale의 `Aφ`, `b`, `β(0)`, `β(1)`, `β(2)`, `α1`, `α2`, `Cφ`, parameter record SHA-256과 Evidence를 명시한다. 계산 온도는 caller parameter가 선언된 온도와 허용차 안에서만 받는다. ionic strength도 parameter record가 지원한다고 caller가 선언한 최대값 안에서만 계산한다. β·C·Aφ 값은 이 패키지에 내장하지 않는다.

Pure-salt virial expression에 따라 Debye–Hückel 항과 cation–anion β/C interaction 항을 결합한다. 작은 `α√I`에서는 `Bγ`의 수치 상쇄를 줄이는 급수식을 사용한다. 수식·계수는 molality 표준상태 `1 mol/kg-water`를 기준으로 한다. 결과는 mean ionic `γ±` 및 `a± = γ± m/m°`이며, 개별 이온 `γᵢ`를 만들지 않는다.

## 명시적 한계

이 구현은 단일 pure salt만 지원한다. 혼합염의 cation–cation/anion–anion `θ`, ternary `ψ`, 중성종 상호작용, parameter fitting, 반응/상평형, activity coefficient의 단일이온 convention은 포함하지 않는다. parameter temperature의 허용차와 최대 ionic strength 표식은 caller 입력의 applicability 선언일 뿐, coefficient set이 실제로 qualified됐음을 증명하지 않는다. 계산 결과를 부식률이나 재료성능으로 변환하지 않는다.

Pytzer는 Pitzer 이론·평형 계산 구현을 제공하지만 공식 프로젝트가 GPL-3.0을 선언한다. MIT 공개 배포의 라이선스 경계를 유지하기 위해 이 계산 API는 Pytzer를 import하거나 배포 의존성으로 요구하지 않고 pure-salt 식을 별도로 구현했다. [Pytzer project](https://github.com/mvdh7/pytzer). 독립 라이선스 검토는 이 모델의 수학적·물리적 검증을 대신하지 않는다.

합성 API 배선 예제는 [`examples/pitzer_single_salt_activity.py`](../examples/pitzer_single_salt_activity.py)에 있다. 숫자는 계산 결과나 염 parameter가 아닌 임의 합성 계수다. 검증은 아직 수행하지 않았다.

요청 JSON 계약은 [`PitzerSingleSaltActivity`](schemas/PitzerSingleSaltActivity.json) 스키마를 따른다. 모델 레지스트리에서 `chemistry.pitzer_single_salt_activity`를 호출하는 경우 결과에도 input digest와 parameter provenance가 함께 보존된다.
