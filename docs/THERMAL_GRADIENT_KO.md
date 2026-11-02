# 과도 열전도와 두께방향 열응력

`thermal.transient_conduction_1d`은 평판 또는 원통 반경 방향의 1차원 과도 열전도를 계산한다. `mechanics.through_wall_thermal_stress`는 계산되거나 측정된 두께방향 온도 분포를 선형 탄성 단면 평형으로 변환한다. 두 계산기는 서로 독립적으로 호출할 수 있으며 `examples/thermal_gradient.py`가 명시적인 결합 예를 제공한다.

이 경로는 온도장과 탄성 열응력의 선별 계산이다. 압력·노즐·불연속부·잔류응력·소성·크리프·균열·피로·규격 분류와 기간 고장확률을 자동으로 포함하지 않는다.

`matintegrity.bind_thermal_temperature_profile()`은 계산된 `thermal.transient_conduction_1d` AssessmentResult에서 선택한 정확한 시간 행을 열응력 요청에 바인딩한다. 요청 위치는 thermal cell-centre와 정확히 일치해야 하며, 자산·위치·time basis와 전체 결과 SHA를 응력 결과에 보존한다. 공간 재등록·보간은 수행하지 않고, 셀 중심과 응력 단면 방향이 같은지 caller 검토를 요구한다.

열응력의 네 기계 물성 profile은 각기 선택적 `property_profile_evidence` 레코드로 출처를 연결할 수 있다. 레코드는 quantity, provider/revision, record ID, source SHA-256 및 일치하는 `Evidence`를 요구하며, 출처를 연결하는 경우 `material_condition_id`도 필수다. 결과에는 위치·재료 상태·값 배열을 정규화한 profile digest와 출처가 quantity별로 기록된다. 출처 레코드가 없으면 `caller_supplied_unprovenanced`로 표시한다. 이 계보는 입력 추적이지 물성의 진위나 재료 적용성 검증이 아니다.

`examples/thermal_gradient.py`는 이 계약의 합성 배선을 보여준다. 각 물성 출처를 `origin="synthetic"`으로 명시하고 계산 결과의 `mechanical_property_lineage`를 출력한다. 숫자는 실제 재료 표가 아니며 설계 판단에 사용할 수 없다.

## 열전도 입력 계약

- 형상은 `planar` 또는 `radial_cylindrical`이고 실제 두께·면적 또는 내외반경·원통 길이를 받는다. 격자 값은 유한체적 셀 평균이다.
- 각 셀은 사용자 재료 ID를 가진다. 열전도율과 체적 열용량은 온도 표로 주며 표 사이만 선형 보간한다. 범위 밖 외삽은 하지 않는다. `ThermalMaterialProperties`는 선택적으로 재료 상태 ID, provider/revision/record, provider 원본 SHA-256 및 일치하는 Evidence를 받는다. 결과에는 정규화 물성표 SHA-256과 원 출처 계보를 포함한다. 계보 미제공 시 출력은 이를 명시적으로 `caller_supplied_without_provider_evidence`로 표시한다.
- 열용량 표를 온도에 대해 적분한 엔탈피를 저장량으로 사용한다. 연속적인 겉보기 열용량 표로 표현한 전이는 사용할 수 있지만 불연속 잠열, 이동 경계와 이력은 지원하지 않는다.
- 좌우 경계는 지정 온도, 부호 있는 지정 열유속, 단열, 또는 대류와 회색복사의 조합이다. 경계 열률의 양수는 계산 영역 안으로 들어오는 열이다.
- 셀별 체적 발열과 분포 대류를 선택적으로 줄 수 있다. 분포 열교환에는 선택적으로 상수 방사율 또는 출력시각별 방사율, 시각별 등온 복사 환경온도를 추가할 수 있으며, 시간 방사율은 구간 안에서 선형 보간한다. 회색표면 복사·환경 형상계수 1·복사 차폐 없음의 적용성 검토를 명시한다. 출력 시각, 셀/재료 ID와 입력 이력은 순서를 보존한다.
- 상변화 또는 온도 의존성을 검토하지 않았다고 선언하면 계산을 `needs_data`로 중지한다. 물성 표 범위 밖이나 비선형 반복 미수렴은 `out_of_scope`다.

후진 Euler와 셀 중심 유한체적 보존식을 사용한다. 온도 의존 물성과 경계·분포 복사는 반복해서 갱신하고 삼중대각계는 이 프로젝트가 작성한 Thomas 알고리즘으로 푼다. 분포 복사는 셀별 대류와 함께 순 열률에 더하며 각 iteration에서 복사 전달계수를 갱신한다. 출력에는 셀 온도 이력, 양쪽 표면 온도와 열률, 저장·발열·분포 대류/복사·경계 에너지, 이산 에너지 잔차와 반복 수가 포함된다. 에너지 잔차는 상쇄된 순열량이 아니라 절대 열기여 합으로 정규화한다. 작은 잔차는 구현된 이산식의 보존 확인이지 공간·시간 정확도나 실험 자격의 증거가 아니다.

