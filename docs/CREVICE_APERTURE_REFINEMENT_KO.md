# CREV1 개구 이력 구간 세분화 어댑터

## 목적

`matintegrity.models.crevice_aperture_refinement`는 CREV1 기하 모델이 만든
`geometry_states`의 시간 구간을 더 작은 구간으로 나누는 보조 API다. 각 구간의
셀별 상대 개구 변화량이 호출자가 정한 한도를 넘으면 구간 중간에 선형 보간
상태를 추가한다. 이 기능은 후속 계산에 사용할 시간 격자와 입력 이력을 구성하고
검토하기 위한 것이다.

## 입력 및 호출

호출자는 CREV1 결과 전체를 JSON 호환 딕셔너리로 전달하고, 해당 딕셔너리의
`canonical_digest`를 `source_geometry_result_sha256`에 지정한다. 상위 등록 모델의 `AssessmentResult` 객체와 전체 result digest를 함께 전달하면 원본 model/input/context/result identity도 교차 검증된다. 요청에는
`maximum_relative_aperture_change_per_segment`, 양의 정수
`maximum_internal_segments`, `maximum_bisection_refinements`, 그리고 선형 보간
적용성에 대한 명시적 검토값 `linear_geometry_interpolation_reviewed=True`가
필요하다. 스키마 모델은 `CreviceApertureHistoryRefinement`, 계산 함수는
`refine_crevice_aperture_history`다.

개념적 사용 예:

```python
from matintegrity.contracts import canonical_digest
from matintegrity.models.crevice_aperture_refinement import (
    CreviceApertureHistoryRefinement,
    refine_crevice_aperture_history,
)

source = crev1_geometry_result  # JSON 호환 딕셔너리 전체
request = CreviceApertureHistoryRefinement(
    refinement_id="case-a-grid-review",
    source_geometry_result=source,
    source_geometry_result_sha256=canonical_digest(source),
    maximum_relative_aperture_change_per_segment=0.05,
    maximum_internal_segments=500,
    maximum_bisection_refinements=200,
    linear_geometry_interpolation_reviewed=True,
)
result = refine_crevice_aperture_history(request)
```

세분화 조건은 한 구간의 시작 개구 `a`와 끝 개구 `b`에 대해 각 셀마다
`abs(b - a) / a <= maximum_relative_aperture_change_per_segment`인 것이다.
위반하면 해당 구간을 시간 중점에서 이등분하고 셀 개구는 원본 양 끝 상태 사이에서
선형 보간한다. 시간 상태와 구간은 시간 순서대로 반환된다. 요청의 원본 결과
digest와 정규화된 요청 digest를 결과에 포함한다. Source 입력이 `AssessmentResult` JSON인 경우 model ID/version, input digest, context digest도 남긴다.

## 한도 초과와 접두 결과

최대 내부 구간 수 또는 최대 이등분 횟수에 도달하거나 부동소수점 시간 정밀도로
더 나눌 수 없으면 결과 상태는 `out_of_scope`다. 이때 `computed_prefix`와
`computed_prefix_states`에는 성공적으로 수락한 연속 구간과 상태만 남는다.
각 분할 기록은 시작/끝 상태가 원본 knot인지 보간 상태인지 구분하고, 결과는 원본 상태와 삽입 상태를 별도 배열로도 반환한다.
`failed_source_interval_index`, `failed_interval_time_s`, `failure_reason`은 처음
수락되지 않은 구간과 원인을 식별한다. 접두 결과는 전체 이력 완료를 뜻하지 않는다.

## 경계 및 가정

- 입력 원본의 개구 이력과 digest를 검증하지만, 원본 모델의 실험적·물리적 타당성을
  재검증하지 않는다.
- 중간 상태는 원본 끝점의 단순 선형 보간이다. 전기화학 반응속도, 부식 생성물,
  침전, 응력, 유동, 농도장 또는 벽면 플럭스를 다시 계산하지 않는다.
- 작은 상대 개구 변화 제한은 시간 적분 정확도나 물리 오차 한계가 아니다.
- 후속 수송 campaign이 구간 안에서 형상을 고정하면 기존 operator-split 제한은
  그대로다. 이 어댑터는 moving boundary 또는 동시 연성 해석을 제공하지 않는다.
- CREV1 `crevice_campaign`에는 수송 기반 개구 갱신을 위한 자체 적응 세분화 기능도
  있다. 이 신규 API는 campaign 계산을 대체하거나 그 계산 결과를 재사용하지 않고,
  이미 산출된 CREV1 기하 이력에만 적용하는 별도 입력 전처리다.

이 문서와 구현은 API 사용 및 한계 기록이며, 수치 검증이나 물리 검증의 통과를
주장하지 않는다.

기본 registry 이름은 `integration.crevice_aperture_history_refinement`다. 결과는 `resolved_geometry_states`와 `interpolated_geometry_states`를 별도로 제공해 후속 계산이 원본 knot와 보간점을 구분할 수 있게 한다.
