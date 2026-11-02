# 가스켓 압축 curve의 가중 단조 회귀

## 모델 목적

`fabrication.gasket_compression_curve_monotone_fit`은 같은 가스켓 재료 상태, 시험편/lot, 시험 방법, 온도, loading rate 및 caller가 지정한 단일 loading branch에 속하는 측정 압축력 점을 받아 측정된 변형량 knot에서 비감소 힘 곡선을 적합합니다. 측정 잡음 때문에 force point가 국소적으로 감소하는 경우에 사용할 수 있는 bounded 데이터 정리 계산입니다.

입력은 압축량 `m`, 압축력 `N`, 각 힘 관측의 caller 표준불확도 `N`과 observation ID를 포함합니다. 같은 압축량에서 반복 측정된 점은 inverse-variance 가중 평균으로 묶고, 서로 다른 압축량 knot에는 해당 가중 합을 적용합니다. 기록 digest는 시험 조건과 모든 원 관측을 고정하며 Evidence는 provider·digest·사용권을 연결해야 합니다.

## 수학적 방법

주어진 압축 knot의 평균력 `y_i`와 양의 가중치 `w_i = 1/u_i²`에 대해 아래 제약 최소제곱 문제를 풉니다.

```text
minimize  sum_i w_i (f_i - y_i)^2
subject to f_i <= f_(i+1)
```

비감소 단조 제약은 pool-adjacent-violators algorithm (PAVA)으로 계산합니다. SciPy의 `scipy.optimize.isotonic_regression`을 사용할 수 있으면 우선 사용하고, 선택적 SciPy가 없는 최소 설치에서는 같은 weighted PAVA 계산으로 대체합니다. 입력에는 실제 측정한 `(0 m, 0 N)` origin 관측이 반드시 포함되어야 합니다. 입력에 zero origin이 없으면 이를 합성하거나 첫 계측점까지 외삽하지 않고 contract 오류로 거부합니다.

필요 시 caller는 `minimum_tangent_stiffness_N_m`을 선택해 양의 최소 기울기를 제한할 수 있습니다. 이때 힘에서 `k_min * compression`을 뺀 값을 단조 적합한 뒤 같은 항을 다시 더합니다. 해당 선택이 고유 시험 데이터와 downstream constitutive curve 조건에 맞는지 caller가 검토해야 합니다. slope floor가 없으면 적합 curve가 평탄 구간을 포함할 수 있으며 출력의 `strictly_increasing_force_curve_compatible`가 이를 표시합니다.

## 출력 읽기

- `fitted_curve_points`: zero origin을 포함해 관측된 고유 압축량 knot에서 적합된 `(compression_m, compressive_force_N)` 점
- `residuals`: 입력 각 observation의 측정력, 적합력 및 signed residual
- `fit_diagnostics`: 사용 알고리즘, 원 관측/knot 수, PAVA pool 수, weighted/unweighted RMSE 및 최대 절대 residual
- `test_condition`: 적합 curve를 식별하는 재료 조건·시험편·방법·branch·온도·속도 정보
- `strictly_increasing_force_curve_compatible`: 기존 downstream curve contract의 strict force 증가 조건을 만족하는지 표시

fitted points는 기존 가스켓 joint evaluator의 force-compression knot 형태와 맞게 구성되지만, 자동으로 gasket 자료의 적용성을 확인하거나 joint solver 입력으로 등록하지는 않습니다. 이를 downstream으로 넘기기 전에 material state와 geometry/area normalization, force convention, 시험 branch 및 source lineage를 검토해야 합니다.

## 적용 단계

