# 사용자 공급 파괴평가 경계와 파괴 자료

`structural.failure_assessment_points`는 균열 평가점의 두 무차원 좌표를 계산해 사용자가 공급한 경계와 비교한다. 패키지는 상용 규격의 곡선·절단값·안전계수·허용표를 내장하지 않는다. 사용자가 정당하게 사용할 수 있고 적용성을 검토한 경계만 `FailureAssessmentCurve`로 공급한다.

이 계산기는 균열 건전성의 결합 지점이다. 기존 `fracture.stress_intensity` 또는 사용자 해석의 K, 별도 reference-stress 해, 재료 상태에 맞는 파괴저항과 정규화 강도를 명시적으로 받는다. 곡선 안쪽이라는 결과만으로 규격 합격, 시험 유효성, 잔여수명 또는 고장확률을 주장하지 않는다.

## 입력과 수학

각 `FailureAssessmentPoint`는 point·load case·location·material condition, K 기하해, reference-stress 해와 toughness source ID를 보존한다. 좌표는 다음과 같다.

- `Kr = effective_stress_intensity / fracture_resistance`
- `Lr = reference_stress / normalizing_strength`

`effective_stress_intensity_Pa_sqrt_m`에는 호출자가 검토한 하중 조합 결과를 넣는다. 1차/2차 응력, 잔류응력, 소성 보정과 constraint 효과를 패키지가 임의로 합치지 않는다. 파괴저항도 KIC·KIa·J 변환값·하한값 사이를 자동 변환하지 않는다.

`FailureAssessmentCurve`는 다음을 요구한다.

- 고유 curve ID와 assessment basis ID
- `Lr=0`에서 시작하는 엄격히 증가하는 Lr 절점
- 음수가 아니고 증가하지 않는 허용 Kr 절점
- 선형 보간, 적용 범위 설명, 출처·라이선스 또는 이용권한 근거

마지막 Lr 절점 밖은 외삽·절단하지 않고 `out_of_scope`다. 지원 범위 안에서 `Kr <= allowable Kr`이면 `inside_or_on_declared_boundary`, 초과하면 `outside_declared_boundary`다. 전체 `declared_boundary_outcome`은 모든 점이 안쪽이면 `satisfied`, 하나라도 밖이면 `not_satisfied`, 곡선 지원 밖이 있으면 `unknown`이다. 계산 상태와 사용자가 선언한 경계 결과는 서로 다른 필드다.

필수 검토 bool은 K 해, reference stress 해, toughness 적용성, 하중 조합과 곡선 적용성을 각각 다룬다. 하나라도 확인되지 않으면 `needs_data`다. 재료 condition ID 불일치도 평균·대체하지 않고 중지한다.

## Python 예

전체 중첩 입력은 `examples/model_inputs.json`의 `structural.failure_assessment_points`에 있다.

```python
from matintegrity.registry import default_registry

registry = default_registry()
result = registry.run_json(
    "structural.failure_assessment_points",
    request_json,
    context,
)
```

곡선 digest는 절점·근거·적용 설명을 포함한다. 다른 규격 판본이나 사용자 곡선으로 바꾸면 같은 curve ID를 재사용하지 않는다.

## 공개 crack-arrest 자료

고정 자료 `g69875w65c.1`은 CC BY 4.0으로 공개된 ferritic/martensitic steel의 C1·C2 crack-arrest 원시 시험이다. 로컬 고정 ZIP의 SHA-256은 `233f70de5d51148b93eab68654297d4ac4aa782864a5c7e43a3520be8ca54bde`다.

- C1 9파일, C2 9파일, 총 79,341행
- 파일명 표기 온도 범위 150.15~296.15 K
- 모든 기록의 원 시간 간격 0.05 s, 시험별 기록 길이 140.25~388.1 s
- 원 힘 채널 음수 76,285개·양수 3,056개·정확한 0 없음
- 한 파일은 전체 헤더를 한 번 더 인용한 형식이며 그 정확한 표현만 열 단위로 복구

`list_crack_arrest_runs`는 family·source filename·파일명에서 읽은 온도와 원 멤버를 반환한다. `read_crack_arrest_series`는 시간, machine displacement, signed force, extensometer displacement와 cycle index를 SI로 읽는다. zeroing·부호 반전·필터·resampling·compliance correction·event picking을 하지 않는다. 파일명 온도는 아직 시편 로그와 독립 대조하지 않았다고 표시한다.

이 자료는 raw force-displacement 채널이며 곧바로 유효 KΙa가 아니다. 시편 치수·균열 길이·동적 해석·시험 유효성·온도 이력·원 연구의 reduction 절차를 검토하기 전 toughness를 산출하지 않는다. Crack-arrest toughness를 initiation toughness, 서비스 하한, FAD 곡선 또는 확률분포로 바꾸지 않는다. 원 파일과 점별 자료는 공개 배포물에서 제외한다.

## 공개 전이구간 파괴인성 편집 자료

고정 자료 `2vkgrbsy8j.1`은 CC BY 4.0으로 공개된 ferritic steel 전이구간 KJc 편집 workbook이다. 로컬 고정 ZIP의 SHA-256은 `d1007e9b3a3802594f169a15e72a94353a674cb72daf2faef93f9ae9fabdf66f`다.

