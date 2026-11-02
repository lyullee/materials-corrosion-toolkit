# 내압 중공 시편의 다축 피로 하중상태와 종료 사건

## 목적과 경계

`fatigue.pressurized_annulus_load_state`는 중공 원형 기준단면에 작용하는 축력, 토크,
내·외압을 서로 구분한 뒤 명목 응력 성분으로 변환한다. 출력은 다축 피로모델의 입력을
준비하기 위한 값이다. 피로강도, 피로수명, 임계면, 노치 집중, 비비례 추가경화 또는 합격
여부를 계산하지 않는다.

구현 근거는 공개된 FABEST HCF Competition package version 2.1.2와 독립적으로 작성한
환형 단면 평형식이다. 자료의 공개 위치는 <https://doi.org/10.5281/zenodo.23532147>이다.
원 자료의 문장·표·그림은 소스나 배포 문서에 복제하지 않는다.

## 입력 계약

- `reference_section_id`, `load_case_id`: 기하와 하중 조건을 재현하는 식별자다.
- `inner_radius_m`, `outer_radius_m`: 환형 기준단면의 내·외반경이다.
- `pressure_evaluation_radius_m`: Lamé 압력응력을 평가하는 벽 내부 반경이다.
- `external_axial_force_mean_N`, `external_axial_force_amplitude_N`: 외부 축력의 평균과
  음이 아닌 진폭이다.
- `torque_mean_N_m`, `torque_amplitude_N_m`: 토크의 평균과 음이 아닌 진폭이다.
- `axial_torsion_phase_rad`: 축력과 비틀림 채널의 위상차이며 0부터 2π까지 허용한다.
- `internal_pressure_Pa`, `external_pressure_Pa`: 절대압 자체가 아니라 벽 응력 계산에
  사용되는 내·외측 경계압이다. 두 값을 별도로 보존한다.
- `closed_ends`: 압력이 유효 폐쇄면에 작용해 축방향 평균응력을 만드는지 선언한다.

기하가 역전되거나 압력 평가점이 벽 밖이면 입력 검증에서 거절한다. 축력과 토크의 평균은
부호를 허용하지만 진폭은 음수가 될 수 없다.

## 계산

내반경을 `a`, 외반경을 `b`라 하면 기준면적과 극2차모멘트는 다음과 같다.

```text
A = π (b² - a²)
J = π (b⁴ - a⁴) / 2
```

축력은 `F/A`, 외표면의 명목 비틀림 전단응력은 `T b/J`로 변환한다. 평균과 진폭을
각각 계산하고 최솟값과 최댓값도 반환한다. 압력 성분은 장축 방향으로 충분히 긴 균질
등방 선형탄성 원통의 Lamé 해를 사용한다. 폐쇄단이면 압력에 의한 축응력을 포함하고,
개방단이면 그 성분을 0으로 둔다.

외부 축력에서 계산한 축응력 진폭에는 압력 축응력을 더하지 않는다. 압력은 정적 평균
성분으로 별도 반환한다. 따라서 경쟁·시험 프로토콜처럼 보고 대상이 외부 축력 기준 명목
진폭인 경우에도 정의가 섞이지 않는다.

## Python API 예

```python
from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

context = RunContext(
    asset_id="specimen-or-component",
    location_id="net-annular-section",
    time_basis="declared cyclic load case",
)
result = default_registry().run(
    "fatigue.pressurized_annulus_load_state",
    {
        "reference_section_id": "net-annulus",
        "load_case_id": "axial-torsion-pressure-01",
        "inner_radius_m": 0.006,
        "outer_radius_m": 0.008,
        "pressure_evaluation_radius_m": 0.006,
        "external_axial_force_mean_N": 0.0,
        "external_axial_force_amplitude_N": 10000.0,
        "torque_mean_N_m": 0.0,
        "torque_amplitude_N_m": 100.0,
        "axial_torsion_phase_rad": 1.5707963267948966,
        "internal_pressure_Pa": 60000000.0,
        "external_pressure_Pa": 0.0,
        "closed_ends": True,
    },
    context,
)
```

실제 부품에서는 기준단면과 내압 경계가 적합한지 먼저 검토한다. 노치 시편의 명목
단면값은 국부 노치근 응력이 아니다. 국부 응력장, 응력집중, 잔류응력, 소성, 끝단과
치구 영향은 자격 있는 해석 공급자가 추가해야 한다.

## 압력 저하 종료 사건 계약

`fatigue.pressure_loss_endpoint`는 한 물리 시편의 검토된 유효 하중 구간을 합산하고 시험
관측을 다음과 같이 구분한다.

- 시편의 관통균열 또는 파열이 확인되고 선언 임계 압력 저하를 충족한 실패 끝점
- 압력계통 또는 계측계통의 중단으로서 동일 시편 재개가 가능한 사건
- 종료된 관측창에서 선언 cycle 한도에 도달하고 시편 끝점이 없는 우측 검열 runout
- 사건 출처, 시편 연속성 또는 하중 이력을 확인할 수 없는 불명확 관측
- 아직 cycle 한도나 관측 종료에 도달하지 않은 진행 중 관측

