# Chronoamperometry 창 요약

## 목적

`corrosion.chronoamperometry_window_summary`는 특정 논문이나 제공자 feature 정의를 복제하지 않는
일반 신호 계약이다. 사용자가 가진 시간–전류 표에 provenance와 분석창을 붙여 즉시 호출할 수 있다.
원자료를 평활하거나 부식 사건으로 분류하지 않고 재현 가능한 기본 적분량만 만든다.

## 필수 입력

- 고유 trace·물리 시편·source group ID
- 원 trace SHA-256과 선택적인 archive/member SHA-256
- 엄격히 증가하는 유한 `time_s`와 같은 길이의 유한 `current_A`
- 분석창과 선택적인 baseline 창
- `exact_samples` 또는 `piecewise_linear` 경계정책
- 시료 순서, s, A와 보고 전류 부호 basis의 검토 상태

`piecewise_linear`는 요청한 창의 시작·끝에만 보간점을 넣는다. 내부 시료는 정렬·재표본화하지 않는다.
창 밖으로 외삽하지 않으며 `exact_samples`에서 경계가 실제 시료가 아니면 중지한다.

## 출력과 수학

signed charge는 조각선형 전류의 사다리꼴 적분이다. absolute charge와 positive/negative polarity
charge는 선분이 0을 지나는 실제 위치에서 구간을 나눠 계산한다. 따라서 양·음 극성 전하는 절댓값
전하로 합쳐지고, 부호 있는 전하의 차이와 일치한다. 시간가중 평균은 signed charge를 창 길이로 나눈다.
최소·최대 전류가 plateau면 첫 시각과 마지막 시각을 모두 보존한다. baseline도 시료 산술평균이 아니라
해당 창의 시간가중 평균이다.

## SECCM 연동 예

```python
from matintegrity.adapters import seccm_chronoamperometry_summary_inputs
from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry
from matintegrity.seccm_data import read_seccm_ca_trace

trace = read_seccm_ca_trace(
    local_zip,
    1,
    physical_specimen_id="provider-map-physical-scope-unresolved",
    source_group_id="seccm-map-1031-c",
)
inputs = seccm_chronoamperometry_summary_inputs(
    trace,
    analysis_window_s=[0.0, 59.9915],
    boundary_policy="exact_samples",
    current_sign_basis="provider-reported sign; electrochemical polarity not inferred",
    current_sign_reviewed=True,
)
result = default_registry().run(
    "corrosion.chronoamperometry_window_summary",
    inputs,
    RunContext(asset_id="provider-map", location_id="MAP_Point_1", time_basis="provider hold"),
)
```

## 해석 제한

positive/negative polarity는 계측 신호의 부호를 나눈 것이며, 검토된 부호 basis가 없으면 양극/음극
또는 산화/환원으로 명명할 수 없다. signed·absolute·polarity charge는 모두 신호 요약이며 금속
용출량이 아니다. Faraday 질량손실로 바꾸려면 이 trace에서 전기이중층·배경·다른 반응의 전류를
분리할 근거, 반응 valence, 유효 면적, 밀도와 전류효율을 별도로 검토해야 한다. baseline 창은 부식기구를 정의하지 않는다. 극값도 peak event나 pit initiation으로
자동 분류하지 않는다. 같은 map의 여러 위치는 독립 시편이 아니다. 따라서 이 출력만으로 provider
descriptor 재현, 전기화학 반응 분리, pit 치수, 분류 정확도, POD, 합격, 잔여수명 또는 고장확률을
주장하지 않는다.
