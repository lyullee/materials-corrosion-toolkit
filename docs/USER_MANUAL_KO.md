# Materials Corrosion Toolkit 사용 설명서

처음 사용하는 경우 [처음부터 단계별 사용 설명서](GETTING_STARTED_KO.md)를 먼저 읽는다.
모듈 선택·목적·입출력은 [README 전체 API 표](../README.md)와
[757개 상세 단위 모듈 설명서](MODULE_DIRECTORY_KO.md)에서 바로 찾을 수 있다.
배포 이름은 `materials-corrosion-toolkit`, Python import는 `matintegrity`다.
아래는 기존 기능별 상세 노트를 보존한 내용이다.

독립 저장소로 damage/PoF 또는 consequence scenario를 주고받을 때는
[`CROSS_REPOSITORY_EXCHANGE_KO.md`](CROSS_REPOSITORY_EXCHANGE_KO.md)의 의미·단위·digest·receipt 경계를
먼저 적용한다.

## AE·thermal-spray·thermal parameter 자료 준비

AE 위치추정에는 하나의 3D frame과 clock, calibrated sensor 위치, caller-fixed wave speed/support, 검토된
arrival picks와 uncertainty가 필요하다. Thermal-spray 입력은 calibrated field, layer/substrate/batch,
thickness traverse와 reviewed pore geometry/edge/overlap를 제공한다. Thermal parameter 보정은 외부 solver의
baseline prediction·parameter sensitivity·geometry/boundary digest와 정렬된 sensor/time 관측을 제공한다.
[자료 준비와 중단 조건](AE_THERMAL_SPRAY_GRADIENT_KO.md)을 먼저 확인한다.

## 성형·코팅 pull-off·replica 자료 준비

성형 입력은 원/최종 두께, 내측반경, angle, forming mode와 engineering 또는 true 관례 하나를 명시한다.
Pull-off 입력은 dolly/층/substrate/preparation/cure/exposure identity, force·area 또는 별도 provider stress,
uncertainty, calibration/holdout partition과 break-mode component를 제공한다. Replica 입력은 physical site,
frame calibration, segmentation provider, observer review, feature coordinate/area/edge/overlap와 digest를
제공한다. [세부 자료계약과 미추론 범위](FORMING_COATING_REPLICA_KO.md)를 확인한다.

## 단조 인장·음극방식·충격 신호 자료 준비

단조 보정에는 같은 stress/elastic-modulus 단위와 하나의 true 또는 engineering 관례, 검토된 pre-necking
window, 독립 calibration/holdout 시편이 필요하다. 음극방식 조사는 reference electrode calibration과
온도 support, native/on/off/instant-off convention, IR-drop 처리, current 부호·환경·불확도를 명시한다.
계장화 충격은 specimen/notch/orientation, 시험온도, striker/instrument calibration, SI 원신호와 valid
window를 제공한다. [세부 계약과 미추론 범위](PLASTICITY_CP_IMPACT_KO.md)를 확인한다.

## 인증서·진공시험·이종용접 자료 준비

인증서 대조에는 요구조건을 외부에서 제공하고 chemistry/property domain과 단위를 분리한다. Pressure-rise
계산에는 같은 apparatus의 독립 blank/test, 절대압력, known volume, 온도와 불확도가 필요하다. 이종용접
경로에는 양 base material, deposited layer, fusion boundary, WPS/PWHT/service history와 caller review를
입력한다. [자료 준비와 중단 조건](CERTIFICATE_VACUUM_DISSIMILAR_WELD_KO.md)을 먼저 확인한다.

## 마모·경도·인장 자료 준비

Archard 보정에는 같은 접촉 regime의 SI 마모체적·하중·거리·경도와 분리된 calibration/holdout 시편을
넣는다. 경도 보정은 같은 scale과 장비 설정의 인증 기준블록을 사용한다. Offset-yield는 engineering
stress–strain의 단조 증가 branch와 검토된 elastic/pre-necking window를 공급한다. 입력 경계와 해석은
[마모·경도·인장 설명서](WEAR_HARDNESS_TENSILE_KO.md)를 따른다.

## 고분자·충식부식·기준누설

새 세 보정기는 시편·출처·독립성 그룹을 calibration과 holdout에 걸치지 않게 나눈 뒤
사용한다. polymer shift는 동일 formulation/state/endpoint, 충식부식은 동일 material/fluid/
geometry/regime, 기준누설은 동일 instrument/gas/boundary identity를 요구한다. 자료 준비와
결과 해석은 [고분자·충식부식·기준누설](POLYMER_EROSION_LEAK_KO.md)을 따른다. ESCAPE‑1은
`audit_escape1_leak_dataset` 후에도 참조 압력·온도와 release window를 별도 확정하기 전에는
보정기 입력으로 쓰지 않는다.

## 수명 적합과 반복 안정성

Strain–life와 크리프 파단 자료는 먼저 물리 시편·출처·독립성 그룹을 정의하고 calibration과 holdout에 걸치지 않게 나눈다. 정보가 불충분한 runout/censor를 failure로 바꾸지 않는다. Sobol 안정성은 각 replicate의 seed와 완전한 distribution/design/evaluator digest를 동일하게 고정한 뒤 실행한다. 입력 준비와 해석 한계는 [수명·민감도·실가스 계약](LIFE_SENSITIVITY_LEAK_KO.md)에 정리했다.

압력감쇠에 실가스 보정이 필요하면 압력은 absolute Pa, 온도는 K로 변환한 뒤 `thermo.gas_pressure_decay_inputs_from_coolprop` 결과를 `inspection.gas_pressure_decay`에 전달한다. 재고량 변화는 누설 경로나 유량이 아니므로 현장 판정에는 별도 누설모델·계기·절차 근거를 연결한다.

## 누설자속검사 기록

누설자속검사는 `inspection.magnetic_flux_leakage_acquisition_summary`에 자화기 방향·제어 근거, 센서
channel과 측정 축, calibration/lift-off, 기준시편, H/B checkpoint, scan digest와 indication 근거를
입력한다. B/H ratio나 scan span을 포화 판정·결함 치수·합격 결과로 사용하지 않는다. 원 ILI 이상
목록도 raw flux 및 excavation truth가 확인되지 않으면 이 모델의 calibration 자료가 아니다. 자세한
범위는 [누설자속검사 설명](MAGNETIC_FLUX_LEAKAGE_KO.md)을 따른다.

### 처리된 연속 ILI workbook 읽기

