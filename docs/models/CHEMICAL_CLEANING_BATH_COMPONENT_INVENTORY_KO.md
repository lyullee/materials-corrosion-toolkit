# 화학 세정액 성분 재고 계산

## 목적

`fabrication.chemical_cleaning_bath_component_inventory`는 세정조의 액체 부피와 성분별 질량을 이산 작업 순서로 추적한다. 액 추가, 성분 보충, 완전혼합 액 배출, 사용자가 별도로 산정한 성분 소비량을 반영해 각 단계와 마지막 시점의 농도를 계산한다. 세정 배치 기록을 재고 수지와 연결하거나, 자체 공정 데이터로 반복 계산할 때 사용할 수 있다.

이 기능은 세정 성능이나 재료 적합성을 판정하지 않는다. 기존 `fabrication.chemical_cleaning_envelope`의 조건 범위 비교 및 production-campaign evidence API와도 목적이 다르다.

## Python API

모듈: `matintegrity.models.chemical_cleaning_bath_inventory`

- 입력: `ChemicalCleaningBathHistory`
- 작업 단위: `ChemicalCleaningBathEvent`
- 질량 항목: `BathComponentMass`
- 계산: `chemical_cleaning_bath_component_inventory(history)`
- 모델 ID: `fabrication.chemical_cleaning_bath_component_inventory`

입력 질량은 kg, 액체 부피는 m³, 시간은 caller가 고정한 시계 기준의 초로 전달한다. 농도는 `kg/m^3`로 반환한다. 계산 결과는 공통 `Calculation` 계약을 따른다.

### 이벤트 의미와 순서

각 이벤트의 순서는 아래와 같이 고정한다.

1. 액체 부피와 용해 성분 질량 추가
2. 현재 균일 혼합 조성에 비례한 액체 배출 및 동반 성분 제거
3. caller가 제공한 성분별 소비량 차감

따라서 배출량이 `V_out`, 배출 직전 액량이 `V_before`라면 해당 배출로 제거되는 각 성분 질량은 `m_removed = m_before × V_out / V_before`이다. 이벤트가 끝난 뒤 용액 농도는 잔류 성분 질량을 잔류 액량으로 나눈 값이다. 이는 잘 섞인 단일 용기 재고수지이며, 시간 간격 내의 반응속도 모델은 아니다.

이벤트마다 고유 ID, 순번, 시각, 근거 `Evidence`가 필요하다. 성분 ID·이벤트 순서·액량 기준·소비 항은 caller가 검토했는지 명시한다. 초기 성분 목록은 계산 기간 내 사용할 수 있는 성분 ID의 기준 집합이며, 미선언 ID를 이벤트에서 새로 도입할 수 없다.

## 예시 골격

```python
from matintegrity.models.chemical_cleaning_bath_inventory import (
    BathComponentMass,
    ChemicalCleaningBathEvent,
    ChemicalCleaningBathHistory,
    chemical_cleaning_bath_component_inventory,
)
from matintegrity.contracts import Evidence

evidence = Evidence(
    source_id="plant-bath-record",
    origin="user_declared",
    citation="Caller-controlled batch record revision 3",
    sha256="a" * 64,
)

history = ChemicalCleaningBathHistory(
    history_id="bath-run-001",
    asset_id="asset-01",
    location_id="cleaning-loop-01",
    clock_id="utc-seconds-from-run-start",
    initial_liquid_volume_m3=0.5,
    initial_components=(BathComponentMass(component_id="acid-A", mass_kg=10.0),),
    initial_evidence=(evidence,),
    events=(
        ChemicalCleaningBathEvent(
            event_id="makeup-1",
            sequence_position=1,
            time_s=60.0,
            added_liquid_volume_m3=0.1,
            added_components=(BathComponentMass(component_id="acid-A", mass_kg=1.0),),
            evidence=(evidence,),
        ),
    ),
    component_identity_reviewed=True,
    event_order_and_volume_basis_reviewed=True,
    consumption_terms_reviewed=True,
)

result = chemical_cleaning_bath_component_inventory(history)
```

예시의 값은 API 사용법을 설명하기 위한 임의 값이며 특정 약품이나 설비에 대한 권고값이 아니다. 실행 가능한 검증 예제 또는 실험 데이터로 취급하지 않는다.

## 자료 근거와 사용 조건

새 외부 데이터, handbook 문장, 산업 표준 허용치 또는 약품별 상수를 내장하지 않았다. 계산은 입력으로 받은 재고를 보존하는 산술 수지이며 근거는 `caller_declared_well_mixed_solution_component_inventory_balance`로 표시한다. 실제 적용 전 사용자는 각 batch 성분의 정의·단위 변환·분석 결과·액량 보정·소비량 산출법을 자체 원자료와 Evidence로 연결해야 한다.

## 반환 및 실패 처리

- 입력 검증은 음수 재고, 잘못된 이벤트 순서, 중복 ID, 알려지지 않은 성분 ID를 거부한다.
- 배출 요구량이 남은 액량을 넘거나 성분 소비량이 가용 재고보다 크면 `needs_data`를 반환하고 해당 이벤트 ID와 부족 정보를 기록한다. 실패 뒤의 이벤트는 계산하지 않는다.
- 액량이 0인데 양의 성분 질량이 남으면 용액 농도를 계산하지 않고 `needs_data`를 반환한다.
- 검토 플래그가 빠져도 계산은 보류되고 누락된 검토 항목을 돌려준다.

## 적용 가정과 한계

- 용기는 단일 구획이며 농도와 액량이 공간적으로 균일하다.
- 배출 직전 조성으로 배출 성분량을 결정한다.
- 추가 성분은 단일 성분 ID의 질량으로 표현되며 모든 질량은 일관된 화학종·등가 기준을 사용한다.
- 온도·밀도·부피 수축, 휘발, 증발, 가스 용해, 침전·재용해, 상분리, 벽면 부착, 누설, 반응속도, pH 및 세정 성능은 계산하지 않는다.
- `caller_supplied_component_consumption`은 외부 데이터 또는 별도 모델이 제공하는 순 소비량이다. 이를 자동으로 금속 용해나 세정 반응으로 해석하지 않는다.
- 결과는 재고 추적일 뿐 운전 절차 승인, 재료 호환성, 폐액 분류, 배출 허용, 건전성 또는 안전 판정이 아니다.

## 확장 연결

이 계산은 공통 `Calculation`/`Contract` 형식으로 결과를 내며 registry의 `ModelSpec`을 제공한다. 후속 연결은 batch 분석 adapter가 검토된 성분 질량과 Evidence를 구성하고, caller 지정 반응/유출 모델이 단계별 소비 및 손실 항을 제공하도록 분리할 수 있다. 물성 기반 부피 변화나 다구획 혼합을 추가하려면 상태식·전달 항·독립 검증 자료를 별도 모델로 정의해야 한다.

이 API에는 기능 테스트, 수치 검증, 사례 계산, 패키지 빌드가 수행되지 않았다. 공개 사용 전 모델 입력, 단위 기준, 질량 보존과 실패 경로를 별도 검증해야 한다.
