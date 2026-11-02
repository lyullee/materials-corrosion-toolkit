# 다축 피로 수명 보정자료의 쌍별 비교 진단

## 목적과 적용 범위

`matintegrity.multiaxial_calibration_transfer_audit`는 caller가 제공한 기준 재료 조건과 대상 재료 조건의
피로수명을 **동일한 caller 정의 매개변수 값**에서 짝지어, 대상/기준 수명비와 가중 로그비 요약치를 계산한다.
이는 calibration transfer 가능성을 검토할 때 데이터 차이를 드러내는 진단값이다. 보정곡선을 옮기거나
새 수명을 예측하지 않는다.

Python API:

- 요청: `matintegrity.multiaxial_calibration_transfer_audit.MultiaxialCalibrationTransferAudit`
- 한 쌍의 값: `PairedLifeCalibrationPoint`
- 계산: `evaluate_multiaxial_calibration_transfer_audit(request)`
- 결과: `matintegrity.contracts.Calculation`

## 계산 정의

각 점 i에서 caller가 동일하다고 선언한 매개변수 값 xᵢ의 기준 수명 Nᵣ,ᵢ와 대상 수명 Nₜ,ᵢ를 입력한다.

```text
ratio_i = N_target,i / N_reference,i
log_ratio_i = ln(N_target,i) - ln(N_reference,i)
mean_log = Σ(weight_i × log_ratio_i),     Σ(weight_i) = 1
geometric_mean_ratio = exp(mean_log)
weighted_population_sd = sqrt(Σ(weight_i × (log_ratio_i - mean_log)²))
```

가중치는 호출자가 모두 양수로 주고 합을 1로 맞춰야 한다. 구현은 자동 정규화하지 않는다. 점의 순서는
매개변수의 오름차순이며 중복 수준은 허용하지 않는다. 점별 수명비, 로그수명비, 기준·대상 수명, 매개변수,
가중치는 결과에 그대로 보존된다.

## 입력 계약과 근거

호출자는 다음 정보를 정확히 연결해야 한다.

- 동일 매개변수 정의 ID와 단위, 실제 짝지은 수치 수준
- 서로 다른 기준/대상 재료 상태 식별자와 시험 조건 식별자
- 양쪽 원자료 record SHA-256, 각 digest와 일치하는 Evidence, 출처 식별자·인용·사용권한 ID
- 짝짓기·시험 프로토콜 검토와 출처 권리·조건 범위 검토

이 경로는 새 실험값, 물성표, 기준식 또는 외부 라이브러리를 포함하지 않는 독립적인 산술 구현이다. method
source ID는 `caller_paired_exact_parameter_level_life_ratio_audit`다. 원자료의 재사용 권한은 각 데이터 제공자
조건을 따르며, 공개 API를 만들거나 원자료를 얻을 권한이 생기는 것은 아니다.

## 결과 해석 및 제한

- 결과는 제출된 유한한 짝 데이터에 한정된 기술통계다. 동일 매개변수 수준을 두 조건에서 직접 측정했는지,
  피로시험 정의와 중단기준이 비교 가능한지는 호출자가 확인해야 한다.
- 서로 다른 시험 조건은 각각 결과에 기록된다. 조건 차이를 자동 보정하거나 비교 가능하다고 판정하지 않는다.
- 로그-로그 보간, 외삽, 곡선 적합, 재료 간 전달식 생성, 설계 수명 산출은 하지 않는다.
- 평균 수명비 또는 산포는 고장확률, 신뢰구간, 분포 꼬리, 허용기준, 재료 qualification 또는 코드 합격이 아니다.
- 지수 범위 밖, 환경·온도·주파수·변형률 속도·시편 방향·표면처리 차이, censoring 및 생존자료 처리는
  별도 설계와 검토가 필요하다. 현재 API는 그러한 데이터를 추정하거나 보정하지 않는다.
- 서로 다른 매개변수 정의/단위, material condition, 위치 또는 측정 프로토콜을 이 입력에 억지로 맞추지 않는다.

## 개발·검증 기록

API는 입력 형식·digest·Evidence가 연결된 caller 원자료와 exact-level pairing을 요구한다. 수치 계산은
쌍별 log ratio와 명시적 caller 가중치의 유한합만 사용한다. 별도 시험과 package build는 아직 수행하지 않았다.
따라서 이 문서는 방법의 물리적 타당성, 데이터 재현성 또는 산업 적용 적합성에 대한 검증 주장이 아니다.