1. 원시 시험 값이 동일 시험 계열에 속하는지 확인합니다. loading, unloading 또는 별도 cycle branch를 섞지 않고, 보정된 compression displacement와 force의 SI 단위를 통일합니다.
2. 힘 표준불확도는 장비 해상도·보정·시험 반복성에 대해 caller가 정한 값이어야 합니다. 이 API가 자료에서 불확도를 추정하지 않습니다. 관측 간 의존성이 있으면 inverse-variance independent-weight 방식이 적합하지 않을 수 있습니다.
3. provider·revision·record ID·gasket/test condition·관측 배열을 canonical digest에 포함하고, 적법한 계산사용 라이선스가 연결된 Evidence를 제공합니다.
4. 다섯 review flag를 평가합니다. 검토가 빠지면 계산을 `needs_data`로 반환합니다. 자료가 finite support 밖이거나 수치 오버플로가 나면 적용범위 밖으로 종료합니다.
5. 적합 잔차와 knot별 curve를 raw data와 함께 비교하고, 노이즈 보정이 곡선의 물리적 특징을 지나치게 평탄화하지 않았는지 판단합니다. residual 수치만으로 curve를 물리 검증한 것으로 간주하지 않습니다.

## 적용 한계

- 한 개의 단조 압축 loading branch만 적합합니다. unloading, cyclic hysteresis, viscoelastic relaxation, stress relaxation, dwell history 또는 온도 shift는 별도 모델이 필요합니다.
- 가중치 입력이 유효한 독립 표준불확도라는 가정 아래 조건부 least-squares 결과를 계산합니다. 잔차는 사후 예측 오차, 신뢰구간, 재료 모집단 분포 또는 품질 통계를 의미하지 않습니다.
- 압축량 knot 사이에서의 interpolation이나 knot 범위 밖 extrapolation을 하지 않습니다. 이 모델은 입력된 knot에 fitted force만 반환합니다.
- 인장 gasket response, 면적별 응력 변환, 접촉장, 플랜지 유연도, 누설, seating acceptance, 재료 자격 및 코드 적합성은 다루지 않습니다.
- 임의 시험 curve를 다른 가스켓 종류, 두께, 보강재, lot, 표면, 온도, 변형속도 또는 조립 조건에 이전하지 않습니다.
- 물리 validation, 독립 benchmark, 실측 calibration/holdout 및 downstream solver 검증은 아직 별도 작업입니다.

## 독립 참고자료

- F. M. T. A. Busing, “Monotone Regression: A Simple and Fast O(n) PAVA Implementation,” *Journal of Statistical Software*, 102(1), 2022. weighted PAVA 알고리즘 구현 맥락을 참고합니다. [DOI: 10.18637/jss.v102.c01](https://doi.org/10.18637/jss.v102.c01)
- SciPy documentation, `scipy.optimize.isotonic_regression`. 단조 최소제곱 목적함수, case weights와 PAVA의 공용 API 정의를 참고합니다. [SciPy 1.15.2 reference](https://docs.scipy.org/doc/scipy-1.15.2/reference/generated/scipy.optimize.isotonic_regression.html)
- A. I. Jordan, A. Mühlemann, and J. F. Ziegel, “Characterizing the optimal solutions to the isotonic regression problem for identifiable functionals,” *Annals of the Institute of Statistical Mathematics*, 74, 489–514, 2022. 단조 회귀 해의 통계적 성질을 다루는 일반 배경입니다. [DOI: 10.1007/s10463-021-00808-0](https://doi.org/10.1007/s10463-021-00808-0)

이 문헌의 문장, 데이터, 예제 결과 또는 가스켓 물성값을 복사하지 않았습니다. 코드에는 수치 reference curve나 material default가 내장되어 있지 않습니다.

## API 계약

- 모듈: `matintegrity.models.gasket_compression_curve_monotone_fit`
- 모델 ID: `fabrication.gasket_compression_curve_monotone_fit`
- 스키마: `matintegrity.gasket_compression_curve_monotone_fit.v1`
- 입력: `GasketCompressionCurveMonotoneFit`
- 관측: `GasketCompressionCurveObservation`
- 평가기: `evaluate_gasket_compression_curve_monotone_fit(request)`
- 모델 메타데이터: `specifications()`
- source ID: `caller_gasket_compression_force_observations_and_uncertainties`, `weighted_non_decreasing_isotonic_regression_pool_adjacent_violators`, `caller_material_condition_temperature_rate_and_loading_branch`
- SciPy가 설치된 환경에서는 해당 isotonic API를 사용하며, SciPy가 없는 경우 코드에 포함된 작은 PAVA 구현으로 동작합니다. 수치 검증·패키징은 수행하지 않았습니다.
