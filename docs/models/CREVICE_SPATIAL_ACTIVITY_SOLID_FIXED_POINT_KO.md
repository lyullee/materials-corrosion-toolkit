# 크리비스 셀별 활동도–고체 재고 연성 반복

## 목적과 모델 식별자

- 모델 ID: `chemistry.crevice_spatial_activity_solid_fixed_point`
- 입력 계약: `CreviceSpatialActivitySolidFixedPointRequest`
- 셀 계약: `CreviceCellActivitySolidInput`
- 계산 함수: `solve_crevice_spatial_activity_solid_fixed_point`
- 소스 ID: `caller_cell_aqueous_mass_action_and_solids`, `aqueous_solid_inventory_feedback_fixed_point`

이 모듈은 셀마다 사용자가 제공한 Davies 활동도·수용액 질량작용 시스템과 경쟁 고체 평형을 실제로 연속 계산한다. 수용액 상태를 계산하고 고체 용해/침전의 유한 재고 전이를 적용한 다음, 고체상으로 이동한 양만큼 수용액 선형 제약의 목표량을 갱신해 다시 수용액 평형을 푼다. 사용자가 지정한 셀 순서로 계산하며, 셀 간 물질 이동은 계산하지 않는다.

## 입력 자료와 단위

각 `cells[]` 항목에는 고유 `cell_id`, `AqueousDaviesIteration`, `CreviceCompetingSolidEquilibriumRequest`가 필요하다. 두 chemistry 계약은 온도, 종 집합, 전하, 원소 조성이 일치해야 한다. 수용액 종 입력은 activity iteration 계약에서 1 mol/L 기준 활동도 상태를 사용한다. 수용액 선형 제약의 농도 단위는 mol/L이며, 고체 평형 입력과 내부 고체 재고 및 종 농도는 mol/m³이다. 연결 시 단위 변환은 `1000 L/m³`로 명시 적용한다.

고체 평형 템플릿은 각 종의 활성도 기준 농도, 활동도 계수 및 원소식을 선언한다. 각 고체상은 수용액 반응물의 양의 화학양론 계수, 중성 고체 원소식, 무차원 용해도곱, 상수 레코드 ID·SHA-256 및 이를 고정하는 Evidence를 갖는다. Geometry 입력은 현재 `fixed_single_knot`만 지원하고 provider ID, revision, SHA-256을 요청 Evidence에 연결한다. 전체 chemistry 원자료와 공급자 계보는 하위 계약의 Evidence에 보존된다.

## 계산 순서

1. 셀의 caller 선언 리뷰, geometry digest, 종 집합, 온도, 전하 및 원소식을 검사한다.
2. 기존 Davies self-consistent solver를 실행해 각 셀의 질량작용/활동도 해를 구한다. Davies A, 물 질량 환산, 평형 상수와 수용액 질량 제약은 caller가 제공한다.
3. 계산된 mol/L 농도를 mol/m³로 바꾸고 결과 활동도 계수를 사용해 종 입력 digest와 Evidence를 다시 구성한다.
4. 기존 경쟁 고체 active-set solver로 caller 유한 상 목록의 평형 상태와 고체 재고를 계산한다.
5. 각 수용액 선형 제약 `bᵀc = T`에 대해 상 전이로 인한 농도 변화 `Δc = c_after_solid − c_before_solid`를 사용하여 다음 목표량을 `T_next = T + bᵀΔc / 1000`으로 조정한다. 이로써 침전은 용존 제약 재고를 줄이고 용해는 늘린다. 고체 재고도 같은 단계의 계산 결과로 넘긴다.
6. 제약량과 고체 재고를 선언된 damping 비율로 갱신한 후 다시 2단계부터 푼다. 연속 반복 간 수용액 농도, 고체 재고, 제약 목표량의 상대 잔차가 각각의 사용자 허용치 안에 들어와야 셀을 수락한다.

고체·종 입력을 갱신할 때 새 정규화 입력 digest를 계산하고, 이전 digest를 고정하던 Evidence 행을 새 digest로 바꾼다. 해당 Evidence 행이 없으면 계산을 거부한다. 상수 record digest와 나머지 공급자·표준상태 계보는 보존한다.

## 수렴과 부분 결과

`maximum_outer_iterations`가 소진되거나 하위 aqueous/solid solver가 실패하면 해당 셀은 수락하지 않는다. `cells × maximum_outer_iterations`가 `maximum_total_cell_iterations`를 넘는 요청은 계산 전 거부한다. 결과에는 이미 수렴한 앞쪽 셀의 `cell_results`, 실패 셀/반복 번호, 실패 하위 결과 및 반복별 입력·결과 SHA-256 계보를 남기며, 전체 `committed` 결과는 내지 않는다. 성공 결과에도 각 반복의 수렴 잔차, charge balance, active-set complementarity, 전체 입력 digest와 종·고체 농도가 기록된다. 기본 damping은 0.5이며 사용자 입력으로 바꿀 수 있다. 하위 고체 평형의 유한 반응 extent 계산에는 SciPy `brentq`가 필요하다.

## 보존식과 물리 범위

수용액 반응의 전하/원소 화학양론 검사와 caller 선형 제약, Davies solver charge gate는 하위 계산기에서 수행된다. 고체 반응은 전하 중성 및 원소 균형을 검사하고, 고체 solver가 종·상 extent balance 및 saturation complementarity를 확인한다. 이 외부 반복은 고체 전이에 따른 선형 제약 변화를 되돌리는 수치적 연성 알고리즘이다.

이 모듈은 다음을 추론하지 않는다.

- 실제 공정의 조성, 활동도/평형 상수, 반응망, 고체상 후보의 완전성 또는 kinetic parameter
- 셀 사이 확산·이동, 전기화학 반응 전류에 따른 species source, 혼합전위, 부식률
- 시간 적분, 가변 geometry, aperture 피드백 또는 침전 형상
- Gibbs 에너지 전역 안정성, 핵생성/준안정성 및 설비 건전성 판정

따라서 이는 시간·공간 reactive transport 또는 corrosion integrity 평가기를 대체하지 않는다. 셀 입력 chemistry는 별도의 공정자료 선별·상태 매핑이 필요하다.

## 구현 파일과 통합 메모

코어는 `src/matintegrity/crevice_spatial_activity_solid_fixed_point.py`에 있고 기본 `ModelRegistry` 및 생성 catalog/schema에 연결된다. 기존 spatial mass-action ledger나 variable-area transport와 연결할 때는 셀 ID·geometry digest·물리 범위가 동일한지 별도 adapter가 확인해야 한다.

## 저작권과 출처

모듈 설명과 계산 절차는 자체 기술 서술이며 외부 교재 문장을 재사용하지 않는다. 계산 입력의 근거 자료와 이용조건은 caller Evidence에 기록한다. 코드는 라이브러리 계약의 공개 입력·출력 동작을 호출하지만 그 자체로 외부 데이터의 이용 허가를 부여하지 않는다.
