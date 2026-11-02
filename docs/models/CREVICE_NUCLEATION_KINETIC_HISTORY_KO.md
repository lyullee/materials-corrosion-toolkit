# Crevice 핵생성·성장 동역학 이력

## 목적과 적용 경계

`chemistry.crevice_nucleation_kinetic_history`는 한 개의 닫힌, 균일 조성 batch에 대해 caller가 제공한 exact interval saturation ratio, thresholded molar nucleation source, 그리고 상이 생긴 뒤 적용할 precipitation/dissolution rate law를 계산한다. 각 interval의 속도는 기존 경쟁 고체 kinetic ledger에 전달되어 실제 용존 종과 고체 재고를 갱신한다. 반응별 공통 aqueous-resource 제한과 원소·전하 수지는 해당 ledger가 확인한다.

이 API는 핵 개수, 입자 크기 분포나 임계 핵의 미시적 자유에너지로부터 nucleation rate를 유도하지 않는다. 핵생성 law의 입력 속도 단위는 **고체 몰수 / 용액 부피 / 시간**이다. 이 정의를 쓰므로 적분 결과는 용액 재고로 직접 들어가며, 단순한 핵 개수 source가 아니다.

## 수치 계약

각 phase의 caller nucleation law는 다음 관계를 선언한다.

`r_nuc = k_n · max(S / S_crit − 1, 0)^p`

여기서 `S`는 dimensionless saturation ratio, `S_crit`은 caller가 정한 onset ratio, `p`는 무차원 차수, `k_n`은 mol m⁻³ s⁻¹ 단위의 caller parameter다. 생성 고체 재고가 caller `nucleated_inventory_threshold_mol_m3`에 도달하기 전에는 이 source를 적용한다. 그 이후 interval부터는 `SolidSaturationRateLaw`의 caller growth/dissolution rate를 쓴다. 그 law가 제공하는 Arrhenius 온도 항목을 쓰면 선언된 support와 review gate를 만족해야 한다.

Saturation 기록은 ID·시간·온도·상 순서·ratio가 포함된 record digest와 Evidence가 일치해야 한다. 전체 request Evidence는 aqueous species, solid phase, 성장법칙, 핵생성법칙, saturation interval, kinetic configuration 및 parameter source digest를 모두 포함한다. 모든 법칙은 phase identity가 정확히 일치해야 하며 최대 interval×phase 연산량, interval당 seed threshold split 수, 총 ledger evaluation 수, 합산 절대 속도 제한을 적용한다.

각 nucleation source가 일정한 구간 안에서 seed 재고 임계값에 도달할 것으로 예상되면 event time을 `(threshold − 현재 고체 재고) / molar nucleation rate`로 산출한다. 계산기는 먼저 해당 시간까지 보수적 ledger를 실행해 공통 aqueous-resource 제한 아래 실제로 threshold를 넘는지 확인한다. 도달하지 못하면 제한된 source rate를 임의로 외삽하지 않고 그 interval을 `out_of_scope`로 종료한다. 도달을 확인한 경우 첫 substep에서 그 시각까지 source law를 적용하고, 두 번째 substep에서는 갱신된 재고를 초기값으로 삼아 이미 seed된 phase에 growth/dissolution law를 적용한다. 두 substep 모두 caller interval의 saturation ratio를 유지한다. 결과는 event 시각, 적용 law, 각 substep의 ledger digest와 element/charge residual을 기록한다. 각 interval은 계산 성공 후에만 history에 반영되어 실패한 interval의 일부 결과는 정상 이력으로 내보내지 않는다.

## 호출 순서

1. 사용 조건에 맞는 초기 aqueous species와 후보 neutral solid reaction record를 준비한다. 모든 상 반응은 전하 및 원소 조성이 닫혀야 한다.
2. 각 phase에 대해 적용성이 검토된 nucleation molar-source law와 seeded growth/dissolution law를 제공한다.
3. 시간축을 gap 없이 나누고 interval마다 정확히 한 번씩 모든 후보 phase의 saturation ratio를 제공한다. 해당 source, unit, 시간축, 온도, 기준상태와 Evidence digest를 검토한다.
4. 계산 결과의 `history`에서 각 knot의 aqueous/solid inventory, 핵생성 적용 상태, 적용 속도, threshold event split 기록, ledger 결과 digest, element/charge residual을 확인한다. `maximum_total_ledger_evaluations`와 `maximum_seed_threshold_splits_per_interval`을 계산 전에 설정한다. 하나라도 interval ledger가 계산되지 않으면 해당 interval의 부분 결과는 history에 commit하지 않는다.

## 제한

- Interval 안의 saturation은 고정되며, source law와 seeded law는 threshold event 시각에서 바뀐다. interval 내부의 speciation/saturation feedback은 계산하지 않는다.
- Event 시각 식은 caller가 지정한 일정한 molar source에 대해서만 정확하다. 경쟁 용존 재고 제한이 event를 늦추는 조건은 현재 모델 범위 밖으로 fail-closed 처리한다.
- 상 후보 자동 발견, 열역학 평형 판정, 유도시간·입자 population balance, 표면 핵 밀도, morphology, scale 보호성 또는 벽 coverage는 계산하지 않는다.
- spatial transport, 유동, moving geometry, aperture 변화, 부식률, 수명, 확률·위험도 및 qualification은 이 API의 결과가 아니다.
- law calibration과 applicability는 caller 책임이다. 본 계산은 독립적인 물리 검증을 대신하지 않는다.

## 관련 계약

- 입력: `CreviceNucleationKineticHistoryRequest`
- 핵생성 law: `CreviceMolarNucleationLaw`
- Evidence가 결합된 성장 law: `EvidenceBoundSaturationGrowthLaw`
- interval saturation: `NucleationSaturationInterval`
- evaluator: `solve_crevice_nucleation_kinetic_history`

수치 테스트는 아직 실행하지 않았다.
