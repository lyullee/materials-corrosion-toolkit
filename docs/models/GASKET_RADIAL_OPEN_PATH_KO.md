# 가스켓 환형 접촉 압력장의 방사형 개방 경로 스크린

## 목적

`fabrication.gasket_radial_open_path_screen`은 caller의 환형 셀별 평균 접촉압력 맵을 이산 그래프로 해석합니다. caller가 정한 접촉 폐쇄 기준보다 낮은 셀을 잠재 개방 셀로 분류한 뒤, 내경에서 외경까지 연결된 저압 경로가 있는지와 임계 경로의 최소 최대 접촉압력을 계산합니다. 기존 원주 방향 연속접촉 요약과 달리 내·외경 경계를 잇는 방사 방향 2차원 연결성을 평가합니다.

## 격자·면적·연결 계산

입력은 단조 증가하는 radial edge와 한 바퀴를 덮는 angular edge로 정의한 극좌표 annulus입니다. 셀 면적은 다음 극좌표 면적 관계를 사용합니다.

```text
cell_area = 0.5 * (r_outer**2 - r_inner**2) * (theta_outer - theta_inner)
```

셀 평균 접촉압력이 caller 기준보다 작으면 해당 셀을 개방 상태로 분류합니다. 그래프에서 반경 방향 이웃과 원주 방향 좌우 이웃만 연결하며 원주 경계는 주기적으로 이어집니다. 대각선 셀끼리는 연결하지 않습니다. 연결 성분을 탐색하여 내경·외경을 함께 접하는 개방 영역을 찾습니다.

추가로 가중 minimax 경로를 계산합니다. 모든 내경 셀에서 출발해 각 경로에서 가장 높은 셀 압력이 최소가 되는 외경 도달 경로를 반환합니다. 이 값은 caller 임계값 아래의 연결 경로 존재 여부를 구분하는 그리드 기반 bottleneck pressure입니다. 경로 좌표는 격자 인덱스로 반환하며 유체 유량으로 해석하지 않습니다.

## 입력 및 데이터 근거

- 완전한 원주각과 방사 방향을 덮는 격자 경계 및 셀별 평균 압력
- 물리 범위·자료시점·단위·압력 정의·mesh mapping이 기록된 pressure map
- 해당 가스켓 joint에 적용할 caller 임계 접촉압력 기준과 Evidence
- 압력 기준의 비교 규칙 및 4-이웃 원주주기 연결 규칙에 대한 검토
- mesh resolution, 표면 방향, 개방 경계 위치, 데이터 사용권 및 계산 사용 권한 검토

맵과 threshold 기준에는 별도의 제공자·revision·digest·사용권 Evidence가 필요합니다. 데이터나 기준을 찾지 못하면 caller가 제공할 때까지 적합한 경로 계산을 주장하지 않습니다.

## 적용 한계

- 입력은 셀 평균 접촉압력만 나타냅니다. 실제 표면 거칠기, sub-cell 접촉 섬, 간극 높이, 유체·압력 효과, 가스켓–플랜지 접착 및 누설 경로 개구 형상은 계산하지 않습니다.
- 개방 상태를 접촉압력 한계로 구분하는 것은 caller가 선언한 스크린 정의입니다. 재료와 조인트에 보편적으로 적용되는 밀봉 임계압력을 뜻하지 않습니다.
- 유한 격자에서의 4-이웃 연결성은 격자 분해능과 대각선 연결 관례에 의존합니다. 실제 연속 표면의 percolation 전이, 누설률, 압력 수용 또는 seal acceptance로 바꾸어 해석하지 않습니다.
- 면적 가중 평균압력과 임계경로 지수는 전처리된 caller pressure field로부터 얻는 기하 요약값입니다. flange FE 응답을 만들거나 응력·변형장을 역산하지 않습니다.

## 독립 참고자료와 source ID

공개 연구는 가스켓/씰의 비접촉 영역 연결성이 누설경로 형성에 중요하다는 배경만 제공합니다. 논문에서 제안한 경험 계수나 percolation 임계값은 코드에 복사하지 않았습니다. 이 모델은 별도의 caller 임계 접촉압력과 유한 환형 격자의 그래프 연결을 사용합니다.

- H. Li et al., “Analytical model for the sealant performance of tunnel gasketed joints based on multi-scale contact and percolation theories,” *Underground Space* 14 (2024), 319–337. [DOI: 10.1016/j.undsp.2023.08.004](https://doi.org/10.1016/j.undsp.2023.08.004)
- I. Nitta and Y. Matsuzaki, “Visualisation Of The Real Contact Area At Gasket Surfaces Using Thin PC Films,” *WIT Transactions on Engineering Sciences* 49 (2005). [DOI: 10.2495/SECM050321](https://doi.org/10.2495/SECM050321)

카탈로그 source ID 제안:

- `caller_gasket_annular_contact_pressure_map`
- `caller_radial_seal_threshold_and_mesh_connectivity`
- `annular_cell_area_and_four_neighbor_radial_path_graph`
- `gasket_contact_open_path_topology_screen`

## Python API

```python
from matintegrity.models.gasket_radial_open_path import (
    GasketRadialOpenPathScreen,
    evaluate_gasket_radial_open_path_screen,
)

result = evaluate_gasket_radial_open_path_screen(request)
```

- Model ID: `fabrication.gasket_radial_open_path_screen`
- Schema: `matintegrity.gasket_radial_open_path_screen.v1`

문서와 코드 설명은 독립적으로 작성했으며, 공개 자료의 문장을 복사하지 않았습니다.
