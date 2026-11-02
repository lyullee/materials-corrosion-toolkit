# 수소 재료수송 결과 교환

`HydrogenTransportHistory`는 외부 수소 수송 해석기가 만든 1차원 농도·재고 이력을 JSON으로 보존하는 공급자 중립 계약이다. 단위는 필드명에 고정하고, 운반체가 원자 H인지 분자 H2인지 명시한다. 공급자·리비전·solver·재료상태·기준격자·시간원점과 native 결과 SHA-256을 함께 보존한다.

지원하는 기하는 평판과 구형 쉘이다. 면 위치·면적, 셀 중심·체적, 시간×셀 이동농도, 시간×트랩×셀 포획농도, 좌우 좌표방향 누적유량, 벽 재고와 벽/전체 보존잔차를 받는다. 모든 배열은 공통 시간·격자와 정렬되어야 한다. 음의 농도는 선언한 수치 허용오차 안에서만 보존하며 자동으로 0으로 자르지 않는다. 전체 payload digest가 값·단위 정체성·공급자 리비전의 변조를 검출한다.

```python
from matintegrity.hydrogen_exchange import hydrogen_transport_history

record = hydrogen_transport_history(
    provider_id="my-transport-provider",
    provider_revision="reviewed-revision",
    solver_id="one-dimensional-finite-volume",
    result_id="run-001",
    native_result_sha256="0" * 64,
    material_condition_id="alloy-state-001",
    reference_lattice_id="lattice-basis-001",
    carrier="atomic_hydrogen",
    carrier_molar_mass_kg_mol=0.00100794,
    geometry="planar",
    trap_population_ids=[],
    elapsed_time_origin_id="charging-start",
    time_s=[0.0, 1.0],
    face_positions_m=[0.0, 0.001, 0.002, 0.003],
    cell_centers_m=[0.0005, 0.0015, 0.0025],
    face_areas_m2=[1.0, 1.0, 1.0, 1.0],
    cell_volumes_m3=[0.001, 0.001, 0.001],
    mobile_entity_mol_m3=[[1.0, 1.0, 1.0], [0.9, 1.0, 1.1]],
    trapped_entity_mol_m3=[[], []],
    left_integrated_coordinate_flow_mol=[0.0, -1e-6],
    right_integrated_coordinate_flow_mol=[0.0, -1e-6],
    wall_inventory_mol=[0.003, 0.003],
    wall_inventory_residual_mol=[0.0, 0.0],
    total_inventory_residual_mol=[0.0, 0.0],
    concentration_numerical_tolerance_mol_m3=1e-10,
    function_evaluations=20,
    coefficient_basis="reviewed coefficient record identifier",
    boundary_basis="reviewed boundary record identifier",
    limitations=["No stress coupling or damage inference."],
)
```

이 계약은 외부 결과를 MatIntegrity의 계산 결과로 가장하지 않는다. 누적 좌표유량을 순간 검출기 유량으로 임의 미분하지 않고, 원자/분자 mol을 자동 변환하지 않으며, 수송 결과에서 취성화·균열성장·수명·고장확률을 만들지 않는다. 실제 연계에는 같은 재료상태·격자·표면·시계의 검토, 계수 자격화, 공간·시간 수렴, 질량보존, 독립 투과 또는 탈리 실험 비교가 별도로 필요하다.

`scripts/validate_hydrogen_transport_exchange.py`는 합성 보존 항등식의 JSON 왕복, 배열 정렬, 값 변조 거절을 검사한다. 이는 교환계약 검증이며 물리모델 또는 실험 검증이 아니다.