- Provider training 448행, test 192행, 총 640행
- 재료명 14개, CT 394행·SEB 165행·PCCv 81행
- 보고 KJc 36.1~255.4 MPa√m, 보고 항복강도 348.8~990.1 MPa
- 두 partition 사이에 모든 필드가 같은 행은 없지만 물리 시편의 독립성은 확인되지 않음
- 온도 열의 단위 표기는 `K`이나 값은 −160~100. 연계 논문은 해당 시험 온도 특징과 재료별 범위를 °C로 명시
- W·B·a 열에는 workbook 단위 표기가 없지만 논문의 T 크기 mm 정의와 전 행의 두께 척도가 일치해 `article_mm`로 검토됨
- 재료·시편형식·W/B의 3% 또는 0.1 mm 허용오차로 만든 형상 조건 그룹 34개가 모두 두 partition에 존재
- 연계 논문 표의 재료·참고문헌 그룹 대조: 정확 614행, 유력 이름 변형 18행, 미해결 8행
- 참고문헌 그룹 9개 중 DOI 7개 확인. Workbook 행은 DOI 그룹 176행·서지만 확인 456행·출처 그룹 미해결 8행이며 원 관측 재배포 권리는 전부 미확정

`read_fracture_toughness_temperature`는 source sheet/row와 partition-local ID, 보고 온도·KJc·항복강도·탄소·one-hot specimen type·W/B/a·재료명을 보존한다. [연계 논문](https://doi.org/10.1016/j.engfailanal.2020.104458)의 방법 설명과 재료별 표가 온도를 °C로 표현하므로 workbook의 충돌하는 `K` 표기를 함께 기록하고 기본 113.15~373.15 K를 만든다. 파생 workbook에는 `temperature_unit_override="degC"` 또는 `"K"`를 명시할 수 있고 비양의 절대온도는 거절한다. 논문은 W·B·a와 T 크기를 mm로 정의하고 전 행의 B 4.07~101.6이 그 척도와 일치하므로 기본 `dimension_unit_basis="article_mm"`에서 SI 치수를 만든다. 원 workbook의 단위 표기 부재는 별도로 보존한다. 파생 자료에는 `apply_article_dimension_review=False` 또는 `dimension_unit_override="mm"`/`"m"`를 사용한다.

`condition_group_id`는 재료명·시편형식·검토된 W/B만 묶는 source-specific 누설 방지 층이다. 기본 상대 허용오차 3%와 절대 허용오차 0.1 mm는 호출자가 바꿀 수 있다. 단위 검토를 끄면 그룹도 생성하지 않는다. 34개 그룹이 모두 training/test 양쪽에 있으므로 provider 분할을 독립 holdout으로 사용하지 않는다. `condition_group_physical_independence_reviewed=False`이며 그룹 번호를 물리 시편 ID로 해석하지 않는다.

`article_source_group_id`는 논문 안의 참고문헌 그룹 번호일 뿐 행별 원 문헌 식별자가 아니다. `article_reference_bibliographic_id`는 확인된 DOI만 기록하고, 보고서·학위논문은 `bibliography_only`로 남긴다. 출판물 라이선스와 원 관측 권리를 별도 필드로 보존하며 DOI·공개 PDF·TDM 허용을 관측 재배포 허가로 바꾸지 않는다. `S55CFY2012`는 논문 표의 `S55C`와 이름·탄소량이 달라 `probable_name_variant`, 대응 그룹을 확인하지 못한 `SS400`은 `unresolved`로 보존한다. 표의 행 번호도 물리 시편 ID나 원 문헌 ID가 아니다. `test`는 제공자가 정한 데이터 분할이지 독립 기관·장치·재료 검증 표식이 아니다. Reported KJc는 시험 유효성, 구속·두께 보정, 검열 여부와 원 문헌 조건을 확인하기 전 FAD의 파괴저항·서비스 하한·확률분포로 자동 연결하지 않는다. 원 workbook과 점별 변환은 공개 배포물에서 제외한다.

## 검증과 한계

`scripts/validate_fad.py`는 49개 점에서 독립 작성한 구간 선형 계산과 결과를 비교한다. 최대 차이는 약 `1.67e-16`이고 모든 경계 절점을 재현하며 마지막 Lr 밖 값은 허용 Kr를 만들지 않는다. 결과는 `validation/failure_assessment_math.json`에 소스 해시와 함께 남는다.

```powershell
.\.venv\Scripts\python.exe scripts\inspect_fracture_data.py
.\.venv\Scripts\python.exe scripts\inspect_fracture_toughness_data.py
.\.venv\Scripts\python.exe scripts\validate_fad.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_fad.py tests\test_fracture_data.py tests\test_fracture_toughness_data.py
```

이 검증은 정규화·보간·상태 계약의 수학 검사다. 실제 K 해, reference stress, toughness, FAD 경계, cracked component 또는 규격 판정을 검증하지 않는다.

## 다음 과제

공개 원 연구의 시편 기하·균열 위치·측정/해석 절차와 유효성 표식을 검토한 뒤 crack-arrest 전용 데이터 계약을 확대한다. 편집 KJc에는 원 문헌·물리 시편·온도/치수 단위·유효성·두께/constraint·검열 표식을 연결한다. Initiation toughness의 자격과 tearing resistance는 별도 시험 계약으로 확보한다. 실제 FAD 검증에는 같은 재료·온도·두께·균열 형상의 K/reference-stress 공급자, 독립 파괴 결과, 잔류/2차 응력 처리, 소성·constraint·불확실성 근거가 필요하다. 기간 고장확률은 균열 분포·성장·하중 이력·검출·파괴한계 불확실성을 별도 모델로 연결해야 한다.