`pipeline_ili_data.iter_pipeline_ili_features`에 물리 배관 ID, 고유 검사 회차 ID, provider의 회차
token과 고정 SHA-256을 전달한다. 반환 행은 m·radian SI view이지만 원 파일·행·누락·품질 flag를
보존한다. 먼저 `audit_pipeline_ili_workbook`으로 header, 행 수, 누락·수식·회차 불일치를 확인한다.
수식은 실행하지 않으며 reader가 숫자 위치의 수식을 거절한다. 서로 다른 회차의 행 또는 가까운 좌표를
자동 연결하거나 부식 성장률로 해석하지 않는다. 자세한 계약은
[연속 배관 ILI 자료 설명](PIPELINE_ILI_HISTORY_KO.md)을 따른다.

## 와전류검사 자료와 계산

와전류검사는 `inspection.eddy_current_acquisition_summary`에 절차, probe/주파수, reference standard,
encoded raster와 indication 근거를 넣어 실행한다. DICONDE 원자료는 선택 의존성 pydicom이 설치된
환경에서 `read_eddy_current_diconde`로 읽되 physical specimen ID, source role, frame component 순서와
그 근거를 호출자가 지정한다. 반환된 정수 배열과 rescale metadata를 자동 보정 신호나 결함 판정으로
간주하지 않는다. 전체 예제와 제한은 [와전류검사 설명](EDDY_CURRENT_KO.md)을 따른다.

## 배관 유도초음파 자료 읽기

`science` 확장을 설치한 뒤 `guided_wave_data.list_guided_wave_acquisitions`로 먼저 archive ID와
체크섬을 확인한다. 한 acquisition만 필요하면 `read_guided_wave_acquisition`에 실제 관을 나타내는
`specimen_id`와 acquisition ID를 넣는다. 반환 `signals`는 주파수 오름차순이지만
`source_sheet_frequency_order_Hz`가 원 workbook 순서를 보존한다. 거리축의 반복 표본은 제거하지
말고 `repeated_distance_intervals`와 함께 사용한다. 전압의 baseline 차이·특징량은
`guided_wave_pair_feature_inputs`로 같은 관·archive의 두 reader 결과를 조합한 뒤
`inspection.guided_wave_pair_features`로 계산한다. 주파수·모드·공간창과 반복 거리 정책을 반드시
명시하고 장치 설정과 같은 건강 기준 acquisition을 사용자가 먼저 자격화해야 한다. 실행 예제는
`examples/guided_wave_pair_features.py`다. 세 개 이상의 사전 선택 baseline이 있으면
`guided_wave_reference_ensemble_inputs`와 `inspection.guided_wave_reference_ensemble`로 mean/median
reference, baseline spread와 leave-one-out 변동을 함께 계산한다. baseline source group과 선택 근거를
반드시 기록하고 결과 비를 이상확률이나 임계값으로 사용하지 않는다. 이 API 출력은 잔여두께,
부식률, POD, 검사 합격 또는 수명 결과가 아니다. 전체 범위와 예제는
`docs/GUIDED_WAVE_DATA_KO.md`를 따른다.

## 설치

