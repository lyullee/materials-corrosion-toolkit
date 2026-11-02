# 확장 요청: 부식 전기화학 계산 결과와 기존 FTA 모듈 연결

## 목적

현재 MatIntegrity 계산 결과를 계정 내 기존 위험도/FTA 모듈에서 재현 가능하게 소비할 수 있도록 얇은 어댑터를 추가한다. 이 요청은 부식률·전류·재료 손실을 고장확률로 직접 변환하지 않는다. 물리 계산 결과와 위험분석 기본사건의 확률 모델을 분리한다.

## 사용할 수 있는 MatIntegrity 경계

- `integration.crevice_current_carrying_np_faradaic`: 공간 Nernst–Planck 전류, Faradaic branch, 종·전하·원소 수지 및 수렴 상태를 가진 Crevice 계산.
- `integration.crevice_faradaic_spatial_chemistry_coupling`: endpoint chemistry와 Faradaic extent를 연결하는 제한 경로. 비영 전해질 면전류는 지원하지 않는다.
- `adapter.corrosion_rate_history_to_fault_tree_basic_event`: 기존 FTA 기본사건 계약에 digest-bound 감육 조건을 전달하는 경계.
- `reliability.fault_tree_minimal_cut_sets`: caller가 제공한 기본사건 확률 및 독립성 가정으로 FTA를 계산하는 경계.

## 타 저장소에서 구현할 내용

1. FTA 기본사건 입력에 MatIntegrity의 `model_id`, 모델 버전, request/result digest, 물리 자산·위치·시간 범위, 계산 단위, 수렴·수지 상태를 보존하는 provider adapter를 추가한다.
2. 계산 실패, 미수렴, 수지 불일치 결과는 확률 입력으로 변환하지 않고 명시적 거부 상태로 반환한다.
3. 고장 한계값, 초과 확률 또는 조건부 확률은 별도 caller 소유 모델로 받는다. 임계값·분포·의존성·공통원인 가정을 MatIntegrity 결과에서 추론하지 않는다.
4. 각 기본사건의 FTA 확률은 검토된 보정/신뢰성 모델에서 산출하고, 원 모델 입력 digest와 사건 의미를 FTA 결과까지 연결한다.
5. FTA 공통 자산·관측 기간·사건 범위·독립성 가정을 검토하고, 상관된 손상 메커니즘을 독립 사건으로 중복 계수하지 않는다.

## 인터페이스 요구사항

- 단위는 SI로 명시하고, 결과의 `status`, qualification, assumptions, evidence 및 계산 범위를 손실 없이 전달한다.
- FTA 모듈의 자체 schema/version 정책에 맞춘 별도 adapter를 둔다. MatIntegrity 내부 계약을 외부 모듈의 저장 형식으로 강제하지 않는다.
- request/result digest가 바뀌거나 asset/location/time scope가 다르면 기존 위험사건과 자동 결합하지 않는다.
- 원 계산 provenance를 보존한 JSON 교환 예시와 실패 예시를 제공한다.

## 산출물 및 검증 계획

- 대상 FTA 저장소의 버전 고정, adapter, schema, 사용 예시 및 설치 선택사항.
- 정상 계산, 미수렴, digest 불일치, 단위 불일치, 사건 기간 불일치, 확률 공급자 누락 사례.
- 결정론적 감육 결과를 확률로 오해하지 않는지, 실패 상태가 확률 계산으로 새지 않는지에 대한 계약 검증.
- 실제 위험도 검증은 FTA 입력 확률·의존성·고장 기준을 제공하는 별도 qualified source가 확보된 뒤 수행한다.

## 현재 경계

MatIntegrity가 제공하는 감육 또는 Faradaic 결과는 상태·물질량 계산이지 failure probability가 아니다. FTA 확률, consequence, acceptance 기준과 공통원인/의존성 모델은 호출 시스템에서 책임지고 제공해야 한다. 실제 기존 GitHub 저장소에 적용하기 전에는 해당 저장소의 현재 schema와 라이선스를 확인하고 별도 확장 작업으로 수행한다.
