# 가스켓 조립 평형의 국소 공분산 전파

## 목적

`integration.gasket_joint_equilibrium_local_covariance`는 기존의 `fabrication.gasket_multi_bolt_sector_equilibrium` 계산에 caller가 제공한 후속 하중 단계 입력 공분산을 연결하여, 공통 opening·볼트 힘·가스켓 평균 접촉압력 출력의 1차 근사 공분산을 구합니다. 가스켓 곡선이나 초기 체결 상태를 다시 추정하지 않습니다.

불확실 좌표는 기준 조립점 이후(`step_index >= 1`)의 다음 scalar 항목에서 명시적으로 선택합니다.

- 외부 분리 하중 `external_separating_force_N`
- 순서가 지정된 개별 볼트의 자유 길이 변화 `bolt_free_length_change_m`
- 순서가 지정된 개별 가스켓 섹터의 자유 두께 변화 `gasket_free_thickness_change_m`

각 좌표는 입력 공분산 행렬의 동일 순서와 중앙 차분 크기에 연결됩니다. 입력 행렬은 유한·대칭·양의 준정부호여야 하며, 최대 32개의 불확실 좌표를 받습니다. 공분산 레코드의 digest는 공급자, revision, 레코드 ID, 좌표 순서 및 전체 공분산 행렬을 결합해야 합니다. Evidence에는 같은 source ID, SHA-256, 사용권 ID를 포함합니다.

## 계산

먼저 기존 조립 평형 evaluator를 기준 입력에서 계산합니다. 각 불확실 좌표 `x_j`에 대해 `h_j`만큼 위·아래로 이동한 두 입력을 같은 evaluator에 보내고, 결과 출력 벡터 `y`의 중심 차분으로 Jacobian을 근사합니다.

```text
J[i,j] ≈ (y_i(x + h_j e_j) - y_i(x - h_j e_j)) / (2 h_j)
Cov(y) = J Cov(x) Jᵀ
```

출력 벡터는 각 단계의 opening, 각 볼트 인장력, 각 섹터 평균 접촉압력을 순서대로 펼친 값이며 `output_labels`가 정확한 순서를 설명합니다. `output_standard_uncertainty`는 이 값들의 각 분산 대각 원소의 제곱근입니다. `output_covariance` 단위는 행·열마다 각 output label의 단위 조합으로 해석해야 하며 한 개의 공통 단위가 아닙니다.

## 적용 단계

1. 기준 이력에 caller가 검토한 joint geometry, preload, bolt stiffness, gasket force-compression curves 및 각 단계 열 자유 이동을 구성합니다. 기준점은 기존 solver의 force-balance·review·support 조건을 만족해야 합니다.
2. 민감도를 추정할 후속 하중 단계 좌표만 입력합니다. 같은 `input_covariance` 배열의 행과 열은 `coordinates` 목록의 순서와 완전히 일치해야 합니다.
3. 각 `finite_difference_step`은 좌표 단위와 크기, 입력 정밀도, 주변 응답의 매끄러움을 고려하여 선택합니다. 두 방향의 섭동 모두 원래 contract 및 gasket curve/opening support 안에서 계산되어야 합니다.
4. 결과의 `sensitivity_jacobian`과 nominal output을 함께 확인합니다. 하중 섭동이 접촉 활성상태를 바꾸거나 constitutive curve knot을 넘으면 작은 섭동에 대한 미분값을 전역 민감도로 간주할 수 없습니다.

## 한계 및 해석

- 이는 1차 delta method입니다. global nonlinear uncertainty envelope, Monte Carlo 표본, 확률 분포, 실패 확률 또는 신뢰수준을 만들지 않습니다.
- 초기 체결력·볼트 강성·stress area·가스켓 force curve·면적·geometry·temperature·CTE 및 calibration 불확실도는 포함하지 않습니다. caller가 별도 확장해야 합니다.
- 기준 단계는 고정되며 불확실 좌표에 포함할 수 없습니다. 모든 perturbation에서 nominal과 동일한 출력 구조를 얻어야 합니다.
- 접촉 전이점, zero-force bolt 경계, 곡선 knot 및 support 경계 가까이에서는 미분 근사가 불안정하거나 미분 불가능할 수 있습니다. active set 안정성과 차분 step 적용성은 caller가 검토해야 합니다.
- 하위 계산은 공통 축방향 opening의 준정적 parallel-sector 모델을 사용합니다. 플랜지 FE 해석, 동적 하중, 국부응력, 누설, 밀봉 acceptance, 설계코드 적합성 및 재료 qualification은 포함하지 않습니다.
- 계산 결과는 입력 공분산의 provenance·실험적 타당성 또는 물리적 적합성을 인증하지 않습니다.

## 독립 방법 참고자료

- Joint Committee for Guides in Metrology, *Evaluation of measurement data — Guide to the expression of uncertainty in measurement*, JCGM 100:2008. 표준불확도 전파와 sensitivity coefficient의 일반적인 원리를 참고합니다. [BIPM 공식 발행본](https://www.bipm.org/documents/20126/2071204/JCGM_100_2008_E.pdf)
- Joint Committee for Guides in Metrology, *Evaluation of measurement data — Supplement 1 to the Guide to the expression of uncertainty in measurement — Propagation of distributions using a Monte Carlo method*, JCGM 101:2008. 비선형성 또는 분포 전파가 필요한 경우 별도 검토할 일반 지침입니다. 이 API는 그 Monte Carlo 절차를 구현하지 않습니다. [BIPM 공식 발행본](https://www.bipm.org/documents/20126/2071204/JCGM_101_2008_E.pdf)

이 API는 위 문서의 일반 측정불확도 개념을 참고해 자체 입력 계약과 수치 계산을 정의합니다. 문헌의 문장·표·수치 예제는 코드에 복사하지 않았고, 기준 오차분포나 자료를 내장하지 않습니다.

## API 계약

- 모듈: `matintegrity.models.gasket_joint_equilibrium_covariance`
- 모델 ID: `integration.gasket_joint_equilibrium_local_covariance`
- 스키마: `matintegrity.gasket_joint_equilibrium_local_covariance.v1`
- 입력: `GasketJointEquilibriumLocalCovariance`
- 좌표: `JointLoadCovarianceCoordinate`
- 평가기: `evaluate_gasket_joint_equilibrium_local_covariance(request)`
- 등록 메타데이터 공급자: `specifications()`
- source ID: `caller_covariance_for_ordered_joint_load_coordinates`, `central_finite_difference_local_sensitivity_of_quasistatic_gasket_equilibrium`, `first_order_covariance_pushforward_joint_contact_outputs`
- 수치/물리 검증 및 패키지 작업은 아직 수행하지 않았습니다.