Python 3.11 이상을 사용한다. 이 디렉터리를 독립 저장소의 루트로 사용한다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[science,thermo,dev]"
.\.venv\Scripts\python.exe -m matintegrity.cli models
```

기본 설치는 NumPy·Pydantic·Pint를 사용한다. 통계 적합·데이터 처리는 `science`, 열역학은 `thermo`, 검증 도구는 `dev`에 포함된다. 선택 기능의 의존성이 없으면 해당 기능 호출 시 설치 필요 오류가 발생한다.

## 입력 작성과 실행

```powershell
.\.venv\Scripts\python.exe -m matintegrity.cli describe corrosion.uniform_forecast
.\.venv\Scripts\python.exe -m matintegrity.cli run examples/uniform_loss.json --out artifacts/result.json
.\.venv\Scripts\python.exe examples/python_composition.py
.\.venv\Scripts\python.exe examples/process_history.py
.\.venv\Scripts\python.exe examples/pod_to_inspection_update.py
.\.venv\Scripts\python.exe examples/material_verification_gate.py
.\.venv\Scripts\python.exe examples/pitting_area.py
.\.venv\Scripts\python.exe examples/burst_prediction_comparison.py
.\.venv\Scripts\python.exe examples/profile_capacity.py
```

각 요청은 `model_id`, `inputs`, `context`로 구성한다. 입력 스키마에 없는 키, 비유한 값, 잘못된 부호·범위는 거절한다. 물성·시험·허용값의 근거는 `context.evidence`에 넣는다. 일반 메모와 파라미터 출처는 `context.metadata`에 보존할 수 있다.

결과를 해석할 때는 값뿐 아니라 `status`, `assumptions`, `notes`, `units`를 확인한다. 예를 들어 부식속도 0이면 단순 선형 모델의 기준 도달 시간이 유한하지 않으므로 JSON에는 `null`과 설명을 반환한다. 무한 설비 수명을 보증하는 값으로 해석하지 않는다.

여러 caller-defined 전기화학 손실 시나리오를 두께 관점에서 비교할 때는 `integration.electrochemical_wall_thickness_scenario_envelope`를 사용한다. 이 기능은 같은 기준선·material condition·시간 절점을 가진 각 완전 결과에서 절점별 두께/margin extrema와 witness만 제공한다. finite scenario set 밖을 보증하거나 확률을 부여하지 않는다. 상세 wiring과 required review는 [시나리오 안내](ELECTROCHEMICAL_WALL_THICKNESS_SCENARIO_ENVELOPE_KO.md)를 따른다.

계산된 전기화학 금속손실을 measured wall thickness에 연결할 때는 `integration.electrochemical_metal_loss_wall_thickness_history`를 사용한다. 첫 금속손실 구간 시작과 동일한 Evidence-bound baseline, 반응별 공통 면적 적합성, 전체 반응 커버리지, effective density 근거와 적용성 review를 제공해야 한다. 결과는 공급된 기간의 두께 margin 및 crossing interval bracket이며 잔여수명이나 부식률 예측이 아니다. [전용 wiring 안내](ELECTROCHEMICAL_WALL_THICKNESS_KO.md)를 따른다.

공정 모니터링 시스템으로 결과를 보낼 때는 `monitoring_record(result)`를 사용한다. 반환 JSON은
`MonitoringAssessmentRecord`로 다시 검증할 수 있고 완전 assessment digest가 값·모델·확률 의미의
변조를 차단한다. `source_digest`는 원 센서 파일 hash가 아니라 assessment snapshot digest다.
모니터링 score·threshold·alarm과 이 레코드를 별도 객체로 유지하며 `computed`를 정상으로,
통계 alarm을 고장확률로 바꾸지 않는다. 상세 내용은
[공정 모니터링 교환계약](MONITORING_EXCHANGE_KO.md)을 따른다.

온도별 운전압력 경계를 확인할 때는 `structural.pressure_temperature_envelope`에 검토한 경계 knot와
운전점을 SI 단위로 전달한다. 경계 내용을 SHA-256으로 고정하고 적용성 근거를 남긴다. CoolProp
출력이나 공정 이력값을 사용할 때도 압력이 절대압인지 차압인지 상류에서 먼저 맞춰야 한다. 계산기는
지원온도 밖을 외삽하지 않으며 공급 경계 내부 표시는 규격 합격이 아니다. 자세한 내용은
[압력–온도 운전경계 계약](PRESSURE_TEMPERATURE_ENVELOPE_KO.md)을 따른다.

반복 검사 두께로 한 CML의 일정 손실률을 갱신할 때는
`reliability.bayesian_linear_thickness_update`를 사용한다. prior 두께·손실률의 평균·표준편차·
상관과 근거, 관측별 시간·두께·측정 표준편차·방법·교정·source group을 입력한다. 보정에 쓸
행은 `update`, 모델 확인용 행은 미리 `holdout`으로 고정한다. holdout 값은 posterior를 바꾸지
않는다. 측정오차가 독립이라는 근거가 없으면 update 행 순서의 전체 공분산을 공급한다.
요구두께 미달확률은 요청한 각 시점의 조건부 상태확률일 뿐, 검사기간 중 최초 미달이나
고장확률이 아니다. 입력·출력과 제한은 [Bayesian 두께 갱신](BAYESIAN_GROWTH_KO.md)을 따른다.

검사 사이 열화 변동을 무시할 수 없다면 `reliability.linear_thickness_state_space_update`에 검토된
2×2 과정잡음 공분산률을 공급한다. 관측은 엄격한 시간순서로 주고, `update`만 상태를 갱신하며
`holdout`은 one-step-ahead 잔차에만 사용한다. 현재 모델은 과정잡음을 자료에서 자동 적합하지 않고
독립 측정오차만 받는다. 결과의 미래 임계두께 미달확률은 특정시점 상태확률이다.

평가시점 생존을 조건으로 한 잔여두께-비음수 손실률의 자격 있는 공동 표본이 있다면
`reliability.sampled_linear_thickness_first_passage`로 선형 최초 임계도달 곡선을 만들 수 있다.
이미 임계 이하인 행을 삭제해 조건을 맞추지 말고, 분포·표본설계와 공동 표본 hash를 보존한다.
계산된 선형 Gaussian Bayesian 결과는 `gaussian_thickness_posterior_sample_inputs` 어댑터와
`reliability.gaussian_thickness_posterior_sample_design`으로 공동 표본화할 수 있다. seed와 고정
알고리즘을 기록하고 비음수 손실률·평가시점 생존 조건을 명시적으로 검토한다. 이 경로는 posterior
모형이나 현장 타당성을 자동으로 검증하지 않는다. 완성 표본은
`sampled_linear_thickness_first_passage_inputs`로 최초도달 입력에 연결한다.

성분·경도처럼 요구조건을 비교하는 모델은 `values.outcome`도 확인한다. 음극방식 예산은 `values.declared_budget_outcome`이 해당 필드다. 계산 완료 `computed`와 요구 충족 `satisfied`는 별도 값이다. 충족이 후속 절차의 전제라면 `SatisfactionGate`에 해당 결과 필드를 명시한다. 위 재료 확인 예제는 탄소 미측정이 미확정으로 남고 후속 단계가 실행되지 않는 경우를 함께 보여준다.

## 데이터 취득

```powershell
.\.venv\Scripts\python.exe scripts/fetch_data.py
.\.venv\Scripts\python.exe scripts/fetch_data.py --ids coqtel hannover-weld
.\.venv\Scripts\python.exe scripts/inspect_open_data.py
```

공개 카탈로그의 허용된 자산만 내려받는다. 큰 파일은 목록에 있더라도 `default=false`로 표시될 수 있다. 취득 기록에는 안정된 요청·응답 주소, 파일 크기, SHA-256과 제공자 체크섬을 남긴다. 장부 주소의 query·fragment·자격정보는 제거하며 제거 여부도 기록한다. 재취득은 검토한 카탈로그의 원 자산 주소로 수행한다. 임시 서명 URL을 공개 장부에 그대로 보존하지 않는다. 파일을 확보했다는 사실과 재배포·모델 보정에 적합하다는 판단은 별도로 기록한다.

원본은 `data/raw/`, 변환 자료는 `data/derived/`, 이용조건 확인 자료는 `data/evidence/`에 둔다. 이 폴더들은 Git과 배포물에서 제외한다. 전체 데이터가 없는 환경에서는 핵심 단위시험을 실행할 수 있으며, 데이터 조사 스크립트는 필요한 자산을 먼저 취득해야 한다.

`data/data_inventory.json`에는 실제 행 수와 관측 구조, 데이터 품질 문제, 제한된 보정 결과가 담긴다. MetroPT-3의 압력 기준은 미확정이므로 실제 절대압 이력으로 변환하기 전에 그 기준을 확인해야 한다. COQTEL의 전기화학 시간은 분 단위이며, 같은 시각·동일 값의 반복 관측이 있다. 명시적으로 선택한 정책으로만 처리한다.

부식저항 합금 지표 편집본은 `scripts/fetch_data.py --ids
corrosion-resistant-alloy-metrics`로 취득하고 `scripts/inspect_corrosion_alloy_metrics.py`로
감사한다. `read_corrosion_alloy_metrics(..., require_pinned_hash=True)`는 지표·통계량·검열
상태·SCE 기준·시험조건·원행과 참조번호를 유지한다. `Transpassive`, 상·하한, 누락을 exact
숫자로 대체하지 않는다. Workbook의 CC BY 4.0 선언은 각 원 문헌의 점별 관측 권리나 물리
시편 독립성을 자동으로 확정하지 않는다.

충격시험 편집 자료는 `scripts/fetch_data.py --ids charpy-impact`로 고정 리비전을 취득한다. 재료·시편 형상·방향·조사 조건을 분리하고 원 문헌을 보존한다. 편집 저장소의 MIT 표기만으로 수집된 모든 문헌 관측의 재배포가 허용된다고 판단하지 않는다. 원본·점별 파생 관측은 배포에서 제외하며 실제 시범 적합의 한계는 `DATA_KO.md`에 기록한다.

WILLOW는 `scripts/fetch_data.py --ids willow-synthetic willow-harshlab`로 취득한다. 전체 데이터 조사 또는 `scripts/inspect_willow_data.py`로 기하·시각 매핑과 실패·누락을 확인한다. 시뮬레이션 2,000건과 두 실제 시편의 774개 반복 기록을 별도 영역으로 유지한다. 처리 성공 표식을 결함 치수의 정확성으로 해석하지 않는다. 원 신호의 sample clock·장치 설정·미확정 시간대를 확인하기 전 재표본화나 성장 적합을 수행하지 않는다.

FABEST는 `scripts/fetch_data.py --ids fabest`로 취득하고 `scripts/inspect_fabest_data.py`로 종료 필드를 감사한다. `provider_interrupted`를 곧바로 runout으로 바꾸지 말고, `cycles_to_reported_break`, `endpoint_contract_status`, `calibration_role`을 함께 확인한다. 문자 접미사는 시편 계보가 아니며 주석 태그·온도 숫자는 검토 색인일 뿐이다. 실제 보정에는 곡선별 END 기준과 물리 시편 관계를 별도 근거로 확정한다. [피로자료 설명](FATIGUE_DATA_KO.md)에 필드와 재현 명령이 있다.

별도 FABEST LCF 벤치마크에는 `fatigue.cyclic_response_relative_error`, `fatigue.life_rmsle`,
`fatigue.dynamic_modulus_drop_endpoint`를 사용한다. 평균값/진폭 정규화, case 집합, 기준 동적탄성률,
저하율과 교차 정책을 사용자가 선언해야 한다. calibration Case 1-3과 blind Case 4-5는 합치지 않고,
검열 수명은 RMS 로그오차에 숫자로 넣지 않는다. [LCF 벤치마크 설명](FABEST_LCF_BENCHMARK_KO.md)에
예제와 재현 명령이 있다.

극값 예제는 동일 노출의 동등한 면적 블록 최대값만 대상으로 한다. 사용자가 독립성·표본 모집단·미검열·면적 상한을 확인해 입력한다. 출력의 공간 초과확률은 기간 고장확률 어댑터가 거절한다. 검토한 물리·시간 연결 모델을 추가한 뒤 위험성 모듈에 연결한다.

## 검사시점 계획

검사시점 계산에는 `inspection.threshold_inspection_schedule`을 사용한다. 먼저 열화 또는 신뢰성
모듈에서 동일 사건의 누적 최초기준도달 확률을 후보시각별로 만든 뒤, forecast ID·revision·입력
digest와 함께 전달한다. 한 시점의 두께미달 확률, 공간 pit 확률 또는 POD를 기간 최초도달확률로
바꾸지 않는다. 점추정 또는 상한 기준과 최대허용확률은 사용자가 승인해야 하며, 계산기가 규격값을
제공하지 않는다. 자세한 상태·예제·제한은 `INSPECTION_SCHEDULING_KO.md`를 따른다.

표본 기반 두께 최초도달의 `forecast_points`는 같은 asset/location/time basis에서 점추정 일정에
직접 넣을 수 있다. 신뢰상한은 별도로 산출·검토하지 않는 한 `upper_bound` 기준을 선택하지 않는다.

행동 대안을 비교하려면 `inspection.action_expected_loss`를 사용한다. baseline과 각 검사·정비 행동에
대해 동일 사건·기간·conditioning의 잔여 최초고장확률을 외부 모델로 각각 계산하고, 동일 비용
기준의 행동비용 및 고장 결과비용을 검토해 넣는다. POD를 곧바로 고장확률 감소율로 쓰거나 baseline
확률에 임의 계수를 곱하지 않는다. 비용 최소 결과는 규격 합격이나 안전 허용 판정이 아니며, 동률은
사용자가 해소해야 한다. 자세한 계약은 `ACTION_RISK_COMPARISON_KO.md`에 있다.

검사 뒤 결과별 처분을 포함하려면 `inspection.disposition_decision_tree`에 상호배타·완전분할 결과,
각 결과확률, 처분비용과 처분 뒤 조건부 잔여 최초고장확률을 넣는다. `POD=결과확률`로 두지 말고
true state·coverage·관측·처분을 연결한 검토 모델의 결과를 사용한다. 계산된 tree는 전용 adapter로
estimate-basis 행동 후보가 되지만 확률상한이나 다기간 최적정책을 제공하지 않는다.

외부 시뮬레이터가 여러 시점의 검사·모니터링·수리 경로를 이미 생성했다면
`inspection.multi_period_policy_evaluation`에 누락 없는 경로 manifest를 넣는다. 경로확률은 합이
1이어야 하고, 각 행동의 시각·정의·모델 digest와 비용·현재가치계수를 그대로 보존한다. 고장 경로는
최초고장 시각까지만 행동을 가질 수 있다. 결과는 한 고정 정책의 기대값이며 다른 정책보다 최적이라는
뜻이 아니다.

경로 대신 유한 상태·관측·전이표가 있다면 `inspection.finite_policy_path_generation`에 시작분포,
각 시점의 상태조건부 관측확률, 관측별 행동, 상태-행동 전이를 넣는다. 모든 분포의 합을 1로 맞추고
failure 전이에만 결과비용 할인계수를 둔다. `maximum_generated_paths`는 근사 절단값이 아니라 안전한
실행 한도이며 초과 시 한도를 늘리거나 모델을 재구성해야 한다.

확률표를 자료에서 만들려면 먼저 상태 truth, 관측 라벨, 수행 행동과 시편/feature의 종단 identity를
검토한다. `inspection.finite_policy_probability_calibration`에는 동일 sequence와 source group이
calibration/holdout에 동시에 나타나지 않게 넣는다. smoothing은 승인한 대칭 pseudocount만 허용하며
기본값 0은 관측되지 않은 사건에 0을 유지한다. holdout에서 0확률 사건이 나오면 log loss가 `null`이고
해당 record ID가 보고되므로 임의 epsilon으로 숨기지 않는다. 현재 공개 ILI 이력은 회차간 feature
identity와 굴착 truth가 없어 이 입력으로 사용하지 않는다.

복수의 고정 정책을 비교하려면 각 평가 결과를
`inspection_policy_candidate_from_evaluation_result`로 후보화하고
`inspection.multi_period_policy_comparison`에 넣는다. 동일 사건·기간·비용·할인 기준을 유지하며,
최초고장확률과 outage 등 자원 한도를 사용자 승인 hard constraint로 선언한다. 상한 기준을 쓰려면
모든 후보에 자격 있는 상한이 있어야 한다. 제약 위반 후보를 비용이 낮다는 이유로 선택하지 않는다.

## 새 분야 추가

수소의 첫 국소 평형 예제는 `python examples/hydrogen_partition.py`로 실행한다. 원자 수소 농도와 site density를 mol/m³로 맞추고 결합에너지의 기준·부호를 확인한다. 원자 계산의 이동 장벽을 트랩 결합에너지로 넣지 않는다. 기체 압력만으로 농도를 임의 결정하지 않으며 국소 평형 선언을 충족하지 못하면 동역학 모델을 기다리거나 검토된 사용자 모델을 등록한다.

`scripts/fetch_data.py --ids he-austenite`는 편집 자료의 기본 파일을 취득한다. 선택 자산은 `--ids`와 `--include-optional`을 함께 지정해야 취득하며, 각 파일의 명시적 용량 한도를 유지한다. `carbide-traps`의 전체 압축파일은 약 2.64 GB이므로 `scripts/fetch_data.py --ids carbide-traps --include-optional`로 명시적으로 취득한다. 자료의 코드·매크로는 자동 실행하지 않는다. 가스 수소 시험과 전기화학 충전 실험, 인장 보존비와 균열 성장률을 구분한다.

HyMatBase 4130X 피로 workbook은
`scripts/fetch_data.py --ids hymatbase-4130x-hydrogen-fracture-fatigue --include-optional`로만
명시적으로 취득한다. `read_hymatbase_hydrogen_fatigue`에는 고정 SHA-256, source group,
material-condition ID, 별도로 검토한 record 압력·온도를 넣는다. record 4.5 MPa와 workbook 45 MPa의
충돌은 `acknowledge_pressure_conflict=True` 없이는 통과하지 않는다. Rights가 기재되지 않았으므로
원파일·점별 표를 공개 배포하거나 271점을 독립 시편·서비스 성장곡선으로 취급하지 않는다.
[4130X 수소 피로 자료 설명](HYDROGEN_FATIGUE_DATA_KO.md)을 먼저 따른다.

배관 편집 자료는 `scripts/fetch_data.py --ids compiled-pipe-burst`로 취득하고 `scripts/inspect_burst_data.py`로 주 표·셀 기원·문헌 연결을 확인한다. 보조 시트를 추가 독립 시편으로 합치지 않는다. 범용 프로파일 계산은 별도의 검토된 기준 압력·형상 보정표를 공급해 사용한다. 사용자 예측과 실제 시험을 비교할 때는 `structural.burst_pressure_comparison`과 `BURST_VALIDATION_KO.md`를 사용한다. 편집본의 지름·압력 기준·프로토콜·물리 시편·원 관측 권리·보완 물성에 대한 검토 없이 파열압 검증 자료로 연결하지 않는다.

극값 예제의 작은 재표집 수는 API 실행 확인용이다. 적합도 p값의 해상도 1/(모의 수+1)가 선택한 최소 기준과 같거나 크면 기준 미달을 구분할 수 없다. 실제 통계 해석에는 필요한 Monte Carlo 정밀도와 재표집 수를 검토하고 `VALIDATION_KO.md`의 진단 범위를 확인한다.

`docs/API_KO.md`의 사용자 모델과 파라미터 표를 사용한다. 필요한 데이터·규칙을 공급한 뒤 적용 조건과 검증 예제를 함께 등록한다. `data/catalogs/capabilities.json`의 `planned` 항목은 아직 계산 기능이 아니다. 기능을 추가할 때 모델·검증·문서·카탈로그를 함께 갱신한다.

## 검증과 재현

FAD를 사용할 때는 먼저 정당하게 사용할 수 있는 경계 곡선과 판본, K/reference-stress 해, 재료 상태에 맞는 파괴저항·정규화 강도를 준비한다. `structural.failure_assessment_points`의 다섯 적용성 검토를 실제 근거에 따라 선언하고 material condition과 point/load/location ID를 일치시킨다. `unknown`이나 `out_of_scope`를 안쪽 점으로 채우지 않는다. 시간 이력은 [FAD history guide](models/FAD_ASSESSMENT_HISTORY_KO.md)를, 별도 caller 확률을 기존 FTA event로 넘기는 경로는 [FAD→FTA guide](models/FAD_FTA_BINDING_KO.md)를 따른다. 원자료 확인은 `scripts/inspect_fracture_data.py`, 수학 검사는 `scripts/validate_fad.py`로 수행한다. [파괴평가 설명](FRACTURE_ASSESSMENT_KO.md)의 crack-arrest와 initiation toughness 구분을 유지한다.

편집 파괴인성 workbook은 `read_fracture_toughness_temperature`로 읽는다. 기본값은 workbook의 충돌하는 `K` 표기를 보존하면서 연계 논문에서 확인한 °C를 사용해 온도를 K로 변환한다. W/B/a의 원 단위 표기는 비어 있지만 논문의 T 크기 mm 정의와 workbook 전 행의 두께 척도를 대조한 `article_mm` 근거로 m 치수를 만든다. 파생 workbook에 이 검토가 적용되지 않으면 `apply_article_dimension_review=False`를 사용하고, 별도 근거가 있으면 `temperature_unit_override="degC"`, `dimension_unit_override="mm"`처럼 override를 기록한다. 예제 CLI의 `--no-article-dimension-review`도 같은 중지 경로다. 기본 형상 조건 그룹은 재료·시편형식·W/B를 상대 3%·절대 0.1 mm 허용오차로 묶으며 CLI의 `--condition-group-relative-tolerance`와 `--condition-group-absolute-tolerance-m`로 바꿀 수 있다. 이는 train/test 누설 확인용이지 물리 시편 ID가 아니다. `article_source_group_status`는 논문 표와의 정확 일치·유력 이름 변형·재료조건 불일치·미해결을 구분하는 선별 정보이며 원 문헌 ID나 시편 ID가 아니다. `article_reference_bibliographic_id`가 있어도 관측 재배포 허가를 뜻하지 않으므로 `article_reference_observation_rights_status`를 별도로 확인한다. Provider의 `test` 표식은 같은 편집 자료의 무작위 분할명이며 독립 기관 검증이나 시험 유효성 표식으로 사용하지 않는다.

```powershell
.\.venv\Scripts\python.exe examples\fracture_toughness_data.py data\raw\fracture-toughness-temperature\2vkgrbsy8j-1.zip
```

이 예제는 점별 관측을 출력하지 않고 분할 행 수와 SI 변환 상태만 요약한다. 온도는 연계 논문 근거로 기본 변환된다. 치수 근거를 확인한 뒤에만 `--dimension-unit mm`를 추가하며, 파생 workbook의 온도 선언이 다른 경우에만 `--temperature-unit`를 사용한다.

과도 열전도→탄성 열응력 예제는 `python examples/thermal_gradient.py`로 실행한다. 재료별 온도 물성 표가 모든 계산 온도를 덮는지, 실제 평판 면적 또는 원통 길이, 경계 열유속 부호, 셀/출력 시각과 평면 조건을 먼저 확인한다. 결과의 이산 에너지 잔차와 탄성 한계 사용률을 확인하되 작은 잔차를 실험 검증으로, 탄성 범위 결과를 규격 합격으로 해석하지 않는다. 실제 rod 자료 조사는 `scripts/inspect_thermal_data.py`, 수학·수렴 검사는 `scripts/validate_thermal_gradient.py`로 재현한다. 자세한 제한은 [열구배 설명](THERMAL_GRADIENT_KO.md)에 있다.

분극 곡선과 면적에 따른 갈바닉 전위/순전류 예제는 `python examples/galvanic_coupling.py`로 실행한다. 원자료는 `scripts/inspect_polarization_data.py`로 부호·행·전위 구간과 시험 방법의 미확정 조건을 대조한다. [분극 계산 설명](ELECTROCHEMISTRY_KO.md)에 따라 전위 기준·실제 면적·준정상/저항 조건을 준비한다. 대표 전위가 비어 있으면 다중 평형점·누락 조건·범위/수치 상태를 먼저 확인한다.

전역 민감도 예제는 `examples/sensitivity.py`로 실행한다. 기존 계산기에 단위가 있는 합성 입력 범위를 연결하는 예제이며 실제 재료의 분포 추정이 아니다. 독립성·재현성, 실패 표본, 설계/평가 JSON 보존과 수치 기준을 [민감도 설명](SENSITIVITY_KO.md)에 따라 확인한다. 상관 물성이나 noisy simulator에는 별도 방법이 필요하다.

유한 평판 수소 수송은 `examples/hydrogen_slab.py`, 직접 입력한 독립 속도는 `examples/hydrogen_independent_trap_rates.py`, Arrhenius/전이상태 속도 생성은 `examples/hydrogen_thermal_rates.py`, 검토된 속도 관측 적합은 `examples/hydrogen_thermal_rate_fit.py`, fugacity 기반 축약 표면반응 조합은 `examples/hydrogen_surface_reaction.py`, 반경–축 유한 원통은 `examples/hydrogen_cylinder.py`, 이상적 검출 신호 투영은 `examples/hydrogen_detector_observation.py`, 한 개 평판 수송 이력 배수의 제한적 역추정은 `examples/hydrogen_slab_flow_fit.py`로 합성 실행하고 [입력·수치 제어·검증 설명](HYDROGEN_TRANSPORT_KO.md)을 따른다. 역추정 전에는 관측을 signed outward atom mol/s로 독립 보정하고 실제 면적·정확한 시계·calibration/holdout을 미리 고정한다. 한 번에 한 이력만 선택하고 holdout을 고정 입력 선정이나 목적함수에 사용하지 않는다. 열활성화 공급자의 출력 조각에는 matching population과 초기 점유율을 추가하고, 표면반응 조각에는 surface ID를 붙인다. 비선형 온도·fugacity 변화에서는 시간 knot 세분화 민감도를 확인한다. 실제 TDS에는 공개된 원통 치수만 자동 적용하지 말고 곡선별 시편 대응, 초기 분포, 곡면·양 끝단 방출 조건, 측정 시계·검출기 응답과 반경/축 격자 수렴을 먼저 검토한다.

탄화물 트랩 자료의 수치 CSV를 읽는 절차는 [수소 수치 내보내기](HYDROGEN_EXPORTS_KO.md)에 있다. 기존 내보내기와 장부를 먼저 확인하고 원 시계·단위·처리 열·시편 대응을 보존한다. 단위 미확정 상태나 요약 계수를 검토 없이 수송·열역학·위험성 모델 입력으로 바꾸지 않는다.

외부 수소 수송 solver의 농도·재고 이력을 교환할 때는 [수소 수송 교환계약](HYDROGEN_TRANSPORT_EXCHANGE_KO.md)을 사용한다. 먼저 공급자 revision과 native 결과 bytes를 고정하고 material-condition, lattice, carrier, geometry, trap, clock ID를 채운다. 계약 통과는 데이터 배선 확인일 뿐이므로 외부 결과를 취성화, 균열성장, 수명 또는 FTA 기초사건 확률로 자동 변환하지 않는다.

외부 인적신뢰도 결과는 [인적신뢰도 교환계약](HUMAN_RELIABILITY_EXCHANGE_KO.md)으로 수신한다. task/procedure/context, 실패·기회 정의, conditioning, method/evidence/trace와 recovery·timing 포함범위를 함께 검토한다. 작업 기회당 실패확률을 기간 최초고장확률이나 연간빈도로 사용하려면 별도의 요구 노출, 반복·회복·공통원인·의존모형이 필요하다.

외부 배관 계산 결과는 [배관 평가 결과 교환계약](PIPELINE_EXCHANGE_KO.md)으로 수신한다. 원 공통 결과를 JSON으로 내보내고 provider package version과 source-tree SHA-256을 함께 고정한다. 모델·단위·clock·evidence·qualification을 변경하지 말고 `computed`를 정상·합격·설계승인으로 해석하지 않는다. 압력·온도 이력과 국부 tensor가 필요한 경우에는 각각 기존 `OperatingHistory`와 `LocalTensorHistory`를 사용한다.

용접 후 수소 방출의 빠른 screening에는 [유한 평판 bakeout 모델](HYDROGEN_BAKEOUT_KO.md)을 사용한다. 실제 용접부에서 수소가 빠져나가는 대표 두께, material condition에 맞는 유효 확산계수 이력, 초기 확산성 수소 농도와 온도 이력을 공급한다. 두 표면이 방출 경계인지, 초기 농도가 균일한지, 표면 반응보다 bulk diffusion이 지배하는지 각각 검토한다. 하나라도 확인하지 못하면 결과를 절차 합격에 사용하지 말고 상세 trap/수송 모델 또는 실험을 사용한다.

겨울철 정지 유체 재고는 [겨울철 열수지](WINTERIZATION_KO.md)를 따른다. 먼저 질량, 절대압, 외기·UA·tracing 이력과 사용자 검토 최소온도를 준비한다. 구간별 대표 유체 비열은 직접 공급하거나 CoolProp 조합기로 생성한다. 계산 경로가 최소온도 아래로 내려가면 이를 실제 동결량이나 파손으로 바꾸지 말고, 혼합물 phase data·잠열·국부 열전달을 포함한 상세 평가로 전환한다.

표면 준비, 화학 세정, 저장 보존, coating/thermal-spray qualification, 시험수 수질, 운송·설치, 용접 소모재·phase balance·production test·repair history는 [제작·보존 증거 워크플로](FABRICATION_EVIDENCE_WORKFLOWS_KO.md)를 사용한다. 관측값·불확실성·기록 공백과 사용자 소유 한계를 별도로 유지하고, `needs_data`를 정상으로 바꾸지 않는다. 결과를 위험성 평가에 연결할 때는 위반 또는 누락의 사건 정의·기간·조건부 기준을 별도 adapter에서 명시한다.

Polymer, composite, casting/forging과 under-insulation 기록은 [재료 compatibility 워크플로](MATERIAL_COMPATIBILITY_WORKFLOWS_KO.md)를 따른다. 재료·lot·layup·heat·제조상태와 service environment를 exact identity로 연결하고 사용자 qualification envelope 밖을 자동 보정하지 않는다. Envelope match를 손상률·수명·고장확률 또는 규격 합격으로 바꾸지 않는다.

Phase fraction, sour service, chloride SCC와 microbial campaign은 [환경 열화 증거 워크플로](ENVIRONMENTAL_DEGRADATION_EVIDENCE_KO.md)를 따른다. Pressure basis, exact concentration unit, stress descriptor, assay detection limit와 calibration/holdout source group을 유지한다. Applicability나 indicator 초과를 실제 균열·부식률·기간 고장확률로 변환하려면 별도 보정 모델이 필요하다.

Brittle test, 고온 수소, 액체금속 접촉과 crevice species inventory도 같은 [환경 열화 증거 워크플로](ENVIRONMENTAL_DEGRADATION_EVIDENCE_KO.md)를 따른다. 시험 specimen/source group, absolute partial-pressure basis, liquid composition·wetting, species·volume·rate-provider support를 입력에서 고정한다. Crevice 결과는 supplied net rate의 물질수지이며 pH나 부식률이 아니고, applicability 결과는 손상 발생이나 합격 판정이 아니다.

음향방출, 복제 금속조직, 파괴인성 시험과 극저온 누설시험 자료는 [검사 증거 워크플로](INSPECTION_EVIDENCE_WORKFLOWS_KO.md)를 따른다. `computed`를 정상·무결함·합격으로 해석하지 말고, 원 검사의 물리 범위·source group·시계·검출한계·불확도를 먼저 확인한다. FTA나 기간 고장확률과의 연동은 사건정의·기간·conditioning·검사효과를 별도 adapter에 명시한다.

압력시험 계획에는 `inspection.pressure_test_eligibility`를 사용해 test method·medium·pressure basis, 계획 범위, stored-energy 정의와 prerequisite evidence를 caller envelope에 대조한다. 용접 solidification/reheat cracking과 lamellar tearing 검토는 [용접 균열 applicability](WELDING_CRACKING_APPLICABILITY_KO.md)를 따른다. `computed`와 `requirements_satisfied`도 규격 승인이나 무균열 보증이 아니다.

Joint efficiency는 공개 코드에 규격표를 옮기지 말고 정당한 이용권한이 있는 사용자 rule payload로 `fabrication.joint_efficiency_declaration`을 실행한다. Temper-bead, hot-tap과 brazing/bonding도 [용접 균열 applicability](WELDING_CRACKING_APPLICABILITY_KO.md)의 identity·provider·qualification 요구사항을 따른다. 반환된 factor나 applicability를 구조용량 또는 합격으로 자동 변환하지 않는다.

성형, tube-bundle, 극저온 밸브는 [제작 증거 워크플로](FABRICATION_EVIDENCE_WORKFLOWS_KO.md), peening은 [용접 applicability 문서](WELDING_CRACKING_APPLICABILITY_KO.md)를 따른다. Tube disposition은 caller decision이며 모델 추천이 아니다. Below-detection 누설을 0으로 바꾸거나 peening 잔류응력을 피로수명 증가량으로 변환하지 않는다.

외부 FE, external-pressure, nozzle-stress와 heat-exchanger geometry 결과는 [구조 provider 교환](STRUCTURAL_PROVIDER_EXCHANGE_KO.md)을 따른다. 원 배열을 JSON에 복사하지 말고 불변 저장소에 두며 coordinate/component order, shape와 content digest를 입력한다. `computed`는 provider payload가 caller support 안이라는 뜻이며 mesh convergence, 규격합격 또는 현장검증이 아니다.

크리프를 시작하려면 `scripts/fetch_data.py --ids cmsx6-creep` 후 `scripts/inspect_open_data.py`를 실행한다. 실제 자료와 별개로 `python examples/creep_life.py`는 합성 시편 적합→독립 모델 계약→조건부 기간 사건을 실행한다. JSON 배열을 Python의 엄격한 tuple 계약으로 읽을 때는 `CreepLifeModel.model_validate_json`을 사용한다. 재료 상태·하중 관례·현재 나이의 원점을 정확히 연결하고 적용 검토를 기록한다. 온도가 한 수준이면 `stress_only`를 선택한다. 변동 이력은 이 모델의 조건을 충족하지 않으므로 별도의 누적 열화 경로가 필요하다.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check src tests scripts
.\.venv\Scripts\python.exe -m ruff format --check src tests scripts
.\.venv\Scripts\python.exe scripts/build_capability_catalog.py
```

