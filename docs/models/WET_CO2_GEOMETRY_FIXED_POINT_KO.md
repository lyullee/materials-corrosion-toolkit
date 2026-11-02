# Caller solver를 위한 wet-CO₂ 원통 형상 고정점 제어기

`integration.wet_co2_cylindrical_geometry_fixed_point_controller`는 caller가 제공한 geometry-dependent 계산기를 exact knot별 보어 반경 경로에 반복 적용하는 bounded damped-Picard 제어기다. 이 모듈 자체는 CO₂ 화학, 수송, Butler–Volmer kinetics, 합금 용출률을 계산하지 않는다. 해당 물리 모델은 `candidate_solver` runtime dependency가 매 반복마다 새 반경으로 재계산해야 한다.

## Runtime callback 계약

registry 실행 시 `runtime_dependencies={"candidate_solver": callable}`을 전달한다. 호출은 다음 positional 인자를 받는다.

```python
candidate_solver(request, input_radius_m_by_knot, iteration_index,
                 previous_calculation, fixed_point_input_sha256) -> Calculation
```

반환 `Calculation`은 `status="computed"`여야 하고 `values`에는 아래 항목이 필요하다.

- `model_id`: request의 `solver_model_id`와 동일한 식별자
- `fixed_point_input_sha256`: 전달된 호출 digest와 동일한 값
- `time_s`: request의 exact time grid와 동일한 ordered 값
- `target_bore_radius_m_by_knot`: 해당 고정 형상에서 계산한 다음 형상 또는 반경 응답
- `wall_element_balance_residual_mol_m_by_element`: 원소 ID별로 exact knot 수에 맞는 잔차 배열
- 선택 항목 `wall_element_inventory_scale_mol_m`: 원소별 수지 잔차의 상대허용오차 기준 스케일

원통관 내면 부식은 강재 내면 반경이 외측으로 이동하므로 **보어 반경은 시간에 따라 증가하거나 일정**해야 한다. 입력 seed와 solver target이 이 방향 단조성을 벗어나면 controller는 거부한다. 해당 물리 적용성은 `corrosion_bore_radius_increase_only_reviewed`로 caller가 확인한다.

반복별 입력 digest는 asset/location/time identity, 시간 격자, 현재 반경 벡터 및 caller solver 계약 digest를 고정한다. 결과 digest, 반경 잔차, 원소 재고 잔차 및 모든 반복 입력은 결과에 기록된다. 반경과 inventory closure gate가 동시에 만족할 때만 `computed`를 반환한다. 최대 반복에서 수렴하지 않으면 최종 미수렴 반경을 유효 geometry로 반환하지 않고 `out_of_scope` 진단으로 종료한다.

공간 BV callback은 make_spatial_wet_co2_candidate_solver(spatial_request_template)로 생성할 수 있다. 먼저 adapter를 만든 뒤 WetCo2GeometryFixedPointRequest의 solver_contract_sha256를 candidate_solver.configuration_sha256로 설정하고 solver Evidence에도 같은 digest를 넣는다. Adapter는 각 반복의 보어 반경과 template의 고정 scale phase 재고를 사용해 annular geometry를 재구성하고 spatial BV evaluator의 explicit trial mode를 호출한다. 종·전하·수용액 원소 수지는 유지하며 wall release와 형상의 최종 일치 gate만 고정점 종료까지 보류한다. Scale 재고·kinetics·boundary·material 입력은 template에 고정되며 adapter가 새로운 값을 피팅하거나 추정하지 않는다.

## 가정과 한계

- 입력 보어 반경은 외경보다 작아야 한다. 이 부식 전용 controller에서 보어 반경은 일정하거나 외측으로 증가하며, 외경 도달·초과는 거부한다. 벽 증착·부풀음·scale 외경 성장은 이 controller 범위 밖이다.
- Seed 반경 경로와 매 반복 target 반경 경로는 모두 시간에 따라 비감소해야 한다. 부식 반복에서 각 target은 현재 반경보다 감소할 수 없으며 비물리적 감소는 보정 계수로 숨기지 않고 거부한다.
- knot 사이의 시간 경로 또는 중간 crossing은 만들지 않는다.
- 이 controller는 callback이 물리적으로 올바른 독립 계산을 했는지 증명하지 않는다. callback의 수식, parameter provenance, 질량·전하 보존은 별도로 검토되어야 한다.
- 기본 spatial BV evaluator의 explicit geometry_trial_mode는 wall release와 geometry closure를 분리해 controller에 전체 잔차 ledger를 넘긴다. 제공 adapter가 이 계산을 각 반복 반경으로 재실행한다.
- 이 연결은 caller 입력 kinetics/경계와 고정된 scale 재고에 한정된다. Scale phase kinetics 동시 갱신, 독립 검증, material/service qualification은 여전히 포함하지 않는다.

## 중앙 통합 후 사용 예

```python
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
result = registry.run(
    "integration.wet_co2_cylindrical_geometry_fixed_point_controller",
    request,
    RunContext(asset_id=request.asset_id, location_id=request.location_id,
               time_basis=request.time_basis_id),
    runtime_dependencies={"candidate_solver": caller_solver},
)
```

request의 solver contract 및 Evidence는 caller 계산기의 고정된 API revision을 식별한다. callback 소스, chemistry/transport parameter 및 원자료는 기존 데이터 권리·증거 정책을 따라 별도로 관리한다.
