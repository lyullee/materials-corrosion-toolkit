# 크리비스 셀별 고체 후보 포화도 연결

## 목적

이 adapter는 계산된 크리비스 transport knot의 각 셀을 별도 액상 구획으로 유지하고, 셀에 연결된 mass-action activity 결과에 대해 caller가 제공한 고체 후보의 포화 지수를 계산한다. 기존 aqueous saturation screen의 계산 규칙을 재사용하며 셀별 근거·digest lineage를 결과에 남긴다.

이 기능은 후보 고체가 과포화 조건에 가까운지 비교하는 **screening**이다. 고체를 선택하거나 석출시키는 phase-equilibrium solver는 아니다.

## API와 입력

Python 모듈: `matintegrity.crevice_local_solid_saturation`

- 입력 계약: `CreviceLocalSolidSaturationRequest`
- 평가기: `evaluate_crevice_local_solid_saturation(request)`
- ModelSpec: `specifications()`
- 모델 ID: `integration.crevice_local_solid_saturation`
- source ID: `caller_crevice_cell_local_candidate_saturation_screen`

입력은 기존 `CreviceLocalSpeciationLedgerRequest`와 해당 계산 결과 전체, 결과의 canonical SHA-256, 선택 knot 인덱스, 후보 solid 정의, 용해도 데이터 provider/digest, Evidence 및 review gate다. 선택한 knot의 각 셀은 기존 계약처럼 다음 세 lineage 값에 묶인다: transport cell context digest, mass-action 입력 digest, mass-action 결과 digest.

후보는 기존 `CandidateSolid` 형식을 사용한다. 각 상은 차원 없는 용해도곱 및 활동도곱 stoichiometric terms를 caller가 제공하며 solubility Evidence source ID를 함께 제공해야 한다. 하나의 용해도 자료 묶음을 선택 knot의 모든 셀에 적용하므로 모든 셀에서 온도와 활동도 표준상태가 같아야 한다. 온도별 상수는 caller가 해당 온도에 적용 가능한 값으로 제공하고 검토한다. 이 API는 보간하지 않는다.

한 호출은 최대 200개 셀, 최대 100개 후보 상을 처리한다. 하나의 knot만 평가하므로 시간 축 보간이나 knot 사이의 화학 동역학은 포함하지 않는다. 전체 시간 이력을 만들려면 각 knot를 정확히 선택해 별도 요청을 구성하고 결과 순서를 caller가 관리해야 한다.

## 결과

성공 결과는 셀별로 다음을 반환한다.

- transport cell context SHA-256
- local mass-action 결과 SHA-256
- 용액 ID와 온도
- 후보별 기존 saturation screen 결과: `log10_saturation_ratio`, caller 경계가 있으면 결정론적 상·하한과 포화 구간 분류
- cell saturation result SHA-256

입력 result digest, knot 인덱스/시각/geometry side, upstream ledger의 셀 수·순서가 맞지 않으면 계산하지 않는다. 첫 불완전 셀 이전 결과는 `completed_cells`에 prefix로 남고 실패 셀을 명시한다. review가 빠지면 `needs_data`를 반환한다.

## 제한

각 셀의 local speciation은 upstream에서 따로 계산되어야 한다. 이 adapter는 셀을 섞지 않고, cell 간 평형이나 상 확산도 가정하지 않는다. 포화지수는 후보 평가일 뿐이며 phase selection, 침전 또는 용해량, 핵생성 지연, 반응속도, 고체 재고, 몰부피/간극 변화, 보호성, 부식률, 위험도·합격 판단을 산출하지 않는다. Ksp, 활동도 표준상태, 후보 상 및 source 사용권한의 타당성은 caller 책임이다.