입력 해시와 데이터 해시가 같아도 의존성 버전에 따라 수치가 조금 달라질 수 있다. 배포 기록의 실행 환경과 함께 비교한다. 검증 수준의 의미는 `docs/VALIDATION_KO.md`에 설명한다.
## 희귀한 기간 사건을 외부 한계상태와 연결하기

먼저 같은 자산·부위·기간·생존조건에서 무엇을 `True`로 볼지 고정한다. 입력 불확실성을 검토된
매핑으로 표준정규 잠재변수에 연결하고, 평균이동 제안분포에서 생성한 각 표본에 고유 ID를 붙인다.
동일한 순서로 외부 부식·파괴·FTA 평가자를 실행해 Boolean 사건 지시값을 만든 뒤
`reliability.gaussian_mean_shift_importance_sampling`에 전달한다. 평가 실패나 누락은 `False`가
아니므로 표본을 분석에서 빼거나 정상으로 바꾸지 말고 설계/평가 batch를 수정해야 한다.

결과에서는 확률 추정값만 보지 말고 가중치 평균, 전체 ESS, 사건 ESS, 최대 정규화 가중치와
제안분포 사건 비율을 함께 확인한다. 제안 사건이 0건이면 0이라는 점추정을 서비스 판정에 쓰지
않는다. ESS가 낮거나 소수 가중치가 지배하면 평균이동과 표본 수를 재검토한다. 정규근사 구간은
Monte Carlo 수치오차일 뿐 물성·부식률·상관구조·모델형식·결과 불확실성을 포함하지 않는다.
입력 필드와 검증 절차는 `RARE_EVENT_SAMPLING_KO.md`를 따른다.
## 외부 provider 증거 모델 사용

