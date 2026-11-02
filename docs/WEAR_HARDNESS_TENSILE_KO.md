# 마모·경도 기준블록·인장 offset-yield

## Archard 마모계수 보정

`degradation.archard_wear_coefficient_calibration`은 하나의 검토된 재료·상대재·접촉형상·윤활
regime에서 각 유효 관측의 `k = V H / (F s)`를 계산하고 calibration 행의 가중 기하평균을
구한다. 마모체적은 m³, 경도는 Pa, 법선력은 N, 미끄럼거리는 m로 입력한다. 물리 시편과 source
group은 calibration과 holdout에 동시에 등장할 수 없다. Holdout 진단은 온도·하중·거리·경도와
경도 identity가 calibration 지원범위 안에 있을 때만 계산한다. Fretting-corrosion 상호작용,
운전수명, 합격 또는 고장확률은 생성하지 않는다.

## 경도 기준블록 보정

`inspection.hardness_reference_block_calibration`은 하나의 method·scale·indenter·load·dwell·장비
configuration에 대해 인증 기준블록의 observed-minus-certified bias와 repeatability를 적합한다.
인증값 표준불확도와 caller weight를 likelihood에 포함하고, 물리 블록·source·independence group의
분할 누출을 차단한다. Holdout은 인증값과 온도 지원범위 안에서만 bias-corrected residual,
RMSE와 log-likelihood를 만든다. Scale 변환, 인장강도 추정, 규격 합격판정은 하지 않는다.

## 원 stress–strain offset-yield

`inspection.tensile_offset_yield_curve`는 엄격히 증가하는 engineering-strain branch의 검토된 elastic
window에 가중 직선을 적합하고, 선언 offset과 평행한 선의 유일한 교차를 선형 보간한다. 시편,
gauge length, extensometer, 장비 configuration과 원 curve digest를 보존한다. 교차가 없거나 복수이면
임의 선택하지 않고 `needs_data`다. True-stress 변환, necking 이후 추론, 합격 또는 확률은 만들지 않는다.

## 공개 tribology metadata

Zenodo `10.5281/zenodo.7923128`의 CC BY 4.0 RDF Turtle 57개 파일, 15,578,599바이트를
제공자 MD5로 고정했다. `audit_tribology_metadata_dataset`은 완전한 파일 집합, 크기, MD5와 SHA-256,
experiment/equipment/specimen/consumables/software 역할만 감사한다. 제공자가 연결한 원시·가공
측정값 RO-Crate는 이번 배치에 취득하지 않았다. 따라서 RDF 기록을 독립 시편, wear volume,
hardness, Archard calibration 행 또는 수명자료로 자동 변환하지 않는다.

```powershell
python scripts/inspect_tribology_metadata_data.py
python -m pytest -q tests/test_archard_calibration.py tests/test_hardness_reference_calibration.py tests/test_tensile_offset_yield_curve.py tests/test_tribology_metadata_data.py
```
