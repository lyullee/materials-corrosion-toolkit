# Itoh 비비례 strain-life cycle block Miner 연결

`fatigue.itoh_nonproportional_miner_blocks`는 caller가 분해한 다수의 대표 주기 블록 각각을 `fatigue.itoh_nonproportional_strain_life`로 계산한 뒤, 기존 `MinerDamage` 계산기에 모든 블록의 `cycle_count / cycles_to_failure` 항을 전달한다. 새 cycle-counting 규칙이나 손상 법칙을 추가하지 않는다.

## 공통 lineage와 입력

- 블록마다 고유 `block_id`, 고유 cycle ID, 정수 caller cycle count, 그리고 Itoh life request를 제공한다. 블록 순서 및 count 배정은 caller 소유다.
- 모든 블록은 campaign의 동일 `material_condition_id`와 일치해야 한다.
- 모든 요청의 life curve normalized digest, curve source digest, condition descriptor digest, license ID, strain-definition ID가 같아야 한다.
- 모든 블록은 같은 Itoh alpha calibration source ID/digest/value와 같은 tensor shear convention을 사용해야 한다.
- 고정 strain definition은 `itoh_1995_adjusted_nonproportional_principal_strain_range.v1`이다. 다른 strain parameter 정의는 받지 않는다.
- 누적 정수 cycle 수는 정확 표현 한계 `2^53` 이하여야 한다.
- decomposition/count, material/curve consistency, curve rights/use, linear Miner 적용성, sequence-effect 비포함 리뷰가 요구된다.

## 실행 정책

각 block life mapper를 순서대로 평가한다. curve support 밖이거나 한 항목의 입력 검토가 불완전하면 전체 Miner 합계를 보류하고 block별 결과/실패 위치를 보존한다. 모든 block에 유한 양의 cycles-to-failure가 있을 때만 기존 `MinerDamage` 계산기를 호출한다. Miner의 declared limit/margin은 caller가 고른 수치 기준으로만 반환한다.

## 해석 한계

이 API는 caller가 제공한 대표 주기 수와 블록 열거에 대해 선형 Miner 합계를 계산한다. 실제 하중 이력에서 cycle을 찾거나 분해하지 않는다. Sequence effect, load interaction, creep fatigue, 확률, period failure, acceptance, remaining-life extrapolation 또는 material qualification을 추론하지 않는다. 결과가 caller의 damage limit을 넘었다고 해서 자동 불합격/파손으로 해석할 수 없다.

## 기술 근거

Itoh strain parameter/life의 배경은 [원 논문 DOI](https://doi.org/10.1115/1.2804541) 및 [공개 방법 설명](https://doi.org/10.1299/jmmp.5.230)을 참고한다. Miner arithmetic은 기존 프로젝트의 caller-declared `MinerDamage` utility를 재사용한다. 자료의 수치, 곡선 및 cycle counts는 전부 caller 제공이며 문헌 표는 포함하지 않는다.
