# 사용자 표형 피로균열성장 곡선

## 목적과 경계

`fracture.tabulated_growth_rate`와 `fracture.tabulated_crack_growth`는 사용자가 합법적으로 사용할 수
있는 `ΔK–da/dN` 점을 직접 공급하는 경로다. 패키지는 재료별 계수, 규격 설계곡선, 허용값 또는
제3자 점별 표를 포함하지 않는다. 곡선은 재료상태·환경·응력비·주파수·source group·내용 해시와
함께 입력하며, 점별 계산 이용권한과 적용성 검토를 `true`로 명시해야 한다.

수명 적분 요청은 평가 대상의 `material_condition_id`와 `environment_id`를 별도로 선언하고
곡선과의 매핑 검토를 명시해야 한다. 미지정·미검토 상태는 `needs_data`, 곡선과 대상의 재료상태나
환경이 다르면 `out_of_scope`로 종료한다. 곡선군도 대상 재료상태·환경 일치 검토를 요구한다.
따라서 미상 주파수 자료는 ΔK별 속도 조회에 쓸 수 있지만 하중 이력 수명 적분이나 주파수 기준
곡선 선택에 사용할 수 없다.

`fracture.tabulated_curve_family_growth`는 같은 재료상태와 환경의 여러 곡선을 묶는다. 각 하중
block의 응력비 절대차와 주파수 상대차를 호출자 허용차와 비교한 뒤, 정규화 거리가 가장 작은 곡선
하나만 선택한다. 허용차 안에 곡선이 없거나 최소거리 동률이면 `out_of_scope`로 중지한다. 응력비·
주파수·환경·재료상태 또는 source group 사이의 보간·평균·회귀는 수행하지 않는다.

`fracture.tabulated_crack_growth_uncertainty`는 호출자가 만든 정규화 공동 표본으로 단일 곡선 또는
곡선군 계산을 반복한다. 각 행은 성장률·형상계수·인장응력·파괴인성의 전역 배수와 고유 ID·가중치를
갖는다. 한 행 안의 값은 상관된 공동 표본으로 유지하며 계산기가 난수를 만들거나 가중치를 재정규화·
적합하지 않는다. 하나라도 결정론 적용범위를 벗어나면 모든 표본은 보존하되 평균·표준편차·분위수와
깊이 초과확률을 전부 보류한다.

`fracture.tabulated_crack_growth_uncertainty_convergence`는 같은 입력분포와 결정론 기준모델에 대해
두 개 이상의 표본설계를 순서대로 비교한다. 각 단계는 initial·nested refinement·일반 refined design·
independent replicate 관계 중 하나를 명시한다. nested refinement는 표본 수를 늘리고 기존 ID와 배수행을
그대로 유지해야 하지만 정규화 가중치는 바뀔 수 있다. 가중 평균·표준편차·분위수·초과질량 변화량을
호출자가 검토한 깊이 척도와 허용값으로 비교한다. 기준 만족은 표본설계 안정성 진단일 뿐 수렴 증명,
오차상한, 분포 검증 또는 충분한 표본 수 보증이 아니다.

`fracture.tabulated_crack_growth_scenario_ensemble`은 전역 배수로 축약할 수 없는 불확실성을 위한
경로다. 각 가중 행이 단일곡선 또는 곡선군 결정론 입력 전체를 포함하므로 개별 성장곡선 점, 곡선군
구성, 형상계수 knot, 순서 있는 하중 block, 인성과 수치 제어를 한 공동 시나리오 안에서 함께 바꿀
수 있다. 모든 행은 같은 물리 균열 범위를 가져야 하고 scenario/source ID·source digest·결정론 입력의
canonical digest를 보존한다. 계산기는 시나리오를 생성·적합·보간하거나 확률을 부여하지 않는다.
한 시나리오라도 적용범위 밖이면 모든 행을 남기고 집계 통계를 전부 보류한다.

