# 성적서 문서의 제품·추적번호 연결

`materials.certificate_reconciliation` 모델 버전 1.1.0은 성적서 문서 묶음의 대상 제품과 추적번호를 명시적으로 확인한다. 하위 정량 결과의 heat·lot·재료 상태와 상위 문서의 제품 범위는 서로 다른 식별 수준이다.

새 입력은 `expected_product_id`, `expected_traceability_id`, `product_and_traceability_binding_reviewed`다. 두 ID는 함께 지정해야 하며 모든 coverage 기록의 product/traceability 값과 정확히 일치해야 한다. 식별자가 다른 문서를 섞으면 입력을 거부한다. 실행 asset/location도 평가 입력과 다르면 거부한다.

이전 형태의 입력은 새 필드 없이 파싱할 수 있으나 `needs_data`와 `insufficient_evidence`를 반환한다. 유효 결과를 얻으려면 실제 대상 제품·추적번호를 확인하고 두 ID와 검토 상태를 명시해야 한다. 기록의 첫 행에서 자동으로 대상 ID를 선택하지 않는다.

기존 사용자 기준, 화학·기계적 특성 비교, 불확실성 구간, 문서 누락 및 모순 처리 기능은 유지한다. PMI나 추가 시험을 성적서 원본 또는 완전한 제품 추적성의 대체물로 승격하지 않는다. 출력은 제공된 사용자 기준에 대한 확인이며 규격 합격이나 재료 승인 자체가 아니다.
