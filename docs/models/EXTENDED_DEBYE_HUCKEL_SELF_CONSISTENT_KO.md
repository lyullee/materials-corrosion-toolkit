# Extended Debye–Hückel 자기일관 수용액 speciation

`chemistry.aqueous_extended_debye_huckel_self_consistent_speciation`는 사용자가 정의한 수용액 mass-action 평형/선형 제약을 기존 계산기에 반복 적용하면서, 용액 조성에서 얻은 이온강도에 따라 활동도계수를 갱신한다.

## 계산

각 반복의 종별 molality로부터 이온강도 `I = 1/2 Σ mᵢ zᵢ²`를 계산하고, 전하가 있는 종에 대해 caller가 제공한 온도·용매별 A, B와 종별 이온 크기 `aᵢ`를 사용한다.

`log10(γᵢ) = -A zᵢ² √I / (1 + B aᵢ √I)`

이 식의 B는 `sqrt(kg/mol)/nm`, `aᵢ`는 nm, I는 mol/kg 단위로 입력한다. 따라서 `B aᵢ √I`는 무차원이다.

물 1 kg당 molality 표준상태를 mass-action 입력의 molarity 1 mol/L 표준상태에 연결할 때 caller가 검토한 물 질량/용액 부피 `w`를 사용해 `γc = γm / w`로 변환한다. 양의 활동도계수 로그 공간에서 caller가 정한 감쇠율로 반복하며 지정 잔차 내에서만 수렴 결과를 반환한다.

## 데이터와 적용 조건

A/B 계수, parameter provider revision·configuration·record digest, 각 종의 이온 크기와 Evidence, 전체 종 인벤토리, 반응/평형식, 전하수지 허용치, 수온·용매 적용조건은 모두 입력자가 공급한다. 계수표나 외부 thermodynamic database 값을 포함하지 않는다. 이온 크기는 같은 순서의 질량작용 종 각각에 연결해야 한다. 모델은 질량작용이 molarity 1 mol/L 활동도 표준상태를 사용하고, 단일 액상·침전 없음 조건이 검토된 경우만 지원한다.

이온강도가 사용자가 선언한 지지 범위를 넘거나 charge closure, 내부 평형 solver 또는 외부 활동도 fixed point가 실패하면 결과를 수렴 speciation으로 제시하지 않는다. 종/반응 자동 생성, 고체상 탐색, 속도론, 혼합 용매 일반화, 부식률, 재료 qualification은 계산하지 않는다. 이온별 활동도계수는 단일 이온 근사이므로 절대 활동도는 convention과 parameter basis에 의존한다.

같은 request에서 `build_extended_debye_huckel_transport_activity_callback()`을 만들 수 있다. 이 helper는 caller가 준 species-by-location 농도 행렬에서 각 위치의 몰랄 이온강도와 gamma만 산출하고, 정확한 종 순서·온도·parameter support·전하/재고 review를 요구한다. restricted transport의 flux나 local speciation solver를 수행하지 않으며, 계산 범위 밖 composition은 거절한다.

## 출처와 독립 구현

수식 형태는 USGS PHREEQC 공개 기술문서의 extended Debye–Hückel 설명을 근거로 삼는다. 본 모듈은 독립적으로 작성한 코드이며 문장·parameter table·상수 자료를 복제하지 않는다. 구현에는 공식을 일반형으로 사용하고 모든 계수와 크기값은 사용자가 출처·권리·표준상태를 확인한 뒤 Evidence와 함께 제공한다. 구현과 적용범위에 대한 수치·실험 검증은 별도 절차가 필요하다.
