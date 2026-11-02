# 다축 평균 정수압 불변량 한계 스크리닝

## 목적

`matintegrity.multiaxial_sines_mean_limit_screen`은 caller가 제공한 응력 주기에서 편차응력 경로의 유한표본 진폭 지표와 시간 가중 평균 정수압 응력을 결합하고, caller 보정 한계와 비교한다. Sines 계열 불변량 방법의 평균 정수압 항을 사용하는 계산이며, coefficient와 한계는 모두 caller가 공급한다. 전통적인 구현 정의와 검증에는 별도의 재료·하중 근거가 필요하다.

## 계산 정의

편차응력 진폭 지표는 제공 표본 사이의 최대 pairwise \(\sqrt{J_2}\) 거리 절반으로 정의한다. 평균 정수압 응력은 각 표본에서 \(\sigma_H=(\sigma_{xx}+\sigma_{yy}+\sigma_{zz})/3\)를 계산한 다음, caller 시간축에서 선형 정수압 이력을 사다리꼴 적분해 주기 길이로 나눈다.

\[
\bar{\sigma}_{H,t}=\frac{1}{t_n-t_0}\sum_{i=0}^{n-1}\frac{\sigma_{H,i}+\sigma_{H,i+1}}{2}(t_{i+1}-t_i)
\]

따라서 시간이 비균일한 경우에도 실제 공급 시간 간격을 반영한다. caller가 제공한 편차응력 계수 \(a\), 평균 정수압 계수 \(b\), 양의 한계 \(S\)로 다음 scalar를 만들고 `S − P`를 반환한다.

\[
P=aR_{J2,\mathrm{sample}}+b\bar{\sigma}_{H,t}
\]

여기서 \(R_{J2,\mathrm{sample}}\)은 half maximum pairwise distance다. 비비례 경로에서 이를 최소외접구 반경이나 연속시간 진폭으로 해석하면 안 된다. 공개 연구 문헌은 불변량 기반 기준에서 편차응력 진폭과 평균 정수압 응력을 조합하는 Sines 형태를 설명하지만, 이 모듈의 유한표본 진폭 규약은 별도 명시된 caller 계산 규칙이다([독립 검토 연구](https://pmc.ncbi.nlm.nih.gov/articles/PMC7795696/)).

## 입력 및 계보

- nested `SampledStressInvariantHistory` 전체의 canonical digest를 입력한다. source file의 SHA와 구분되는 계약 digest다.
- `sample_time_s`는 stress sample과 길이가 같고 입력 순서대로 엄격히 증가해야 한다. 표본 순서를 재배열하지 않는다.
- nested history는 양 끝 응력 텐서의 정확한 일치, component order, caller의 closed-cycle/order 및 tensor-basis 검토를 요구한다.
- calibration ID/source/SHA와 일치하는 `Evidence`, 재료 조건 ID, caller 계수와 한계를 함께 보존한다. 보정 조건은 이력의 `material_condition_id`와 정확히 같아야 한다.
- 비균일 시간 가중, 유한표본 진폭 규약, 계수/한계, 재료 범위를 각각 caller가 검토해야 결과를 계산한다.
- 표본 정수압 적분 및 계수 결합 중 부동소수점 비유한값이 생기면 `out_of_scope`를 반환한다.

## 결과와 한계

`screening_parameter_Pa`, 시간 가중 평균 정수압 응력, caller limit, 비교 여유, 표본 witness ID를 반환한다. `caller_limit_not_exceeded`는 주어진 한계와 유한표본 규약에 대한 산술 비교다. 표준 적합, 허용성, 수명, 고장확률, 재료 자격 또는 안전성을 의미하지 않는다.

이 API는 응력 사이를 시간 보간해 extrema를 찾지 않고, 비례/비비례 경로를 분류하지 않으며, cycle counting, 피로수명 곡선, 다중 주기 누적 손상, calibration fitting, uncertainty 또는 qualification을 수행하지 않는다. 고차 응력 이력의 진폭 정의, 검증 방법, 재료별 coefficient와 적용 범위는 사용 목적에 맞게 별도로 검토해야 한다.

## 카탈로그 출처 문구 제안

`caller_finite_sample_sines_mean_hydrostatic_limit_screen`: caller가 제공한 finite tensor stress cycle의 명시적 J2 half-diameter와 시간 적분 평균 정수압 응력을 caller 계수로 결합하고, 같은 재료 조건의 제공 한계와 비교한다. 외부 계수·보정·경로 적용성은 추론하지 않는다.
