# 전기화학 partial current에서 금속손실 장부로 변환

`integration.electrochemical_partial_current_metal_loss`는 computed `electrochemistry.crevice_mixed_potential_history` 결과의 각 반응별 current-density history를 caller가 지정한 금속 dissolution mapping에 연결한다. upstream 전체 결과 SHA-256, input digest, history digest, reaction ID, 전자수, 기준 전극, 시각 및 reference area를 확인한다. 전자수와 branch 실제 노출면적은 고정된 upstream 요청에서 읽어오며 다시 입력받지 않는다.

사용자는 각 금속 반응에 대해 금속 종, 반응 진행량당 용출 금속 원자수, 몰질량, 밀도, material condition ID, 재료 자료 provider/revision/record/SHA-256 및 일치하는 Evidence를 제공한다. 양극 방향이 해당 금속의 용출이라는 점, 합금 선택성·금속 기준, 반응 set의 mapping 완전성, 실제 면적 및 균일 평균 recession 가정을 명시적으로 검토해야 한다. 근거로 연결한 물성은 자료 계보일 뿐 그 값의 적합성 검증은 아니다.

구간 current는 caller가 검토한 선형 재구성으로 적분한다. 기준면적 current density를 (j(t)), upstream 기준면적을 (A_r), 구간을 ([t_0,t_1])이라 하면 (Q=A_r(t_1-t_0)(j_0+j_1)/2)이다. branch 전자수 (n)에서 반응 진행량은 (Q/(nF))이며, caller metal stoichiometry와 몰질량을 적용한다. anodic charge, cathodic equivalent, signed charge, 순 metal mol·kg 및 실제 mapped exposed area에 대한 signed 평균 recession을 별도로 반환한다. 음의 signed loss는 선택 반응식 방향에서 순환원/재석출 equivalent를 표시하며, 그 물리적 해석은 caller 책임이다.

```python
from matintegrity import evaluate

result = evaluate(
    "integration.electrochemical_partial_current_metal_loss",
    request,
    upstream_context,
)
```

최소 JSON contract는 `docs/schemas/ElectrochemicalMetalLossHistory.json`과 `docs/schemas/MetalDissolutionReactionMapping.json`을 참조한다. `examples/crevice_electrochemical_composition.py`는 합성 property Evidence를 포함한 wiring을 보여준다.

이 API는 선택한 caller reaction만 적분한다. 금속 용출 반응을 빠짐없이 mapping했다는 review가 없으면 완전한 총 금속손실로 볼 수 없다. 막 형성·부동태·전달 제한·국부 공격·합금 선택적 용출·계면 moving boundary·균열/구조 건전성·허용기준은 계산하지 않는다. current interpolation, kinetic calibration, stoichiometry, 재료상태, 실제 면적과 부식 적용성은 별도 검토 대상이다. 계산 결과는 부식률 qualification·잔여수명·확률·fitness-for-service 판정을 뜻하지 않는다.

합성 wiring 예제 실행, 수치 회귀, 독립 실험 비교와 HPC 검증은 아직 하지 않았다. 연결된 모든 upstream current 및 금속 자료가 실제 대상 조건에 적용된다고 보증하지 않는다.
