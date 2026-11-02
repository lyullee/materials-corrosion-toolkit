# Crevice aperture history와 transport의 순차 결합

`solve_crevice_geometry_transport_campaign()`은 `planar_slit_aperture_history()`가 만든 digest-pinned geometry 이력과 `solve_restricted_transport()`를 시간 구간별로 연결한다. geometry 상태 clock은 transport의 전역 출력 clock에 정확히 포함되어야 하며, transport 기준 단면적·cell 수·길이는 geometry source와 일치해야 한다.

각 구간은 왼쪽 geometry knot의 단면적과 벽 면적/부피비를 고정해 transport를 계산한다. 반응·활동도·벽/팁 flux·시간변화 advection callback에는 구간 시작시각을 더한 전역 campaign time을 전달한다. 구간 끝에서 다음 geometry의 cell volume으로 농도를 재매핑하여 각 cell별 종 inventory를 보존한다. 결과는 transport segment별 계산과 각 aperture 변화 경계의 사전/사후 농도 및 보존 잔차를 반환하고, mouth/tip/homogeneous/wall 원장을 합쳐 전체 inventory balance를 다시 확인한다. 전체 잔차가 허용오차를 넘으면 캠페인을 `out_of_scope`로 낮춘다. 구간 계산 실패 때는 성공 prefix와 실패 segment를 분리해 기록한다.

필수 review 항목은 geometry/transport clock 정합, 구간 내 고정 geometry의 operator-split 해석, 순간 cell inventory remap, callback 전역시간 해석이다. 시간경계가 transport output clock에 없으면 보간하거나 조용히 정렬하지 않고 거절한다.

## 적용 범위

이 API는 caller가 제공한 recession/aperture history를 transport history에 적용하는 **one-way operator split**이다. transport에서 금속 용해 flux를 새로 유도해 aperture history를 업데이트하지 않는다. 구간 안 moving boundary, 연속 유동·기하 동시해석, 운동량/연속 방정식, 동시 다상/침전 chemistry, 물성/kinetics calibration은 계산하지 않는다. Geometry update 직후 농도는 부피 변화만큼 순간 조정되며, 빠른 혼합·흡착/탈착 또는 미해상 경계과도는 모사하지 않는다.

`geometry_history_sha256`은 `canonical_digest(geometry_history)`로 만들어 전달한다. geometry와 물성은 별도 caller provider가 준 검토 자료여야 하며, 출력은 모델 검증이나 부식 합격 판단이 아니다.

각 interval callback wrapper는 원래 callback의 `provider_id`, `provider_revision`, configuration digest, network/species 순서 및 activity-provider 메타데이터를 유지한다. wrapper에는 해당 segment의 `global_time_offset_s`를 붙여 어떤 전역시각으로 local solver 시간을 옮겼는지 식별한다. 이 메타데이터 전달은 callback 실행을 둘러싼 정보 보존이며 callback 내용이나 수치 모델을 검증하지 않는다.

각 계산 segment에는 callback 역할별 lineage map도 반환한다. Provider identity/revision, configuration digest, 반응망·종 순서와 activity-provider metadata를 복사하고 campaign 전역시각 offset을 포함한다. 각 map은 canonical SHA-256으로 고정되어 segment replay나 외부 소비자가 입력 함수의 선언 identity/time mapping을 대조할 수 있다. Metadata 없는 caller callback은 비어 있는 identity로 기록되며, 결과가 callback 구현 자체를 검증하지는 않는다.
실패한 segment도 시도한 callback lineage를 별도 필드로 보존한다. 이 경우 geometry/clock mismatch, provider 오류 또는 transport solver 실패와 함께 어느 시간 offset에서 어떤 선언 callback 조합을 실행하려 했는지 확인할 수 있다.