가스켓 체결, 수소 피로·균열, 공식 FFS, 크리프-피로 상호작용은 `examples/model_inputs.json`의 대응 model ID를 복사해 시작한다. Asset/location, material condition, 환경·하중 basis, provider revision과 입력·결과 digest를 실제 자료로 바꾸고 calibration/holdout의 물리 시편 및 source-group 독립성을 검토한다.

가스켓 preload는 직접 측정값만 사용하고 torque에서 환산하지 않는다. 수소 압력은 absolute partial pressure와 fugacity를 혼용하지 않으며 K/J/CTOD endpoint를 바꾸지 않는다. 공식 FFS와 크리프-피로는 외부 공급자의 결과 및 exact basis를 전달할 뿐 내부에서 규격 용량이나 선형 손상합을 새로 만들지 않는다. 계약의 `computed` 상태는 배선·범위 검사가 완료됐다는 뜻이지 설계 합격이나 현장 검증이 아니다. 자세한 경계는 [수소 파괴 provider](HYDROGEN_FRACTURE_PROVIDER_KO.md), [구조 provider 교환](STRUCTURAL_PROVIDER_EXCHANGE_KO.md), [제작 증거 워크플로](FABRICATION_EVIDENCE_WORKFLOWS_KO.md)를 따른다.

