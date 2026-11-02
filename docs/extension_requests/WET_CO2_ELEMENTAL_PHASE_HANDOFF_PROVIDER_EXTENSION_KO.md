# 확장 요청: wet-CO₂ 원소 재고 handoff provider 연결

## 목적

`models.wet_co2_elemental_phase_handoff`의 고정된 provider-neutral 계약을 기존 wet-CO₂ calculation graph에 노출하고, upstream phase/transport output과 downstream corrosion / risk module 사이에 명시적인 원소 재고 전달 경로를 만든다.

## 요청 범위

1. provider plugin이 직접 사용할 API convenience constructor를 추가한다. Core request는 이제 optional upstream `AssessmentResult` plus result digest를 받으며, 제공되면 state/context/input digest, values payload digest, asset/location/time basis를 검증한다. Extension helper는 이 complete lineage bundle을 표준화한다.
2. provider별 공개 parser/fixture를 연결하고 provider revision에 따라 `species_ids`, `solid_species_ids`, 배열 축 순서 및 source clock adapter를 고정한다. 새 축 규약은 버전 있는 parser로 연결한다.
3. 원소식과 cell volume을 Evidence-backed public data source 또는 material/chemistry provider에서 조회하는 선택 plugin을 추가한다. 자동 화학종 추론이나 값 보간은 하지 않는다.
4. 상별 inventory를 material loss, scale inventory 및 FTA/risk API에 넘기는 digest-bound adapter를 구현한다. boundary flux·gas·adsorbed pools는 각각 명시 입력으로 둔다.
5. 질량수지는 합성 handoff 결과가 아니라 독립 계산 provider와 외부 boundary flux를 포함한 검증 fixture로 확인한다.

## 기대 산출물

- 카탈로그 설명 및 JSON Schema
- provider별 얇은 mapping adapter와 입출력 예시
- digest 변경, ID 누락/중복, 단위·축 불일치, incomplete pool을 보여주는 검증 사례
- provider extension 이후에 실행하는 수치 검증과 질량수지 비교 기록

현재 구현은 합성된 산술 receipt만 만들며 열화학 데이터, 용해 속도, scale kinetics 또는 안전 판정을 제공하지 않는다.
