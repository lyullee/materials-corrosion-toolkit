# 고정 CO₂ 퓨가시티 탄산계 평형

`chemistry.fixed_fugacity_carbonate_equilibrium`은 사용자가 공급한 일정 CO₂ fugacity, 용매 조성에 맞는 Henry 용해도 계수, 활동도 평형상수와 측정 총알칼리도로 수용액 pH 및 `CO₂*`, `HCO₃⁻`, `CO₃²⁻`, `H⁺`, `OH⁻`를 푼다. USGS PHREEQC 문서는 기상 용해도 계산에 이상기체 Henry 관계 또는 비이상기체 Peng–Robinson 방법을 구분하고, 고압에서 fugacity 계수의 영향을 설명한다. 이 독립 구현은 해당 인터페이스 경계를 참고하되 EOS를 구현하거나 PHREEQC 코드를 복사하지 않는다. [USGS gas-phase reference](https://water.usgs.gov/water-resources/software/PHREEQC/documentation/phreeqc3-html/phreeqc3-17.htm), [USGS high-pressure CO₂ example](https://water.usgs.gov/water-resources/software/PHREEQC/documentation/phreeqc3-html/phreeqc3-84.htm).

## 계산 관계

호출자가 제공한 Henry coefficient convention은 `C_CO2star = H_CO2 × f_CO2`이며, 단위는 `(mol/L)/Pa`와 Pa로 고정한다. 중성 용존 `CO₂*`의 1 mol/L 표준상태 활동도는 `CO₂*` 몰농도를 표준농도로 나눈 값으로 둔다. 주어진 pH 활동도에 대해 아래 질량작용 관계와 탄산계 물질수지를 사용한다.

```text
a_H = 10^(-pH)
a_HCO3 = K1 × a_CO2star / a_H
a_CO3 = K2 × a_HCO3 / a_H
TA = [HCO3-] + 2[CO3--] + [OH-] - [H+]
```

모든 입력 gamma와 K는 같은 온도 및 activity standard state에 맞아야 한다. 탄산+물 알칼리도 함수가 pH에 대해 단조 증가한다는 범위 안에서 사용자 pH 구간의 root를 이분법으로 찾는다. 종료 조건은 명시적 pH 폭 또는 절대 알칼리도 closure 허용오차다. 허용오차를 달성하지 못하면 계산값을 정상 결과로 반환하지 않는다.

## 필수 입력과 lineage

- Henry coefficient, gas-fugacity observation, 총알칼리도 측정과 활동도 평형상수 각각의 provider ID/revision, configuration digest, record digest, evidence.
- 퓨가시티와 Henry convention 확인, 고정 퓨가시티 reservoir 가정, 같은 용매 조성인지에 대한 review ID.
- 총알칼리도 측정 단위·불확도 기준, 탄산-only 가정, activity scale에 대한 review ID.
- 시료 및 Henry record의 일치하는 `solvent_composition_sha256`, CO₂ fugacity(Pa), 온도 허용차, pH 검색 구간, pH/closure tolerance와 반복 상한.

온도 mismatch는 자동 보정하지 않고 `needs_data`로 처리한다. pH 범위에서 root가 bracket되지 않으면 `out_of_scope`이며 해당 상태를 계산 성공으로 바꾸지 않는다. 총알칼리도 불확도만 pH에 전달하는 1차 국부 민감도 `U_pH ≈ U_TA / (dTA/dpH)`를 반환한다. 이 추정은 같은 입력 K, gamma, fugacity와 Henry 계수를 고정하며 해당 입력 및 model uncertainty를 포함하지 않는다.

## 적용 한계

이 계약은 fugacity가 일정한 외부 reservoir와 평형을 가정한다. 유한 headspace의 기체 몰수 보존, 기액 부피·압력 상호변화, fugacity coefficient/EOS, 염수에서 Henry 계수나 activity를 추정하는 일은 수행하지 않는다. 실제 fugacity, 온도·염도별 Henry 계수와 activity parameters는 사용자가 검토한 공급자로 제공해야 한다. 용존 종은 균질 탄산계 평형 계산이지 계면 pH, 전달 제한, scale/FeCO₃ 형성, 부식속도, 손상, 수명, 합격 또는 고장확률이 아니다. 비탄산 buffer가 유의한 용액에는 적용할 수 없다.

NIST Chemistry WebBook의 CO₂ Henry 자료는 표시 단위가 `mol/(kg·bar)`이며 자체 권리 표시도 따로 있다. 이 프로젝트는 그 표의 수치나 회귀식을 재배포하지 않는다. 사용자가 선택한 값을 허용된 공급자·단위변환·용매 기준과 함께 전달해야 한다. [NIST SRD 69 CO₂ Henry data](https://webbook.nist.gov/cgi/cbook.cgi?ID=C124389&Mask=3FF0).

## 가중 입력 시나리오 앙상블

`chemistry.fixed_fugacity_carbonate_scenario_ensemble`은 각각 완전한 기존 평형 입력인 `FixedFugacityCarbonateScenario` 행을 순서와 digest와 함께 보존한다. 각 행은 독립적으로 검토된 퓨가시티, Henry record, 활동도 상수, 알칼리도 및 출처 lineage를 제공해야 한다. 같은 asset/location/sample identity, 양의 합이 1인 정규화 가중치, 공통 시료 범위 review와 가중치 review가 필요하다. 앙상블은 알칼리도만 변하거나 물성·퓨가시티·조성의 결합 시나리오를 모두 표현할 수 있다.

모든 행이 계산되어야 가중 평균, 관측 행의 최소·최대, 누적 가중치 역경험분포의 5%·95% 분위수를 돌려준다. 한 행이라도 미해결이거나 적용범위 밖이면 부분 집계를 반환하지 않는다. 분위수는 보간하지 않고 누적 가중치가 목표를 처음 넘는 행의 값이다. 두 weight meaning은 호출자 시나리오 질량 또는 호출자 지정 입력분포의 질량을 뜻하며 고장확률·사건빈도·부식률 분포로 재해석하지 않는다. 결과는 수용액 상태 민감도만 요약하며 부식률이나 손상으로 변환하지 않는다.

Registry 예제는 합성 두 점 알칼리도 입력이며 물성 데이터가 아니다. batch74에 이 경로의 회귀와 공통 예제 로딩을 등록했으며 테스트 실행 및 Nurion 제출은 하지 않았다.

## 정확 시각 탄산 평형 이력

`chemistry.fixed_fugacity_carbonate_history`는 정렬된 각 시각과 대응 `FixedFugacityCarbonateEquilibrium` 요청을 같은 asset/location의 이력으로 순차 계산한다. 각 시점은 독립적으로 caller가 공급한 CO₂ fugacity, Henry 계수, 용매 조성 digest, 활동도 평형상수와 측정 알칼리도를 사용한다. 온도·공급자·원자료 계보는 시점별 원 요청에 남는다. 하나라도 `needs_data` 또는 `out_of_scope`이면 이후 절점을 계산하지 않고 완전히 계산된 prefix와 실패 sample/time/status를 반환한다. 시간 사이 보간, gas inventory conservation, kinetics, species/phase discovery, scale 성장 또는 corrosion rate를 만들지 않는다. Clock/sample 정렬 검토와 RunContext asset/location/time basis 일치가 필요하다. 합성 registry input은 example JSON에 추가했으며 실행 검증은 하지 않았다.

후속 검증에서는 단일 점과 같은 상태 반복, 절점별 fugacity/알칼리도 변화, 두 번째 점 실패 시 prefix 길이, missing clock review, 시간 중복/역순, context mismatch, point budget 초과, Henry solvent digest 불일치, 온도 mismatch, pH root 미브라켓을 별도 확인한다. 단일점 solver의 closure·bracketing 검증과 이력 sequence/prefix 검증을 분리한다. 구현 테스트와 수치 실행은 아직 수행하지 않았다.

## 합성 예제와 검증 상태

`examples/fixed_fugacity_carbonate_equilibrium.py`는 `H=1e-7 (mol/L)/Pa`, fugacity 100 kPa, `K1=1e-6`, `K2=1e-9`, `Kw=1e-14`, gamma 1 및 alkalinity 0.102 mol/L을 넣는 합성 폐형식 사례다. 기대상태는 pH 7, `CO₂*=0.01 mol/L`, `HCO₃⁻=0.1 mol/L`, `CO₃²⁻=0.001 mol/L`이며 시험자료나 추천 물성값이 아니다. batch64는 이 해석 기대값, 불확도 민감도, review gate, temperature mismatch, bracket 실패와 Registry JSON 경계를 검사한다. batch74는 시나리오 입력 앙상블과 미해결 행의 집계 차단을 추가로 명세한다. 구현 회귀는 아직 실행하지 않았다.
