# 공개 습식 CO₂ 시뮬레이션 grid reader

`matintegrity.wet_co2_data.read_wet_co2_simulation_grid(path)`는 Mendeley Data `10.17632/4nydhxjymw.1`의 CC BY 4.0 Excel workbook을 읽는다. reader는 pinned SHA-256, 파일 크기 상한, 단일 worksheet, 열 순서와 공급자 단위표를 확인하며, 243개 데이터 행을 `WetCo2SimulationGridRow` typed record로 반환한다. [데이터셋](https://data.mendeley.com/datasets/4nydhxjymw/1).

반환 계약은 온도를 K, 두 압력을 Pa, inhibitor efficiency를 0–1 fraction, rate를 m/s로 표현한다. 변환은 workbook 내부 표에 선언된 °C, bar, percent, mm/year 단위에 한정한다. 전단응력은 Pa, 유속은 m/s이며 pH는 공급 숫자를 보존한다. 각 행에는 provider row, archive digest, DOI, CC BY 4.0 evidence가 있다. 모의 데이터는 실험 시편 ID나 독립 물리 관측으로 승격되지 않는다.

```python
from matintegrity.wet_co2_data import read_wet_co2_simulation_grid

rows = read_wet_co2_simulation_grid(
    "data/raw/norsok-m506-simulation-grid/Dataset for internal CO2 corrosion of oil pipeline.xlsx"
)
print(len(rows), rows[0].temperature_K, rows[0].corrosion_rate_m_s)
```

자료는 `data/raw/`에만 선택적으로 내려받고 wheel, sdist, review archive에 포함하지 않는다. CSV 형식으로 편집된 이종 CO₂ 데이터의 첫 243행과는 별도 crosswalk가 정확 일치한 경우에만 source identity를 연결할 수 있다. 계수만 비슷하거나 총행 수가 일치한다는 이유로 row mapping을 추론하지 않는다.

`WetCo2SimulationGridSummary`와 `summarize_wet_co2_simulation_grid(request)`는 선택된 같은 원본 workbook 행들의 수치 범위·산술평균·호출자 지정 분위수를 요약한다. 행별 가중치는 균등하게 취급한다고 명시하고 원행 번호·dataset·archive digest를 보존한다. 혼합 digest나 중복 provider row는 거절한다. 이 기술 요약은 provider 출력의 분포나 확률보정 의미를 확인하지 않으며 평균/분위수를 failure probability, 실험 통계, 보정 데이터 또는 재료 ranking으로 해석하지 않는다.

이 reader는 공급자 시뮬레이션 결과를 재현하거나 NORSOK 규격을 구현하지 않는다. 데이터셋 라이선스는 표준 문서, 표준 구현 또는 derivative surrogate의 공개 권리를 부여한다고 간주하지 않는다. 243개 응답은 해당 공급자 모델의 표본 domain과 가정에 종속되어 물리 실험 검증, 재료 적합성, 부식률 예측 자격, 수명·구조판정·위험확률을 입증하지 않는다. 다른 단위나 workbook 개정은 자동 추정하지 않고 고정 reader 검증에서 거절한다.

`examples/wet_co2_simulation_grid.py`는 reader와 같은-row-summary API를 연결해 source digest와 모델 출력으로 한정된 요약을 표시한다. `tests/test_wet_co2_data.py`에는 합성 workbook의 단위·provenance·summary 경계 회귀가 추가되어 batch75에서 실행하도록 기록했다. 현재 pytest와 실데이터 reader 계산은 로컬에서 실행하지 않았다.
