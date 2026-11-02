# 범주형 상지도 연결 영역·격자 경계 요약

`phase_map_topology.summarize_phase_map_topology()`는 리뷰된 정수 라벨 이미지에서 선택 ROI의 연결 성분 수, 성분 픽셀 크기 요약, ROI·결측 경계 접촉 수와 인접 범주 사이의 격자 공유변 길이를 만든다. 결과 계약은 `PhaseMapTopologySummary`다. 원 배열·ROI·결측 mask의 digest를 기존 phase-map 계약으로 먼저 확인한다.

```python
from matintegrity.phase_map_topology import summarize_phase_map_topology

summary = summarize_phase_map_topology(labels, roi_mask, missing_mask, reviewed_metadata, connectivity=4)
```

4 연결성은 변끼리 이웃한 픽셀만 같은 성분으로 묶고 8 연결성은 대각선 이웃도 허용한다. 경계 길이는 4방향 이웃 격자 변 개수에 직사각형 픽셀의 선언된 높이 또는 폭을 곱한 표본 이미지 길이다. ROI 가장자리에서 잘린 성분과 결측에 닿는 성분은 별도 개수로 표시한다. 미분류 범주와의 인접도 원래 라벨을 유지한다.

이는 영상 격자의 기하 descriptor이며 결정립 분할·입체계측 보정·실제 계면의 3차원 면적·상평형·재료 물성·부식 속도·위험도·합격 판단이 아니다. 픽셀 크기와 축 정합은 사용자가 검토해야 하며 분할·해상도·대표성의 불확도는 산출하지 않는다. 8 연결성은 구성 요소 개수만 바꾸고 경계 길이는 두 범주가 실제 격자 변을 공유하는 경우만 센다. SciPy는 `[science]` 선택 의존성이다.

합성 예는 `examples/phase_map_topology.py`, 아직 실행하지 않은 회귀 입력은 `tests/test_phase_map_topology.py`이며 HPC 일괄 manifest에 추가된다. 기존 area-fraction 및 Oxford reader 경계는 [PHASE_LABEL_MAP_KO.md](PHASE_LABEL_MAP_KO.md)에 있다.
