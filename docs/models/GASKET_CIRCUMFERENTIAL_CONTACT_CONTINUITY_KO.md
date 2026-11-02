# 가스켓 원주 방향 접촉 연속성 지표

## 목적

`fabrication.gasket_circumferential_contact_continuity`는 계산된 가스켓 압력 field를 caller가 제공한 원주 형상 및 최소 접촉압력 기준으로 분류해 접촉 coverage, 기준압 미달 원주 구간, 가장 긴 기준압 미달 호를 구한다. 한 절점의 압력 한계 여부만 보는 결과와 달리, 미달 영역이 원주 방향으로 어떻게 연결되는지 보여주므로 후속 위험 분석에서 활용할 수 있다.

## 입력과 계보

- 계산 완료된 `fabrication.flange_contact_field`, `fabrication.flange_nonlinear_contact_field` 또는 두 viscoelastic contact history의 `AssessmentResult`와 전체 digest. History는 정확한 출력 knot 시각을 선택해야 한다.
- 원주에 놓인 모든 contact node의 고유 ID 및 각도(rad), 기준 각도와 방향 convention, ring radius(m), 제공자 revision, geometry digest, Evidence, 사용권리 ID.
- caller가 채택한 최소 접촉압력(Pa), 기준 제공자·revision, 상류 결과/time knot까지 포함한 criterion digest, Evidence와 사용권리 ID.
- 물리적 범위·시각, ring geometry·방향, 압력 및 threshold 적용성, 이산 field 해상도, 데이터 권리와 계산 이용에 대한 확인.

상류 계산과 caller geometry 사이 node ID가 정확히 일치해야 한다. 이 모듈은 상류 pressure field를 공간 보간하지 않는다.

## 계산 방법

1. node 각도를 `[0, 2π)` 범위로 정규화하고 circular order로 정렬한다. 중복 각도는 허용하지 않는다.
2. 각 node에 인접한 좌우 각도 간격의 절반씩을 할당해 periodic Voronoi cell 폭을 정의한다. 비균일 mesh도 원주 전체를 나누도록 각 cell의 각도 폭을 계산한다.
3. node 압력이 caller 기준보다 낮으면 해당 node cell을 기준압 미달 cell로 분류한다. 인접 미달 cell을 하나의 미달 원주 호로 묶으며, 0/2π 경계를 넘는 연결도 한 구간으로 합친다.
4. radius `r`을 사용해 원주 길이를 `2πr`, 미달 호 길이를 `r × 미달 각도 합`으로 계산한다. 기준압 충족 coverage는 전체 원주에서 미달 호 길이를 뺀 값이다.

결과에는 기준압 충족 coverage fraction, 기준압 미달 원주 fraction, 미달 구간 수, 가장 긴 미달 호, 각 구간의 각도·길이·포함 node가 포함된다. 여기서 “미달”은 caller pressure threshold에 대한 분류이며, contact mechanics solver의 실제 개방 상태나 누설 상태를 의미하지 않는다.

## Python API

```python
from matintegrity.models.gasket_circumferential_contact_continuity import (
    GasketCircumferentialContactContinuity,
    evaluate_gasket_circumferential_contact_continuity,
)

request = GasketCircumferentialContactContinuity(...)
calculation = evaluate_gasket_circumferential_contact_continuity(request)
```

`specifications()`는 central ModelSpec registry, public schema, capability/source catalog, model reference와 scope trace에 연결되어 있다. 결과는 사용자가 별도 event rule로 정의한 FTA 입력 특성, 실험/FE 후처리와 교차검토에 연계할 수 있으나, 본 계산이 위험 연결이나 인과관계를 자동으로 설정하지는 않는다.

## 해석 제한

- Voronoi cell 분류는 caller mesh에 기반한 이산 근사다. node 사이 실제 접촉 patch나 압력을 재구성하지 않는다.
- 낮은 압력 node의 cell을 threshold 미달로 처리하는 기준은 caller 제공값이다. 보편적 seal criterion이나 누설 경계가 아니며 실제 접촉 gap을 판정하는 의미도 아니다.
- 원주 ring radius와 node 각도는 caller 기하학 근거에 종속된다. 두께 방향, radial contact width, 국부 응력, 변형, 점탄성은 다시 계산하지 않는다.
- 누설률, 허용 여부, 규격 적합성, 수명, 재료 qualification 및 사건확률을 산출하지 않는다.
- 데이터 이용 조건을 Evidence로 고정하고 출처자료를 저장소에 복제하지 않는다.
