# 스케일 내 반응–확산과 혼합전위 연립 계산

## 모델 식별자와 목적

`integration.wet_co2_scale_diffusion_electrode_mixed_potential`은 caller가 제공한 고정 두께 스케일의 유효 확산계수 및 1차 체적 반응률과, 하나의 환원성 용존종을 소비하는 Butler–Volmer 환원 분기들을 함께 풀어 정상 농도 분포와 공통 금속 혼합전위를 계산합니다. 각 시간점은 독립 정상상태로 취급합니다. 이 계산은 실측 부식률, 재료 적합성 판정 또는 수명 예측이 아닙니다.

## 계산 개요

스케일을 두께 방향으로 등간격 유한체적으로 나눕니다. 각 체적의 정상 물질수지에는 이웃 체적 확산, caller가 지정한 `k c` 형태의 균일 체적 소비, 액상/스케일 경계의 전기화학 소비가 포함됩니다. 벽면 농도는 첫 셀 중심에서 계면까지의 반 셀 확산 저항과 Butler–Volmer 환원 소비를 연립해 구합니다. 양극 및 음극 분기의 전류 합이 0이 되는 금속 전위를 caller가 지정한 bracket 안에서 수치적으로 풉니다.

각 산화 분기의 비음 전류를 전자수와 Faraday 상수로 반응 진행 플럭스로 변환한 뒤 caller 금속 화학양론, 몰질량 및 밀도로 명목 균일 후퇴율을 계산합니다. 환원종 물질수지 잔차와 전류 잔차를 함께 반환합니다.

## 필수 caller 입력과 데이터 증거

- 운전점별 절대 온도, 스케일 두께, 셀 수, 유효 확산계수, 체적 1차 반응 상수, 벌크 및 기준 농도
- 공통 전위 기준과 bracket, 반응별 평형전위·교환전류밀도·전자수·전달계수
- 양극 금속 반응 진행도당 금속 원자수, 금속 몰질량 및 밀도
- 환원 분기별 용존종 소비 화학양론, 모든 분기의 종 식별자
- 공급자 ID/revision, 구성 해시와 운송·전극 입력에 대한 Evidence
- 고정 형상 패치, 모델식, 공통 등전위/무옴저항, 정상상태 및 계산 사용 권한의 검토 표시

검토 표시가 빠지면 `needs_data`를 반환합니다. 농도 분포가 비음이 아니거나 전위 bracket 내 전류 영점이 성립하지 않으면 해당 knot까지의 결과와 실패 위치를 `out_of_scope`로 반환합니다. 공급자 입력의 사실성이나 적용 가능성은 코드가 인증하지 않습니다.

## 적용 범위와 제한

- 1차원 평판 스케일, 고정 기하, 일정한 caller 유효 확산계수, 균일 1차 체적 sink만 포함합니다.
- 모든 전극 분기는 하나의 공통 금속 전위를 사용하며 용액 저항 강하, 이중층 충전, 부동태화·석출 변화, 다종 수송 및 전위/농도 의존 파라미터 추정을 계산하지 않습니다.
- 시간점 사이 보간이나 동적 적분, 스케일 성장·용해에 따른 형상 갱신, 유동 모델, 국부 부식/공식, 안전성 판정 및 불확실도 전파를 계산하지 않습니다.
- 반환하는 금속 후퇴는 caller가 선언한 Faraday 화학양론에 따른 명목 균일값입니다.

## 독립적으로 참고한 공개 근거

아래 자료는 전기화학 부호 관례·기본 상수 확인에만 사용했습니다. 이 모델의 제어체적 행렬, 입력 계약, 연결 방식, 경계와 한계는 이 프로젝트의 독립 구현이며 출처 문장을 복사하지 않았습니다.

- Butler, J. A. V., “The mechanism of overvoltage, and its relation to the composition of the surface,” *Transactions of the Faraday Society* 28 (1932), 379–382. [DOI: 10.1039/TF9322800379](https://doi.org/10.1039/TF9322800379)
- Erdey-Grúz, T. and Volmer, M., “Zur Theorie der Wasserstoff Überspannung,” *Zeitschrift für Physikalische Chemie* 150A (1930), 203–213. [DOI: 10.1515/zpch-1930-15020](https://doi.org/10.1515/zpch-1930-15020)
- NIST, *2022 CODATA recommended values of the fundamental physical constants*, Faraday constant. [NIST publication](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=958143)
- IUPAC Gold Book, “Faraday constant.” [F02325](https://goldbook.iupac.org/terms/view/F02325)

이 계산은 공개 참고문헌만으로 보편 계수나 운전 데이터를 제공하지 않습니다. 실제 재료·환경에 대한 매개변수와 데이터 이용 권한은 caller가 별도로 확보하고 검토해야 합니다.

## Python API

```python
from matintegrity.wet_co2_scale_diffusion_electrode import (
    WetCo2ScaleDiffusionElectrodeHistory,
    evaluate_wet_co2_scale_diffusion_electrode_mixed_potential,
)

result = evaluate_wet_co2_scale_diffusion_electrode_mixed_potential(
    request,
    scipy=scipy,
)
```

선택한 `scipy.optimize.brentq` 구현이 혼합전위 근을 찾는 데 사용됩니다. 스케일 확산의 삼중대각 시스템은 밀집 행렬을 만들지 않고 직접 풉니다.

## 카탈로그 연결 메타데이터

- Model ID: `integration.wet_co2_scale_diffusion_electrode_mixed_potential`
- Schema version: `matintegrity.wet_co2_scale_diffusion_electrode_mixed_potential.v1`
- Source ID: `finite_volume_scale_first_order_sink_with_butler_volmer_mixed_potential` — 이 프로젝트의 계산식/유한체적 이산화
- Source ID: `butler_erdey_gruz_volmer_electrode_kinetics` — 독립 공개 전기화학 참고자료
- Source ID: `nist_codata_faraday_constant_2022` — Faraday 상수 출처
- Caller Source ID: `caller_scale_reaction_diffusion_transport_parameters`
- Caller Source ID: `caller_scale_anodic_butler_volmer_branches`
- Caller Source ID: `caller_scale_cathodic_butler_volmer_branches`
- Caller Source ID: `caller_scale_reactant_and_metal_stoichiometry`
