# WCO2 종 전달 장부 검사

`integration.wco2_species_transfer_audit`는 화학·수용액 speciation·수송 단계 사이에서 호출자가 선언한 종 대응이 형식식과 전하를 보존하는지 확인한다. 기존 chemistry-boundary audit의 결과 digest, clock, solvent, standard-state와 stage state continuity 검사는 그대로 별도로 수행해야 한다. 이 API는 종별 식과 이동 관계의 화학량론 장부 검토를 보완한다.

## 입력 계약

- upstream/downstream 각 stage에 caller가 고른 종 ID, 형식 전하, 원소별 정수 개수를 선언한다.
- identity/renamed 규칙은 한 종에서 한 종으로 계수 1:1 전달만 허용하며, 형식식과 전하가 같아야 한다.
- reaction_transformed 규칙은 caller stoichiometry로 양쪽 종 묶음을 선언한다. 각 규칙에서 원소와 전하 합이 같아야 한다.
- 모든 upstream 종은 하나 이상의 이동 규칙에 등장하거나, Evidence 및 사유가 붙은 검토된 제외로 처리한다. 모든 downstream 종도 하나 이상의 규칙에서 생성 종으로 선언한다.
- 반응식·mapping Evidence·계수는 caller가 관리한다. 코드가 반응을 발견하거나 평형·표준상태 변환을 만들지 않는다.

## 해석 경계

계산 결과는 선언된 반응/rename 장부의 형식 보존성만 뜻한다. 실제 반응성, 수율, 시간별 양 보존, 용매·활동도 변환, kinetics, 부식률 또는 공정 적용성은 확인하지 않는다. 각 계수 집합은 전체 과정이 아닌 하나의 caller-declared transfer rule에 대응한다. 기존 `wco2_chemistry_boundary`와 연속 사용하면 provenance/state-path 검사와 elemental/charge bookkeeping을 분리해 기록할 수 있다.
