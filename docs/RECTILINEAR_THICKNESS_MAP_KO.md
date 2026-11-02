# 직교 두께 지도 요약

`geometry.rectilinear_thickness_map`은 셀 경계와 셀 중심 두께 측정값을 받아 실제 셀 면적에 따른 평균 두께, 측정 면적, 결측 면적, 부호 있는 관측 손실 체적, 임계 두께 이하 영역의 연결 성분 면적을 계산한다.

입력은 SI 단위다. `None`은 미측정 셀로 유지되며 두께 요약이나 손실 체적에 포함하지 않는다. 격자 내 결측값을 건전 두께로 간주하거나 공간 보간하지 않는다. `threshold_comparison`으로 임계값 동등 포함 여부를 지정하고 `connectivity`는 `four_neighbour`(공유 변 경계) 또는 `eight_neighbour`(변 또는 꼭짓점 접촉)를 선택한다. 대각선 연결은 두번째 선택에서만 하나의 성분으로 묶인다.

```python
from matintegrity.models.rectilinear_thickness_map import (
    RectilinearThicknessMap,
    rectilinear_thickness_map,
)

inputs = RectilinearThicknessMap(
    x_cell_edges_m=[0.0, 0.01, 0.03],
    y_cell_edges_m=[0.0, 0.01, 0.04],
    cell_thickness_m=[[0.010, 0.009], [None, 0.006]],
    reference_thickness_m=0.010,
    reporting_threshold_m=0.008,
    threshold_comparison="less_than",
    connectivity="eight_neighbour",
)
result = rectilinear_thickness_map(inputs)
```

출력은 측정 격자의 기하·면적 요약일 뿐이다. 구조 건전성 적합, 허용기준, 잔여수명, 부식률, 결함 검출확률 또는 확률적 위험 판정을 제공하지 않는다. 연결성 선택은 격자 해상도와 후속 분석 정의에 맞춰 호출자가 기록한다. 입력 검증과 면적 수지 회귀는 `tests/test_rectilinear_thickness_map.py`에 있으며 HPC manifest의 `batch56-rectilinear-thickness-map` 작업에 포함된다.
