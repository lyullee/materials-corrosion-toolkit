# Itoh 비비례 변형률 파라미터

## 목적

`fatigue.itoh_nonproportional_strain_parameter`는 한 번의 caller 검토 완료된 폐주기 tensor-strain 이력에서 비비례성 지표를 계산하고, caller가 제공한 재료 계수와 principal-strain range를 합성해 조정 변형률 범위를 반환한다. 변형률 tensor 방향이 주기 중 회전하는 경로에서 비비례 cyclic hardening을 표현하는 제한된 계산 경로다.

## 계산 정의

각 시간 표본에서 대칭 변형률 tensor의 주값과 주방향을 구한다. 가장 큰 절대 주변형률을 `εI(t)`로 두고, 최대 `εI` 표본의 주축을 기준축으로 사용한다. 주축은 방향 부호가 없는 선으로 취급하므로 두 주축 사이 사인 항은 `sqrt(1 - |u_ref · u(t)|²)`로 평가한다. 시간 적분은 입력된 시각에 대한 사다리꼴 근사다.

`fNP = (π/2) · [∫ εI(t) sin(θ(t)) dt] / [T · εI,max]`

`ΔεNP = (1 + α fNP) · ΔεI`

여기서 `T`는 주기 길이, `θ`는 기준축과 해당 표본 주축의 최소 선-각도, `α`는 재료 조건에 맞춘 caller 제공 계수다. `ΔεI`는 같은 source digest로 연결한 caller-provided 최대 주변형률 범위다. 현 API는 이 range를 다시 구성하지 않는다. 이는 서로 다른 주값 branch와 방향 해석을 입력 tensor만으로 묵시적으로 선택하지 않기 위한 의도적 경계다.

## 입력과 검토 요건

- 한 주기의 모든 tensor 표본, sample ID, 시각을 원래 순서대로 제공한다. 첫 시각은 0, 끝 시각은 `T`이며 첫 tensor와 마지막 tensor는 정확히 일치해야 한다.
- 성분 순서는 `[xx, yy, zz, xy, yz, zx]`이고 전단 성분이 tensorial인지 engineering인지 명시한다.
- tensor 이력, `ΔεI` 입력, 재료 계수 `α`는 Evidence/source digest로 고정한다. 재료 조건과 계수 적용성을 caller가 확인한다.
- 주축 최대/최소 주값의 절대 크기가 같은 표본은 양의 최대 주값 주축을 결정론적 동률 규칙으로 선택한다. 주축이 중복 고유값으로 유일하지 않은 경우 해당 축 선택을 caller가 별도 검토하지 않으면 `needs_data`다.
- `α`는 caller 교정값이며 음수값도 표현할 수 있다. 계산된 보정 multiplier는 반드시 양의 유한값이어야 한다. 보정 자료의 동일 재료·열처리·온도·변형률 조건 및 계수 정의를 확인해야 한다.

## 출력 해석

결과는 무차원 strain range와 입력/교정 lineage를 반환한다. 사다리꼴 적분은 표본 기반 근사이며 표본 사이의 주축 회전 및 진폭 극값을 추정하지 않는다. 균일한 표본 또는 정밀도 기준을 보장하지 않는다. 결과를 수명·허용치·안전 계수로 해석하지 않는다.

## 제외 범위

이 API는 주기 분리, rainflow/cycle counting, 다른 주기 간 손상 누적, fatigue-life curve mapping, creep-fatigue interaction, notch/plasticity correction, calibration transfer, uncertainty, 실험적 validation, acceptance 또는 재료 qualification을 수행하지 않는다. 기존 caller 제공 strain-life curve나 Miner workflow에 연결할 때는 같은 재료 조건과 `ΔεNP` 정의를 명시적으로 검토해야 한다.

## 기술 근거와 구현 독립성

기술 배경은 Itoh, Sakane, Ohnami, Socie의 Type 304 비비례 저주기 피로 기준 및 후속 공개 비비례 하중 연구를 참고한다. [원 논문 DOI](https://doi.org/10.1115/1.2804541), [저자 연구 목록](https://mech.u-fukui.ac.jp/~itoh/itoh/itoh.htm), [공개 다축 변형률 범위 연구](https://doi.org/10.1299/jmmp.5.230). 이 프로젝트는 수식의 기능적 의미만 독립 구현하며 원문 문장, 표본 자료 또는 파라미터를 포함하지 않는다. 재료 계수와 strain range는 전부 caller 입력이다.
