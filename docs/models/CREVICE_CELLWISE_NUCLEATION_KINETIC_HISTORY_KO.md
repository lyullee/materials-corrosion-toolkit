# 크리비스 셀별 핵생성·성장 kinetic ledger adapter

## 목적과 계산 경계

`integration.crevice_cellwise_nucleation_kinetic_history`는 하나의 고정 형상 mesh에 있는 셀별 closed-batch 핵생성 이력을 같은 ordered clock에 맞춰 계산하고, 각 셀의 결과를 amount 단위로 합산한다. 각 셀 계산은 기존 `chemistry.crevice_nucleation_kinetic_history`를 호출하므로 seed inventory event는 일정한 caller molar source에 대해 해석식으로 분할되고, 보수 ledger가 실제 임계 통과를 확인한다.

이 adapter는 spatial transport 계산이 아니다. 셀 사이 NP flux, 대류, 전류, wall flux 또는 공통 reservoir는 셀 ledger에 들어가지 않는다. 따라서 셀 간 물질 교환이 중요하다면 caller가 별도의 transport step과 이 adapter를 명시적으로 operator-split 해야 한다. 반환된 셀 합계는 장부용 공간 합이며 그 자체가 transport 수지를 닫는다는 뜻은 아니다.

## 입력과 정렬 규약

각 `FixedKineticCell`은 고유 cell ID, 길이, 단면적, 액체 부피 및 고정 geometry digest/Evidence를 담는다. 액체 부피는 `cell_length_m * cross_section_area_m2`와 일치해야 한다. 중첩된 kinetic request는 해당 셀의 초기 수용액·고체 재고와 exact saturation intervals를 제공한다.

모든 셀은 동일한 physical scope, clock, isothermal temperature, 수용종/고체 반응 identity와 순서, provider/configuration/parameter digest, nucleation/growth law 및 exact interval 경계를 공유해야 한다. Saturation 값은 셀마다 달라질 수 있지만 각 셀 record의 digest/Evidence를 독립적으로 유지한다. 전체 ordered cell geometry 및 typed subrequest digest는 `cell_order_sha256`와 Evidence에 묶인다.

## 계산과 commit

셀별 batch history solver가 각 interval의 nucleation source와 seeded growth/dissolution law를 기존 conservative competition ledger에 넘긴다. 임계 event 예상 시 inventory deficit/source rate로 event time을 산출하고, 해당 substep의 보수 ledger가 threshold 도달을 확인해야만 commit한다. 공통 용존 반응물 제한으로 도달하지 못하면 해당 cell 계산은 성공으로 처리하지 않는다.

모든 셀 결과가 성공해야만 spatial adapter가 최종 result를 commit한다. 농도와 고체상 몰농도에 고정 액체 부피를 곱해 species/phase amount 이력을 만들고 셀 전체 amount를 시간별로 합산한다. 셀 하나라도 실패하면 결과는 `committed=false`이며 부분 셀 계산을 집계 결과로 내보내지 않는다.

## 제한과 확장 방향

- 체적, 면적, 온도, 반응망, activity/saturation 입력은 caller가 제공한다. 자동 상·종 발견은 없다.
- geometry는 전체 계산 구간에 고정이다. 석출로 인한 aperture, porosity, wall area 또는 diffusivity 변화는 반영하지 않는다.
- interval saturation은 고정된 caller 값이며 nucleation source는 해당 구간에서 상수로 본다.
- transport와 precipitation은 동시 연성되지 않는다. 현재 API는 셀 간 flux를 적용하는 solver나 moving-boundary RHS로 대체할 수 없다.
- 물리 검증, kinetics 적용성 및 사용권은 caller 책임이며 material qualification, corrosion rate, life, risk 또는 probability를 추론하지 않는다.

다음 transport 연동에서는 같은 inserted event clock에서 boundary/velocity/property histories를 재구성하고, 매 substep 이후 aqueous/solid 재고를 수송 초기 상태로 이어가는 별도 계약과 검증 자료가 필요하다.

## API

- Request: `CreviceCellwiseNucleationKineticHistoryRequest`
- Cell record: `FixedKineticCell`
- Evaluator: `evaluate_crevice_cellwise_nucleation_kinetic_history`
- Model ID: `integration.crevice_cellwise_nucleation_kinetic_history`
