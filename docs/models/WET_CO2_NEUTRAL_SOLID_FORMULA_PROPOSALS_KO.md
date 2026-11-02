# Wet-CO₂ 전해질의 중성 이온쌍 고체식 후보 생성

## 목적과 범위

`chemistry.wet_co2_neutral_solid_formula_proposals`는 사용자가 제공한 양이온과 음이온 사이에서 전하가 상쇄되는 가장 작은 정수비를 계산하고, 두 이온에 기록된 원소 조성을 합쳐 조성식 후보를 만듭니다. 동일한 원소 조성은 하나의 제안으로 묶되, 생성에 사용된 이온쌍을 모두 남깁니다.

이는 선언된 이온 목록 안의 이성분 전하중성 조성 제안입니다. 광물 식별, 실제 고체상 발견, 수용액 반응의 타당성, 안정성, 용해도, 석출 여부를 판정하지 않습니다. 다중 이온 성분 고체와 수화물·고용체·비화학양론 상은 범위 밖입니다.

## 입력과 계산

양이온·음이온 각각에 종 ID, 부호가 있는 전하수, 완전한 원소 조성, 원자료 레코드 ID 및 SHA-256을 포함한 Evidence를 지정합니다. 각 종은 개별 출처 증거로 추적되어야 합니다. 입력 최대치는 각 전하 유형 80개이며 Cartesian pair 상한은 요청자가 제한합니다.

양이온 전하를 `z_plus`, 음이온 전하 절댓값을 `abs(z_minus)`, 최대공약수를 `gcd`라 할 때 최소 조성 계수는 다음과 같습니다.

```text
n_plus = abs(z_minus) / gcd(z_plus, abs(z_minus))
n_minus = z_plus / gcd(z_plus, abs(z_minus))
composition = n_plus * cation_atoms + n_minus * anion_atoms
```

각 후보는 전하중성을 재확인하고 계산 입력 전체의 digest와 생성 이온쌍 lineage를 출력합니다. 동일 조성은 조성 맵을 기준으로 중복 제거합니다.

## 적용 및 한계

- 사용자가 선정한 이온만 고려하므로 후보 집합은 수용액 화학종 전체나 가능한 모든 고체상을 포괄하지 않습니다.
- 결과는 formula proposal일 뿐입니다. 후보 선별, Ksp·활동도·온도 의존성, 반응 방향, 평형 또는 동역학 판단에는 별도 출처 자료와 독립 계산이 필요합니다.
- 별도 질량수지, 포화도, 핵생성, 성장, 부착, 스케일 보호 또는 부식률을 계산하지 않습니다.
- 원소식과 전하가 맞더라도 실제 상이 존재하거나 운전 조건에서 형성된다는 의미는 아닙니다. 사용 전에 화학식·분석종 정의와 고체상 해석을 전문가가 확인해야 합니다.
- API는 synthetic 입력 증거를 거절하며, 각 이온 레코드의 원자료 SHA-256을 요구합니다. 계산 결과가 원자료 사용권을 부여하지는 않습니다.

## 참고

- IUPAC, *Compendium of Chemical Terminology (Gold Book)*: [IUPAC Gold Book](https://goldbook.iupac.org/)
- OpenStax, *Chemistry 2e*, ionic compounds and charge-balanced empirical formula construction: [OpenStax Chemistry 2e](https://openstax.org/details/books/chemistry-2e)

위 자료는 일반적인 이온 전하 및 실험식 산정 원리를 확인하기 위한 독립 참고자료입니다. 재료·공정 데이터나 특허·규격 고유 수치는 사용하지 않았습니다.

## API

- 모듈: `matintegrity.wet_co2_neutral_solid_formula_proposals`
- 모델 ID: `chemistry.wet_co2_neutral_solid_formula_proposals`
- 스키마: `matintegrity.wet_co2_neutral_solid_formula_proposals.v1`
- 입력 계약: `WetCo2NeutralSolidFormulaProposals`
- 이온 행 계약: `WetCo2AqueousIon`
- 계산 함수: `propose_wet_co2_neutral_solid_formulas(request)`
- 등록 메타데이터: `specifications()`
- source ID: `caller_ion_pair_charge_balanced_solid_formula_proposals`, `caller_declared_aqueous_ion_formula_and_charge`