대규모 시나리오는 `crack_growth_scenario_manifest`, `evaluate_crack_growth_scenario_job`과
`fracture.tabulated_crack_growth_scenario_reduction`으로 분산할 수 있다. 각 map 결과는 scenario ID,
결정론 입력 digest, evaluator ID·revision·configuration digest와 result digest를 가진다. reducer는
manifest와 평가 ID 집합의 정확한 일치 및 모든 digest/평가자 identity를 확인하고 manifest 순서로
복원한다. 누락·추가·중복·혼합 리비전은 거절하며 실패행을 버리거나 나머지 가중치를 재정규화하지
않는다. Slurm 명령은 [HPC 검증 문서](HPC_VALIDATION_KO.md)에 있다.

보간은 인접한 두 점 사이에서 `log(ΔK)–log(da/dN)` 선형으로만 수행한다. 아래쪽 문턱과 위쪽
성장률을 추정하지 않는다. 첫 점보다 낮은 영역을 0 성장으로 취급하려면 사용자가 별도의 문턱을
선언해야 하며, 문턱과 첫 점 사이의 빈 범위는 계속 적용범위 밖이다. 마지막 점을 넘으면 계산은
`out_of_scope`로 종료한다.

공식 시험방법의 공개 범위는 환경·응력비·주파수와 closure 등 변수가 성장곡선 해석에 영향을 줄 수
있음을 설명한다. 이 프로젝트는 유료 표준 본문·그림·시험절차를 복제하지 않고 공식 서지와 공개
범위만 참조한다. [ASTM E647 공식 페이지](https://store.astm.org/standards/e647)

## Python 예제

```python
from matintegrity import evaluate
from matintegrity.contracts import RunContext

curve = {
    "schema_version": "matintegrity.tabulated_crack_growth_curve.v1",
    "curve_id": "my-reviewed-curve-v1",
    "source_group_id": "my-authorized-source",
    "material_condition_id": "steel-heat-treatment-a",
    "environment_id": "reviewed-environment-a",
    "stress_ratio": 0.1,
    "frequency_Hz": 1.0,
    "delta_k_Pa_sqrt_m": [5e6, 10e6, 20e6],
    "crack_growth_m_cycle": [1e-8, 8e-8, 6.4e-7],
    "interpolation": "log_delta_k_log_growth_linear",
    "below_minimum_policy": "out_of_scope",
    "declared_threshold_delta_k_Pa_sqrt_m": None,
    "source_content_sha256": "a" * 64,
    "pointwise_computational_use_authorized": True,
    "curve_applicability_reviewed": True,
    "physical_specimen_identity_status": "identified",
}

context = RunContext(
    asset_id="pipe-01",
    location_id="reviewed-crack-01",
    time_basis="ordered load blocks from reviewed history",
)
result = evaluate("fracture.tabulated_crack_growth", {
    "schema_version": "matintegrity.tabulated_crack_growth.v1",
    "assessment_id": "growth-run-01",
    "physical_scope_id": "crack-front-01",
    "initial_depth_m": 0.001,
    "terminal_depth_m": 0.004,
    "geometry_depth_m": [0.0005, 0.004],
    "geometry_factor": [1.12, 1.12],
    "blocks": [{
        "minimum_stress_Pa": 10e6,
        "maximum_stress_Pa": 100e6,
        "cycles": 1000.0,
        "frequency_Hz": 1.0,
    }],
    "curve": curve,
    "maximum_absolute_stress_ratio_difference": 0.0,
    "maximum_relative_frequency_difference": 0.0,
    "fracture_toughness_Pa_sqrt_m": 100e6,
    "relative_integration_tolerance": 1e-8,
    "absolute_cycle_tolerance": 1e-6,
    "absolute_depth_tolerance_m": 1e-12,
    "geometry_solution_reviewed": True,
    "load_to_curve_mapping_reviewed": True,
    "toughness_application_reviewed": True,
}, context)
```

하중 block의 응력비와 주파수는 곡선 조건에서 사용자가 선언한 허용차 안에 있어야 한다. 형상계수는
평가 깊이 전체를 덮는 양의 비감소 표만 지원하고 선형 보간한다. 순서 있는 인장 block만 다루며
closure, 과대하중 지연, 압축, 소성, 잔류응력, 균열 개시와 block 상호작용은 포함하지 않는다.

최대 K가 사용자가 공급한 파괴인성에 도달한 경우, 마지막 성장곡선 점에 도달한 경우와 선언 깊이에
도달한 경우를 서로 다른 종료 사유로 보존한다. `computed`는 입력된 사용자 모델의 수치 계산이
완료됐다는 뜻이며 설비 합격·잔여수명 보증·고장확률 또는 규격 적합을 뜻하지 않는다.

## 수소 피로 자료와의 관계

HyMatBase 4130X workbook의 네 곡선은 record와 workbook의 압력이 각각 4.5 MPa와 45 MPa로
충돌하고 점별 재이용 권리가 명시되지 않았다. 따라서 그 점을 이 계산기의 내장곡선이나 자동 예제로
옮기지 않았다. 사용자가 압력·온도·재료상태·시편 계보·이용권한을 독립적으로 해소한 경우에만 같은
중립 계약으로 매핑할 수 있다.

## 검증과 재현

`scripts/validate_tabulated_crack_growth.py`는 외부 점별 자료를 사용하지 않고 작성한 3차 power-law
점으로 보간값과 닫힌형식 Paris 적분을 비교한다. 현재 보간 상대차는 약 `2.22e-16`, 1,000 cycle 후
깊이 상대차는 약 `2.20e-11`이다. 곡선 상한 깊이는 독립식과 일치하고 `out_of_scope` 종료를 유지한다.
결과는 `validation/tabulated_crack_growth_math.json`에 기록된다. 이는 수학 검증이지 실제 재료·환경·
형상·하중 또는 수명의 실험 자격화가 아니다.

두 점 공동 입력분포 검증에서는 성장률 배수 0.5와 2.0에 각각 0.25와 0.75의 질량을 주었다. 가중
평균 최종깊이의 닫힌식 대비 상대차는 약 `6.21e-14`이고, 선언 깊이 초과질량은 `0.75`다. 이 값의
확률 의미는 `model_implied_input_uncertainty_probability`이며 기간 최초고장확률·관측빈도·FTA
기초사건확률·신뢰한계 또는 모델형식 불확실성이 아니다.

퇴화된 동일 공동분포의 2행→4행 nested refinement 검증에서는 모든 통계 변화량이 0이고 진단 기준을
만족한다. 별도 단위검사는 새 행이 통계를 바꾸면 계산은 완료하되 기준 미충족을 보존하고, 적용범위 밖
행이 있으면 단계와 전체 진단을 `out_of_scope`로 유지하며 수렴 주장을 보류하는지 확인한다. 기존 ID
삭제·기존 배수 변경·거짓 initial 관계도 입력 검증에서 거절한다.

완전입력 시나리오 검증은 성장률을 각각 0.5배와 2배로 만든 두 전체 입력에 0.25와 0.75의 질량을
부여했다. 전역 배수 경로 및 각 닫힌형식 깊이를 직접 가중한 평균과 약 `6.21e-14` 상대차로 일치하고,
0.00102 m 초과질량은 0.75다. 별도 검사는 곡선 한 점·형상 knot·특정 하중 block·인성을 동시에
변경한 입력 digest와 결과가 구분되는지, 실패 시나리오가 삭제되지 않는지, 중복 ID·가중합 오류·
물리 범위 혼합을 거절하는지 확인한다.

portable map/reduce 검증은 같은 두 시나리오를 개별 평가한 뒤 결과 순서를 반대로 공급했다. reducer가
manifest 순서를 복원하고 in-process 평균과 절대차 0으로 일치하는지 확인했다. 누락/추가 ID, 입력
digest 불일치, 다른 evaluator revision은 거절하며 `execution_failed` 행은 그대로 남기고 평균·분위수·
초과질량을 보류한다. 이는 직렬화와 집계 계약 검증이지 Slurm·파일시스템·물리모델 자격화가 아니다.
