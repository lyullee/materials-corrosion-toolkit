# 단면적 변화 API

`fabrication.forming_area_reduction`은 같은 재료 구간의 원래 단면적과 변형 후 단면적을 m²로 받는다. 물리 시험편·재료 상태·단면 쌍의 식별자와 측정 근거를 함께 전달한다. 대응 관계를 검토하지 않은 요청은 `needs_data`다.

출력은 변형 후/원래 면적 비율, 부호를 유지한 단면 감소율과 백분율, 면적 비율의 로그다. 면적이 커지면 감소율은 음수다. 로그 면적 비율은 등가 소성변형률을 자동으로 뜻하지 않는다. 재료 경화, 미세조직 변화, 열처리 필요성, 규격 허용 판정은 이 산술 API의 출력이 아니다.

`FormingAreaReduction`은 `matintegrity.models.materials`에서 가져올 수 있다. `default_registry().run`과 `run_json` 모두 같은 모델 ID를 사용한다. 입력 계약은 `docs/schemas/FormingAreaReduction.json`에 있고, 모델 참조 문서에는 출력 단위가 수록된다. 범위를 벗어난 비율이나 백분율은 비유한 값을 내보내는 대신 `out_of_scope`로 반환한다.

검증은 면적의 공통 배율 1e-200·1·1e200, 면적 증가, 검토 누락, 표현 범위 초과, Python/JSON 동일성으로 구성한다. 성형 지지영역 API 1.0.1은 같은 재료·공정 식별자에 여러 지지영역이 일치하면 첫 항목을 선택하지 않고 `needs_data`를 반환한다. 호출자는 하나의 검토된 영역을 선택해 다시 요청한다.
