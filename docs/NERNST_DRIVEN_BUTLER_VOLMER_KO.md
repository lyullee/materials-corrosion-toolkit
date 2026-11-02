# Nernst 전위에서 Butler–Volmer 반응 flux로의 연결

`electrochemistry.nernst_driven_butler_volmer_history`는 `degradation.crevice_nernst_potential_history`의 computed 결과를 받아 caller가 제공한 표면 금속-용액 전위 이력과 한 개의 Butler–Volmer 반응 파라미터를 동일한 clock ID와 시각 knot에서 결합한다. upstream assessment의 입력 digest와 전체 결과 SHA, Nernst potential-history SHA를 확인하고 redox reaction ID, clock ID와 표준전위 기준전극 ID를 반응·전극 입력과 대조한다.

각 knot에서 `η = E_surface − E_eq(t)`를 계산하고 caller가 제공한 교환전류밀도, 전자수, 전달계수, 온도 및 overpotential 유효범위를 사용해 기존 Butler–Volmer 계산식을 평가한다. 결과는 부호 있는 부분 전류밀도, gross anodic/cathodic 성분, 반응 진행속도, caller 화학양론으로 계산한 종별 flux와 전체 lineage를 반환한다. 시간 knot 사이의 보간과 적분은 수행하지 않는다.

이 연결에는 실제 기준전극 일치, 반응방향·전자수, species-flux 화학양론, 표준상태와 각 온도에서 rate parameter 적용성 검토가 필요하다. 한 반응의 partial current history이며 혼합전위, 다중 반응 연성, charge 적분, 총 금속 손실/부식률, scale 보호효과 또는 수명·acceptance를 의미하지 않는다. `examples/crevice_nernst_profile.py`는 synthetic Fe³⁺/Fe²⁺ 경로로 upstream/downstream API를 배선한다.