## 다년 대기부식·비등온 산화·결로·상관사건

대기부식 다년 전이는 현장에 자격화된 1년 손실과 시간지수, 독립 calibration/holdout 근거가 있을 때만 사용한다. 공개 1년 회귀 결과를 자동 연결하지 않는다. 비등온 산화는 재료·표면·환경에 맞는 사용자 `k(T)` 표를 제공하고 표 밖 이력을 외삽하지 않는다.

단열 결로노출은 측정·열해석 외표면 온도와 독립 이슬점 이력을 같은 clock으로 맞춘다. 습공기 상태가 검토됐다면 CoolProp adapter를 사용할 수 있지만, 결로 가능시간을 CUI 부식량으로 바꾸지 않는다. 이진 사건쌍 calibration 결과도 관측 구간의 경험빈도이므로 별도 기간·사건·불확실성 자격화 없이 FTA 기초사건 확률로 넣지 않는다. 자세한 한계는 [대기부식](ATMOSPHERIC_CORROSION_KO.md), [상관 사건](CORRELATED_EVENTS_KO.md), [비등온 산화와 단열 결로](OXIDATION_INSULATION_KO.md)를 따른다.

순환 소성, signal-response POD와 CTMC rate를 적합할 때는 calibration/holdout 시편·source group을 먼저 고정한다. Holdout은 계수 선정이나 threshold 조정에 재사용하지 않는다. 소성 fit의 단위와 지원범위, censored POD 신호, CTMC exposure unit 및 0-rate holdout 모순을 그대로 보존한다. 실행 경계는 [보정 심화 문서](CALIBRATION_DEEPENING_KO.md)를 따른다.


