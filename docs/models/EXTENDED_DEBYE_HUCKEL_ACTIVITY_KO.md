# Caller 파라미터형 확장 Debye–Hückel 활동도 계수

## 목적

`chemistry.aqueous_extended_debye_huckel_activity`는 완전하다고 검토된 수용액 몰랄 농도 목록과 caller가 공급한 온도·용매별 계수 및 종별 이온 크기 파라미터로 단일 이온 활동도 계수를 계산합니다. 기존 Davies 식과 달리 이온별 크기 항을 입력으로 받습니다. SIT·Pitzer 데이터베이스를 포함하거나 그 방법을 대체하지 않습니다.

## 계산식 및 단위

구현하는 식은 다음과 같습니다.

\[
\log_{10} \gamma_i = -\frac{A z_i^2 \sqrt I}{1+B a_i\sqrt I}, \qquad
I = \frac{1}{2}\sum_j m_j z_j^2
\]

- `m_j`, `I`: 물 1 kg 기준 몰랄농도, mol/kg-water
- `z_j`: 무차원 정수 전하수
- `a_i`: 종별 이온 크기 파라미터, nm
- `A`: `(kg/mol)^0.5`
- `B`: `nm^-1 (kg/mol)^0.5`
- `gamma_i`: 무차원 활동도 계수

위 단위 정의로 분모의 `B a_i sqrt(I)`는 무차원입니다. 결과의 몰랄 표준상태 활동도는 `a_i = gamma_i * m_i / (1 mol/kg-water)`로 정규화되며, 이 구현은 `dimensionless_activity`에 그 수치값을 반환합니다. 무전하 용질은 `gamma=1` 관례를 사용하며 염석 효과는 다루지 않습니다.

## API 및 입력 계보

- 모듈: `matintegrity.models.extended_debye_huckel_activity`
- 요청: `ExtendedDebyeHuckelActivityInput`
- 종 입력: `ExtendedDebyeHuckelSpecies`
- 함수: `extended_debye_huckel_activity_coefficients`
- API ID: `chemistry.aqueous_extended_debye_huckel_activity`

요청의 A, B, 이온강도 상한 및 온도는 caller가 출처와 적용범위를 확인해 제공해야 합니다. 계수 제공자 ID·revision·구성 digest·parameter-record SHA-256은 같은 ID 및 SHA-256을 가진 `Evidence`와 일치해야 합니다. 각 하전 종에는 양의 `ion_size_parameter_nm`과 SHA-256이 확인되는 Evidence가 필요합니다. 모델은 누락된 이온 크기, A/B 값, 종 또는 parameter record를 추정하지 않습니다.

## 실패 폐쇄 조건

- 완전 이온 목록, 전하수지 허용오차, 몰랄 이온강도 정의, 식의 적용성, 온도·용매별 A/B 계수 계보, 활동도 표준상태 검토가 모두 확인되지 않으면 `needs_data`를 반환합니다.
- 계산 이온강도가 caller가 Evidence와 함께 검토한 상한보다 크면 `out_of_scope`를 반환합니다. 자동 외삽하거나 다른 모델로 대체하지 않습니다.
- 몰랄 전하 잔차가 입력 허용오차를 넘으면 `needs_data`를 반환합니다.
- 비유한 이온 재고, 유효하지 않은 분모 또는 IEEE-754에서 표현할 수 없는 활동도 계수는 계산 결과로 승격하지 않습니다.
- parameter provider의 자료 적합성과 혼합 용액에서의 종별 이온 크기는 caller가 독립 확인해야 합니다. 모든 계산에서 단일 이온 활동도에 대한 convention이 필요합니다.

## 과학적 경계

식은 USGS PHREEQC Version 3 설명서의 수용액 활동도 모델 중 Debye–Hückel 이온 크기 항을 참고해 독립적으로 구현했습니다. 이 구현은 식의 계산 형태만 제공하며, PHREEQC 코드·parameter database·종별 표·보정값은 복사하거나 포함하지 않습니다. 식의 문서화 근거는 PHREEQC Version 3 매뉴얼의 `SOLUTION_SPECIES` 설명과 extended Debye–Hückel 관련 설명입니다. [USGS, *Description of Input for PHREEQC Version 3*](https://water.usgs.gov/water-resources/software/PHREEQC/Phreeqc_3_2013_manual.pdf)

이 API는 열역학적으로 검증된 범위를 스스로 정하지 않습니다. 결과는 해당 parameter set에서 검토된 지원 영역에 한해 사용해야 합니다. 고농도 전해질, 다중 액상/고체 평형, 이온쌍 발견, CO₂ 가스 용해도, 반응속도, 부식률 또는 재료 수명은 계산하지 않습니다. neutral CO₂의 염석 거동도 구현하지 않습니다.

## 라이선스·배포 경계

수식과 단위는 기술적 설명을 인용해 재작성했으며 문장, source code, 데이터베이스, 표 또는 계수값을 포함하지 않습니다. A, B, 이온 크기 및 그 배포 권리는 caller가 각자의 출처별 조건에 따라 확보해야 합니다. 본 API의 source citation은 기술적 계보를 보존하기 위한 것이며 데이터 재배포 허가를 대신하지 않습니다.
