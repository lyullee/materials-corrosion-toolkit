# hydrogen-physical-models 확장 요청

검토 기준 리비전은 `785dae74dad4771e76e2a8e8aad3731e3dfa799e`다. 이 리비전의 `h2physics.materials.TransportResult`는 운반체, 평판/구형 쉘 격자, 이동·포획 농도, 좌우 누적 좌표유량, 벽 재고와 보존잔차를 계산하지만 장기 저장 가능한 버전 JSON 계약은 내보내지 않는다. MatIntegrity 구현을 복사하지 말고 아래 송신 adapter를 해당 저장소에서 독립 구현한다.

송신기는 MatIntegrity가 공개한 `matintegrity.hydrogen_transport_history.v1` JSON Schema를 대상으로 한다. 공급자 ID와 정확한 Git revision, solver/result ID, native 직렬화 결과 SHA-256, material-condition/reference-lattice ID, atomic-H/H2 운반체와 몰질량, geometry, trap population ID, elapsed-time origin을 채운다. `DiffusionMesh`의 face position/area와 cell center/volume, `TransportResult`의 time, mobile, trapped, left/right integrated mol, wall inventory/residual, total residual과 선택 surface inventory를 원 배열 순서 그대로 내보낸다. 농도 수치 허용오차, 함수평가 수, 계수·경계 근거와 제한도 포함한다.

좌우 누적량은 현재 solver의 양의 좌표방향 부호를 유지한다. 이를 inward/outward 또는 검출기 전류로 이름만 바꾸지 않는다. atomic-H와 H2 mol, 면적당 양과 전체 mol을 암묵 변환하지 않는다. `native_solution` 객체는 JSON에 넣지 말고, 재현에 필요한 solver method·tolerance·maximum step·의존성 버전을 별도 native manifest에 기록해 그 bytes의 SHA-256을 제공한다.

공급자 쪽 인수시험은 평판·구형 쉘 각 1건, trap 0개·1개, 유한 표면재고 유무를 포함한다. Schema validation, JSON 왕복, digest 변조 음성대조, 배열 shape, 원 결과와 모든 수치 배열의 동등성, 원자/분자 운반체 보존을 확인한다. 한 저장소의 같은 방정식을 양쪽에서 실행한 비교는 독립 실험 검증으로 표시하지 않는다.

MatIntegrity 쪽에서는 `HydrogenTransportHistory.model_validate_json`으로만 수신한다. 수신 후에도 계수·재료상태·격자·표면·시계의 일치와 독립 실험 자격이 확보되기 전에는 파괴, 수명 또는 위험성 평가 입력으로 자동 승격하지 않는다.
