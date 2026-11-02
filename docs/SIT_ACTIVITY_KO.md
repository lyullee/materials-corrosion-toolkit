# SIT 활동도 계수 API

`chemistry.sit_activity_coefficients`의 입력 계약 `matintegrity.sit_activity_coefficient_input.v2`는 사용자가 전달한 완전한 수용액 종 목록, 온도별 Debye–Hückel 상수 `A`, 방향성 이온 상호작용 계수 `epsilon(i,j)`를 이용해 몰랄 표준상태의 활동도 계수를 계산한다. 파라미터 표를 프로젝트가 배포하거나 자동 추정하지 않는다. 기존 v1 입력을 v2에 암묵 변환하지 않으므로 caller는 Evidence 파일 hash를 명시해야 한다.

## 식과 입력

각 종 `i`에 대해 다음 식을 사용한다.

```text
log10(gamma_i) = -z_i^2 * A * sqrt(I)/(1 + 1.5*sqrt(I)) + sum_j epsilon(i,j) * m_j
I = 0.5 * sum_j(m_j * z_j^2)
```

`m`과 `I`의 단위는 mol/kg water이고 `epsilon`은 kg/mol이다. `A`는 해당 온도와 용매에 맞는 값으로 사용자가 제공하고 Evidence에 연결한다. epsilon은 방향성이 있으므로 `(i,j)`와 `(j,i)`를 별도로 선언할 수 있다. 각 interaction은 source record ID와 그 record가 실린 원자료 Evidence의 SHA-256을 함께 받아야 하며, source ID와 파일 hash는 선언된 `Evidence`에 정확히 일치해야 한다. 이 필드가 원자료 안의 행 bytes를 별도 해시한다는 의미는 아니다. 명시하지 않은 항은 0으로 계산되므로, 해당 상호작용 집합이 목적 조건에서 충분하다는 caller 검토가 필수다. 중성 종도 사용자가 상호작용 항을 제공할 수 있지만 중성종 파라미터를 자동으로 만들지 않는다.

종 목록은 전체 이온수지와 전하수지를 포함해야 한다. 전하 잔차는 입력한 절대 허용치로 점검하며, 이온강도 한계는 사용자가 선언하고 최대 6 mol/kg로 제한된다. 계산 밖 조건은 외삽하지 않고 `out_of_scope`를 반환한다. 누락된 검토 또는 전하수지 문제는 `needs_data`로 반환한다. 이 계산은 평형 speciation, 이온쌍 생성, 상 발견·침전, 파라미터 회귀, 압력 보정, 부식률이나 재료 자격을 대신하지 않는다.

## 구현과 근거

식의 구조는 NEA Thermochemical Database Project의 공개 SIT 방법 설명과 USGS PHREEQC의 SIT 모델 문서를 참고해 별도로 구현했다. 근거 문서의 문장·표·파라미터 값을 소스 코드나 배포 데이터에 복사하지 않는다. 참고 문헌은 방법의 근거이며 특정 염수, 온도, 조성에 대한 사용 허가나 적합성 보증이 아니다. 각 epsilon과 A 값의 권리·출처·온도·용매 범위는 호출자가 기록해야 한다.

- [NEA Thermochemical Database Project, SIT method](https://www.oecd-nea.org/upload/docs/application/pdf/2020-09/tdb2_2020-09-02_11-51-54_735.pdf)
- [USGS PHREEQC 3, SIT data block](https://water.usgs.gov/water-resources/software/PHREEQC/documentation/phreeqc3-html/phreeqc3-46.htm)

실행·수치 비교 검증은 별도 검증 작업에서 수행한다. 이 API 추가만으로 현장 적합성 또는 검증 완료를 주장하지 않는다.

입력 배선 예제는 [`examples/sit_activity_coefficients.py`](../examples/sit_activity_coefficients.py)에 있다. 예제의 모든 수치는 합성값이며 실제 염의 파라미터로 사용할 수 없다.
