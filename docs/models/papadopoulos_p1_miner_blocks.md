# Papadopoulos P1 block별 선형 Miner 누적

## 목적

`fatigue.papadopoulos_p1_miner_blocks`는 caller가 이미 분해·검토한 block별 닫힌 응력 cycle을 유한 방향 Papadopoulos P1 계산에 전달하고, 공통 재료 P1–수명 곡선에서 얻은 block별 수명으로 Miner fraction `n_i/N_i`를 구성한 뒤 caller 선택의 선형합을 계산한다. 이 API는 P1 fatigue-limit screen 및 P1–수명 mapping을 block ledger에 연결한다.

## 계산 단계와 lineage

1. 각 block에는 독립 P1 입력, 고유 ID, fractional/equivalent cycle count를 넣는다.
2. 요청 전체에서 모든 방향×시간 표본 작업량을 먼저 제한한다.
3. 각 block의 P1 parameter를 계산하고 common material-condition P1–life curve에 log-log 보간한다. curve 외부 값은 거부한다.
4. block별 `n_i/N_i`를 기록하고 `math.fsum`으로 누적한다. history, calibration, curve digest를 각 block 결과에 남긴다.

## 공개 근거 및 caller 가정

P1 하중 parameter는 Papadopoulos의 고주기 integral criterion에 기반한다. block별 수명은 caller가 제공한 시험곡선에서만 얻고, 변수 진폭 이력의 누적은 caller가 명시적으로 선택한 선형 Miner 규칙을 사용한다. cycle-counting 또는 상호작용 법칙을 자동 선택하지 않는다.

- Papadopoulos, I. V. (1995), “A high-cycle fatigue criterion applied in biaxial and triaxial out-of-phase stress conditions,” *Fatigue & Fracture of Engineering Materials & Structures*, 18, 79–91. [DOI: 10.1111/j.1460-2695.1995.tb00143.x](https://doi.org/10.1111/j.1460-2695.1995.tb00143.x)
- 모델 ID: `fatigue.papadopoulos_p1_miner_blocks`

## 사용 제한

P1 integral은 caller의 유한 방향 quadrature 근사라 연속 방향 적분 정확도나 오차상한을 보장하지 않는다. 입력 cycle 분해와 반복횟수, cycle별 P1 equivalence, 동일 재료·시험조건 curve, 선형 Miner 법칙 및 합산 사용 목적을 모두 caller가 검토한다. 상호작용, sequence effect, mean-stress relaxation, 임계 Miner 손상도, 수명 산포/확률, extrapolation, code acceptance 및 재료 qualification은 범위 밖이다. 누적 값은 probability가 아니다.

## Python API

```python
from matintegrity.papadopoulos_p1_miner_blocks import (
    PapadopoulosP1CycleBlock,
    PapadopoulosP1MinerBlocks,
    evaluate_papadopoulos_p1_miner_blocks,
    specifications,
)

spec = specifications()[0]
request = PapadopoulosP1MinerBlocks(...)
result = evaluate_papadopoulos_p1_miner_blocks(request)
```

이 모듈은 standalone이다. 프로젝트 중앙 registry/catalog/schema에 자동 등록되지 않는다.
