# 온도 보정 변형률속도와 크리프 설계 범위

## 계산 API

`creep.zener_hollomon_parameter`는 `ZenerHollomonParameter`를 받는다. 입력은 재료 상태·변형률속도 정의·활성화에너지 근거의 식별자, 양의 변형률속도 `strain_rate_s_1`, 절대온도 `temperature_K`, 비음의 활성화에너지 `activation_energy_J_mol`, 양의 기체상수 `gas_constant_J_mol_K`다. 계수 기본값은 없으며 전체 입력과 권한·적용성 검토를 `CorrelationBasis` 해시로 연결한다.

계산은 `ln(Z / (1/s)) = ln(strain_rate / (1/s)) + Q/(R*T)`를 사용한다. 이 정의는 [Kawulok 등의 공개 연구, Materials 15(2), 595 (2022), 식 4](https://pmc.ncbi.nlm.nih.gov/articles/PMC8780613/)에서 독립적으로 확인했다. 논문의 재료 계수·표·도표·문장은 포함하지 않았다.

`temperature_compensation_exponent`, `ln_z_relative_to_1_s_1`, `z_s_1`, `z_representable`과 입력 근거 식별자를 반환한다. 분모 곱셈이 먼저 넘치는 문제를 피하도록 지수 비율을 유리수로 조합한다. 지수 자체의 오버플로 또는 비영 지수의 언더플로는 `out_of_scope`다. 로그값은 유효하지만 직접 지수값이 표현되지 않으면 `computed`, `z_s_1=null`, `z_representable=false`다. Q가 0이면 공급된 속도를 그대로 보존한다.

Python에서는 `default_registry().run(model_id, request, context)`, JSON에서는 `run_json(model_id, request.model_dump_json(), context)`를 사용한다. 음의 부호를 가진 축방향 압축 속도를 절댓값으로 자동 변환하지 않는다. 어떤 양의 속도 정의가 물리적으로 적합한지는 호출자가 검토해야 한다.

## 지원 경계와 남은 과제

이 API는 속도를 예측하지 않고 공급된 속도를 보정한다. 유동응력, 재결정, 크리프 손상, 파단 시간 또는 수명 확률을 생성하지 않는다. Norton·Larson–Miller·시간 분율·크리프–피로 API가 있다는 사실도 Omega 방식의 다축 손상 계산이나 열이력에 따른 뜨임 모델 구현을 뜻하지 않는다. 해당 방법의 구체화·구현과 규격별 용접강도·압축 설계 조건 연결은 남은 과제다. 일정 하중과 일정 변형률의 응답, 연속 운전과 반복 온도 노출을 구분해야 한다.

## 검증 기록

자체 작성한 수치 사례로 지수 10의 해, 활성화에너지 0, 직접 값 오버플로에서 로그 보존, 분모 중간 곱셈 오버플로 회피, 지수 표현 범위 이탈, 잘못된 물리 입력, 입력 해시 변경과 레지스트리 Python/JSON 결과 일치를 확인했다. 관련 11개 테스트와 정적 검사가 통과했다. 실험 데이터로 활성화에너지를 보정하거나 독립 물리 검증을 수행한 결과는 아니다.