데이터 취득 명세를 빠르게 점검하려면 `.\.venv\Scripts\python.exe scripts/audit_dataset_catalog.py`를 실행한다. 이 명령은 출처별 권리상태와 취득정책을 요약하고, 이미 내려받은 파일의 선언 checksum/크기를 대조한다. 제공자 checksum이 없는 자료는 별도 finding으로 남으며, 로컬 SHA-256만 계산됐다고 제공자 원본과 일치하거나 재배포 권리가 확인된 것으로 해석하지 않는다.


허용된 선택 자산 데이터셋은 `--ids <dataset-id> --include-optional`을 함께 지정해야 취득한다. 기본 전체 카탈로그 조회나 ID만 지정한 요청으로는 선택 자산을 내려받지 않으며 `metadata_only` 및 `do_not_download` 자료는 이 옵션으로도 취득할 수 없다.

## 튜브 압력응력·용접 파형 불확도

튜브 bundle 계산은 식별된 튜브마다 현재 bore/최소 벽두께, 공통 시계와 절대압 기준, digest가 고정된 압력 knots를 준비한다. 균일 축대칭 등방성 선형탄성과 축방향 단부 조건의 적용성을 검토해야 한다. [튜브별 Lamé 응력 이력](models/TUBE_BUNDLE_LAME_STRESS_HISTORY_KO.md)과 [합성 예제](../examples/tube_bundle_lame_stress_history.py)는 inner/outer wall 결과만 계산하며 코드 acceptance·용량·수명을 판정하지 않는다.