## 열응력 입력 계약

두께 위치마다 온도, 기준온도, 시컨트 열팽창계수, 탄성계수, 포아송비와 검토된 탄성 한계를 선형 표로 준다. `uniaxial_plane_stress`는 축방향 자유 열변형을 `E`로, `equi_biaxial_plane_stress`는 동일한 두 면내 응력을 `E/(1-nu)`로 구속한다.

- `resultant_controlled`는 지정한 단위 폭당 막력과 굽힘모멘트를 만족하도록 기준 변형률과 곡률을 푼다.
- `kinematic_controlled`는 사용자가 기준 변형률과 곡률을 직접 준다.
- 각 입력 구간은 12점 Gauss-Legendre 적분으로 단면 합력을 계산한다. 응력 극값과 탄성 한계 사용률은 입력 위치와 적분 위치에서 평가하며 연속 구간 내부의 해석적 최대를 보증하지 않는다.
- 탄성 한계를 넘으면 응력을 잘라내지 않고 `out_of_scope`로 반환한다. 이는 항복 이후의 실제 응력 재분배나 규격 허용 여부가 아니다.

## 자료 연결과 검증 경계

공개 자료 `sbcf36976g`의 고정 리비전에는 77개 원시 CSV와 3개 처리 workbook이 있다. 원시 자료는 215,001개 시간행과 1,290,006개 열전대 관측을 포함한다. 음의 주변온도 초과값 28,161개를 제거하지 않으며 controller의 `Power (1023 Max)`는 전력 W나 열유속으로 바꾸지 않는다. 처리 workbook의 77개 적합 행은 같은 원시 시험을 적합한 결과이므로 추가 독립 실험으로 세지 않는다.

`read_thermal_rod_series`는 원 시계, TC1~TC6, controller setting, 원 파일/멤버 해시와 권리 메타데이터를 반환한다. `read_thermal_rod_fitted_results`는 보고된 경계 ramp·delay, 대류계수, 열전도율, 정상 전력과 오차 필드를 읽되 `same_data_fit` 관계를 표시한다. 원 자료와 처리 표는 공개 source archive와 wheel에 포함하지 않는다.

수학·수치 검사는 다음과 같다.

- 평판 Fourier 셀 평균 해에 대한 12→24→48셀 최대오차는 0.3031, 0.07778, 0.02210 K이며 감소비는 3.90, 3.52다.
- 후진 Euler의 시간간격 0.02→0.01→0.005 s 오차는 2.828, 1.421, 0.7122 K이며 감소비는 1.990, 1.996이다.
- 자유 선형 온도분포의 최대 잔류 응력은 약 `4.34e-8 Pa`, 균일 고정 가열의 기준해 오차는 0이다.
- 공개 rod 시험 `50ss1`은 같은 자료에서 이미 적합된 열전도율·대류·전력·경계 이력을 사용한 외부 유한체적 재현이다. 2,412개 열전대 관측에 대한 RMSE는 약 0.6335 K이고, 50셀/0.4 s와 100셀/0.2 s 결과의 RMS 차이는 약 0.1594 K다. 이는 holdout도 독립 실험 검증도 아니며 계수 식별성과 일반화 성능을 주장하지 않는다.

기계가 읽는 결과는 `validation/thermal_gradient_math.json`에 기록한다.

## Python 사용 예

```python
from matintegrity.registry import default_registry

registry = default_registry()
thermal = registry.run("thermal.transient_conduction_1d", thermal_input)
stress = registry.run("mechanics.through_wall_thermal_stress", stress_input)
```

분포 대류와 회색복사를 함께 넣는 synthetic wiring은 `examples/thermal_distributed_radiation.py`에 있다. 예제의 열전달계수·면적/체적비·방사율·환경온도는 인터페이스 설명용 임의 값이며 설계값이나 검증 자료가 아니다. 복사 활성화 시 `emissivity` 또는 시간 배열과 정렬된 `emissivity_history` 중 하나, `radiative_environment_temperature_K`, `radiation_exchange_basis_reviewed=true`를 제공한다.

전체 결합 예와 검증은 다음 명령으로 재현한다.

```powershell
.\.venv\Scripts\python.exe examples\thermal_gradient.py
.\.venv\Scripts\python.exe scripts\validate_thermal_gradient.py
.\.venv\Scripts\python.exe scripts\inspect_thermal_data.py
```

## 남은 과제

독립 기관·재료·형상의 과도 온도 시험 보류 검증, 물성 불확실성 및 센서 오차 전파, 잠열·이력·열화 물성, 용접 이동 열원, 다층 접촉저항, 비선형 소성·크리프 응력, 압력·구조 불연속·균열과의 결합이 남아 있다. 실제 수명·규격 합격·고장확률은 별도 손상 및 불확실성 모델과 근거가 있어야 한다.
