# 간극 재부동태 전위 여유 선별

## 목적

`validation.crevice_repassivation_margin_history`는 caller가 제공한 운전 전위 관측을 동일 재료·환경·온도·전극 기준에서 얻은 재부동태 전위 측정값과 정확한 시간 절점에서 비교한다. 각 knot에서 signed margin (E_{op}-E_R), 두 표준불확도 제곱합의 제곱근, 그리고 caller가 고른 불확도 배수에 따른 수치 분류를 반환한다.

## 비교 관계

\[
M(t_k)=E_{op}(t_k)-E_R(t_k),\qquad
u_M=\sqrt{u_{op}^2+u_R^2}.
\]

판정 표시는 (M>q u_M)이면 `operating_potential_above_threshold_band`, (M<-q u_M)이면 `operating_potential_below_threshold_band`, 그 사이는 `uncertainty_bands_overlap`다. (q)는 입력된 비음수 multiplier다. 이 분류는 potential 값의 비교이며 고장확률 또는 재료 건전성 판정이 아니다.

## 정확한 자료 매칭

각 threshold와 operating observation은 knot의 시각, 재료 ID, condition ID, 해시 고정된 electrolyte 기록, 온도, 염화물 molality, reference electrode ID 및 전위 부호 규약이 정확히 같아야 한다. 측정 row와 electrolyte record에 라이선스/사용허가 Evidence 및 digest를 붙인다. 전위 불확도는 양쪽 동일 단위(mV)의 표준불확도로 입력한다. threshold specimen 수와 원시 record 계보를 출력에 남긴다.

## 한계

- 이 API는 정확히 대응된 측정 절점만 비교한다. 시간, 온도, chloride 또는 재료 사이 보간·외삽은 하지 않는다.
- `above`/`below` 표시는 threshold 위/아래의 숫자 비교다. 더 양의 전위가 특정 재료에서 부식 개시나 보호를 뜻한다고 자동 해석하지 않는다.
- 전위 기준 변환, 부호, iR 보정, scan/hold protocol, 재부동태 전위 정의, 표면 상태, 표본 대표성은 사용자가 검토해야 한다.
- pH/speciation, 상평형, pit/crevice 성장, kinetics, 금속 손실, 부식률, 위험확률, acceptance, inspection interval 또는 qualification은 계산하지 않는다.

## 절점 기반 초과 지속시간 요약

`validation.crevice_repassivation_excursion_duration_history`는 위 margin API의 완전히 매칭된 절점 기록을 받아 인접 측정 시각 사이의 구간을 요약한다. 출력은 연속 시간의 실제 상태를 복원하지 않는다. 명시적으로, 두 끝점 모두에서 signed margin이 불확도 band보다 큰 구간만 `definite_sample_supported_above_band_duration_s`에 더한다. 한쪽 이상 끝점에서 불확도 범위가 threshold 위에 닿는 구간은 `possible_sample_supported_above_band_duration_s` 및 `unresolved_transition_duration_s`에 포함한다. 나머지 구간도 초과 지속시간으로 확정하지 않고 unresolved로 남긴다.

각 구간의 계산 길이는 정확한 관측 시각 차이 `t[k+1]-t[k]`다. definite 합은 possible 합에 포함되는 부분집합이다. 이 길이는 샘플링 지점 두 곳이 지지하는 구간 합일 뿐이며, 그 사이에서 언제 초과가 시작·종료했는지를 뜻하지 않는다. 따라서 출력은 관측점 기반 기술 통계이며 신뢰도, 발생확률, 가동시간 보증 또는 재료 수명으로 해석하면 안 된다. 입력에 연속된 두 절점이 없으면 구간 및 지속시간 합은 0이다.

새 API 입력은 `CreviceRepassivationExcursionDurationRequest`이며, 기존 `CreviceRepassivationMarginHistoryRequest`와 함께 구간 해석 검토 확인값을 요구한다. Source ID `exact_knot_sample_supported_threshold_excursion_duration`는 이 endpoint-only 합산 규칙을 식별한다.

## API와 provenance

```python
from matintegrity.crevice_repassivation_margin import (
    CreviceRepassivationMarginHistoryRequest,
    CreviceRepassivationThresholdKnot,
    CreviceOperatingPotentialKnot,
    evaluate_crevice_repassivation_margin_history,
    CreviceRepassivationExcursionDurationRequest,
    evaluate_crevice_repassivation_excursion_duration_history,
)
```

Source IDs: `caller_crevice_repassivation_threshold_history`, `caller_measured_crevice_operating_potential_history`, `exact_knot_uncertainty_aware_potential_margin_screen`. 입력 record SHA는 값과 조건을 함께 해시한다. 공개 코드는 사용자가 제공하는 실험 기록이나 데이터 표를 포함하지 않는다.

테스트, 수치 실행, 전기화학 검증, package build, HPC 계산은 수행하지 않았다. 후속 검증은 경계 동일성 실패, uncertainty 중첩, signed margin 양·음 방향, record digest 변조, 단위/reference 불일치와 정확한 시각 정렬을 다뤄야 한다.