용접 파형 불확도 API에는 `WaveformEnergy`의 전압/전류 samples와 효율·이동거리 전체 covariance를 고정 좌표 순서/단위, Evidence, 이용권한, 공급자 revision 및 digest와 함께 제공한다. 시계는 정확값으로 취급한다. [계약 설명](models/WAVEFORM_ENERGY_UNCERTAINTY_KO.md) 및 [합성 예제](../examples/waveform_energy_uncertainty.py)를 참고한다. 결과는 국소 1차 표준불확도이며 확률·신뢰수준·WPS 합격을 뜻하지 않는다.

## Crevice 고정 형상 구간 간 재고 인계

component-state BDF 구간을 확정한 뒤 새 형상 구간을 시작할 때 `integration.crevice_component_state_segment_handoff`를 사용한다. 이전 계산 결과의 digest와 닫힌 성분 수지를 확인하고, 셀별 총 성분 몰수와 고체상 몰수를 다음 구간 후보 초기값으로 넘긴다. 새 구간의 셀 형상, 상 몰부피, 간극 점유율은 사용자가 제공하고 검토해야 한다. 이 API는 구간 사이 초기화만 구성하며 BDF 내부의 이동 경계나 반응을 계산하지 않는다. 상세 입력·제한은 [API 계약](models/CREVICE_COMPONENT_STATE_SEGMENT_HANDOFF_KO.md)을 참조한다.

## Crevice BDF에 caller capacitive-current 이력 연결

`integration.crevice_component_state_bdf`의 선택형 `capacitive_current_schedule`은 사용자가 검토한 cell별 exact-knot capacitive current를 digest와 Evidence에 고정해 charge-continuity 검사와 누적 전하 장부에 반영한다. 전위 state를 풀거나 Butler–Volmer 전류를 이 신호에서 유도하지 않으며, stage mixed-potential 경로와 함께 사용할 수 없다. 입력 부호·면적 기준·전류 출처를 확인하고 [계약과 한계](models/CREVICE_COMPONENT_STATE_BDF_CAPACITIVE_CURRENT_KO.md)를 따른다.

## Crevice segment 경계에서 caller geometry 갱신

고정 geometry component-state BDF 구간을 마친 뒤 다음 geometry에서 이어 계산하려면 `integration.crevice_component_state_segment_transition`을 사용한다. 이전 committed 결과의 최종 성분 몰수를 새 요청의 셀별 초기 inventory로 옮기며, caller가 제공한 새 셀 체적·aperture·면적·spacing을 digest/Evidence와 대조한다. 이 경로는 segment 사이 전환이므로 interval 내부 moving-boundary 연성이나 geometry 예측을 수행하지 않는다. [계약과 단계](models/CREVICE_COMPONENT_STATE_SEGMENT_TRANSITION_KO.md).

## Crevice caller nucleation kinetics 준비

`chemistry.crevice_nucleation_kinetic_history`는 saturation ratio와 thresholded molar nucleation source, seeded growth/dissolution law를 caller로부터 받는다. 시간축을 contiguous exact intervals로 제공하고 interval마다 모든 phase ratio를 Evidence/digest로 고정한다. 결과는 각 interval의 aqueous/solid inventory 및 원소·전하 ledger로 확인한다. **핵생성 source 단위는 mol/m³/s**이며, 핵 개수나 입자 population을 뜻하지 않는다. [상세 적용경계](models/CREVICE_NUCLEATION_KINETIC_HISTORY_KO.md).
