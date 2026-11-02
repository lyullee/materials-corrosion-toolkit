# Neuber 기반 노치 뿌리 변형률 진폭

`fatigue.neuber_notch_strain_amplitude`는 호출자가 검토한 명목 단축 응력 진폭, 탄성 응력집중계수, 탄성계수 및 안정화 반복 Ramberg–Osgood 계수로 국부 응력·변형률 진폭을 푼다. 양의 구간에서 Neuber 곱과 반복 구성식의 교점을 이분법으로 찾으며, provenance와 입력 digest는 공통 registry 계약이 제공한다.

노치 입력과 보정된 strain-life 계수를 한 번에 평가하려면 `fatigue.neuber_strain_life_chain`을 사용한다. 이 모델은 Neuber 단계가 `computed`이고 수렴했을 때만 국부 변형률 진폭을 기존 `fatigue.strain_life` 식에 전달한다. 양쪽 상태, Neuber 잔차 및 반복수, 최종 수명 또는 보정주기 범위 밖 상태를 하나의 digest-bound registry 결과로 묶는다.

독립 Neuber 계산은 core dependency만 사용한다. 연결 모델의 strain-life 단계는 기존 모델과 같이 SciPy가 필요하므로 `pip install 'matintegrity[science]'` 환경에서 실행한다.

## 입력 사용

최소 입력은 `examples/model_inputs.json`의 모델 예제를 참고한다. `all_inputs_reviewed`는 geometry·load basis·property와 적용범위를 외부에서 확인했음을 뜻한다. 검토가 끝나지 않았으면 결과는 `needs_data`다. 탄성 응력집중계수는 geometry solver가 산출하지 않으므로 근거와 함께 호출자가 공급해야 한다. 단독 모델 결과의 `local_strain_amplitude`는 `fatigue.strain_life.strain_amplitude` 입력으로 사용할 수 있다. 자동 연계를 원하면 `fatigue.neuber_strain_life_chain`이 두 단계를 순서대로 실행한다.

## 적용 범위와 한계

모델은 단일 축, 안정화 반복응답, 하나의 cyclic Ramberg–Osgood 법칙에 한정된다. 다축 상호작용, 평균응력, 잔류응력, 비대칭 이력, ratcheting, 비 Masing 응답, notch-gradient/critical-distance, crack initiation 보정, 수명, 규격 적합 판정은 제공하지 않는다. `converged`와 Neuber 잔차는 수치 해법 상태만 나타내며 입력 물성·형상 계수의 자격화나 현장 검증을 의미하지 않는다. 반복 한도 안에 수렴하지 못하면 `out_of_scope`를 반환하므로 해당 진폭을 후속 strain-life 계산에 사용하면 안 된다.

## 검증 계획

`tests/test_neuber_notch_strain_amplitude.py`는 Neuber 곱 잔차, 선형 탄성 극한, 사용자 검토 게이트, 반복 한도 초과 시 계산 보류 및 strain-life 단계와의 registry 연결을 검사하도록 작성했다. 로컬 테스트는 실행하지 않았다. 해당 테스트와 전체 example registry 일치 검사는 누리온 manifest batch50에 등록되어 있지만 새 작업은 별도 사용자 지시 전에는 제출하지 않는다.