각 구간은 `segment_id`, `physical_specimen_id`, `load_case_id`, `valid_loading_cycles`와
cycle 계수 근거를 갖는다. 모든 구간은 같은 하중 case여야 하며, 동일 시편으로 선언한
구간의 물리 시편 ID가 다르면 입력을 거절한다. 압력 저하율은 관측값일 뿐이다. 임계값을
넘었다는 사실만으로 시편 파손을 만들지 않으며, 설비·계측 중단을 runout으로 바꾸지 않는다.

```python
endpoint = default_registry().run(
    "fatigue.pressure_loss_endpoint",
    {
        "segments": [{
            "segment_id": "segment-01",
            "physical_specimen_id": "specimen-01",
            "load_case_id": "load-case-01",
            "valid_loading_cycles": 2000000.0,
            "cycle_count_basis": "reviewed_manual",
        }],
        "initial_pressure_Pa": 60000000.0,
        "observed_pressure_drop_Pa": 0.0,
        "declared_drop_fraction_threshold": 0.1,
        "event_origin": "none",
        "specimen_event_kind": "none",
        "specimen_pressure_loss_confirmed": False,
        "same_physical_specimen_across_segments_declared": True,
        "loading_history_reconstructable": True,
        "runout_limit_cycles": 2000000.0,
        "observation_window_closed": True,
    },
    context,
)
```

`usable_as_fatigue_observation`은 끝점 분류가 보정 자료로 사용할 수 있는 형태인지 나타내는
계약 표식이다. 재료 독립성, 시험 유효성 또는 특정 피로모델의 적합성을 보증하지 않는다.
`right_censored_runout`도 피로강도, 예상수명 또는 기간 고장확률이 아니다.

고정된 경쟁 패키지 v2.1.2의 규칙·시험순서·설비 문서를 대조한 결과, 해당 시험에서 선언한
시편 끝점은 초기 압력의 10% 이상인 급격한 저하와 시편 압력건전성 상실의 확인을 함께
요구한다. 확인 가능한 물리 사건은 완전 파열 또는 내면과 외면을 잇는 관통균열이며, 완전
분리가 반드시 필요한 것은 아니다. 확인된 시편 사건 없이 2,000,000 cycle에 도달하면
runout이다. 압력계통 문제로 중단됐지만 시편이 온전하고 하중 이력을 재구성할 수 있으면
계통 복구·재확인 뒤 같은 시편을 재개하고 유효 구간 cycle을 누적한다. 시편 건전성이나
하중 이력이 확인되지 않으면 실패나 runout으로 강제하지 않고 무효·불명확으로 남긴다.

이 정량 기준은 별도의 HCF 경쟁 패키지에만 적용한다. 기존 FABEST 데이터베이스 workbook의
60개 곡선에 누락된 END 기준, 문자 접미사, interruption 의미를 소급해 채우지 않는다.

## 공개 자료 감사 결과

고정 ZIP의 SHA-256은
`bed23c7253197a226c5394a0eb6267193a2f7946e98478fc85effcb575666f7b`이고 크기는
46,329,584바이트다. 36개 archive member 중 실제 파일은 15개이며 암호화 또는 상위경로
이탈 항목은 없다. 두 workbook에는 수식 셀이 없었다.

blind matrix는 20개 조건으로 구성된다. Plain과 Notched가 각각 10개이고 위상 0°와
90°가 각각 10개다. 목표 반복수는 20,000, 50,000, 100,000, 200,000, 500,000이며 각
수준에 4개 조건이 있다. 제출 템플릿의 20개 case ID는 matrix와 같은 순서이고 결과 칸은
모두 비어 있다. 따라서 이 패키지는 입력 계약과 시험 절차를 검토하는 자료이지 독립적인
피로강도·수명 검증 자료가 아니다.

`validation/fabest_hcf_package.json`은 위 네 프로토콜 문서의 ZIP 내부 경로·바이트·SHA-256과
종료 기준 검토 결과를 함께 보존한다. 문서 해시가 바뀌면 감사 스크립트가 중지한다.

감사는 다음 명령으로 재현한다.

```powershell
.venv\Scripts\python.exe scripts\inspect_fabest_hcf_data.py `
  --output validation\fabest_hcf_package.json
.venv\Scripts\python.exe scripts\validate_pressurized_annulus.py
.venv\Scripts\python.exe scripts\validate_fatigue_endpoint.py
```

## 검증과 미완료 범위

`validation/pressurized_annulus_math.json`은 환형 면적, 극2차모멘트, 명목 축응력,
명목 비틀림 전단응력, 내·외측 반경방향 경계응력과 폐쇄단 축응력을 독립 식과 대조한다.
이 검사는 수학·소프트웨어 검증이며 실험 자격이 아니다.

`validation/fatigue_endpoint_contract.json`은 합성된 네 사건을 사용해 확인된 시편 끝점,
압력계통 중단, runout과 출처 미확정이 서로 섞이지 않는지 검사한다. 임계 압력 저하값을
실험적으로 보정하거나 실제 피로수명을 검증하는 자료는 아니다.

다음 단계는 별도 모듈로 관리한다.

1. 국부 노치 응력장 또는 검증된 응력집중 공급자
2. 임계면과 비비례 하중을 포함한 다축 피로 기준
3. 공개된 실제 파손·runout 결과를 사용한 임계값 검토, 보정과 독립 보류 검증

blind 결과가 공개되기 전에는 목표 수명별 피로강도를 만들어 넣거나 같은 패키지를 독립
검증 자료로 표시하지 않는다.
