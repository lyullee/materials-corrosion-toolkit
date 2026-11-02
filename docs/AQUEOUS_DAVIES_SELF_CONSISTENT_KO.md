# 수용액 Davies 활동도 자기일관 평형

`chemistry.aqueous_davies_self_consistent_speciation`는 호출자가 정의한 정방형 단일 액상 질량작용/물질수지 모델과 Davies 활동도 계수를 반복 결합한다. 기존 고정 감마 모델은 그대로 사용할 수 있으며, 이 계산기는 그 주위에 하나의 제한된 고정점 반복을 추가한다.

## 반복 계산

초기 종 활동도 계수 `gamma_c`로 기존 질량작용 모델을 풀어 활동도와 몰농도 `c_i`를 얻는다. 입력의 `water_mass_per_solution_volume_kg_L`를 `w`라 하면 molality는 `m_i = c_i / w`다. 전체 이온 목록으로부터 `I = 0.5 Σ m_i z_i²`와 전하 잔차 `Σ m_i z_i`를 계산한다. 온도와 용매 조건에 맞는 사용자가 제공한 Davies `A`를 적용해 molality 기준 계수 `gamma_m`을 구한 뒤 `gamma_c = gamma_m / w`로 질량작용의 1 mol/L 표준상태에 맞춘다. 감쇠율 `lambda`에 따라 `ln(gamma_c,next) = ln(gamma_c) + lambda [ln(gamma_c,target) - ln(gamma_c)]`로 갱신한다.

최대 절대 로그 계수 차가 사용자가 정한 허용값 이내이고, 질량작용 내부 solver가 계산 상태이며, molality 기준 전하 잔차가 허용 범위 안일 때만 결과를 `computed`로 반환한다. 반복 예산 내 수렴하지 않거나 중간 단계의 화학 풀이가 실패하면 부분 최종 평형을 만들지 않는다. 입력/활동도 공급자 digest와 매 반복 이온강도·전하잔차·고정점 잔차를 보존한다.

## 필수 입력 해석

기존 mass-action 모델의 표준상태는 1 mol/L 기준 무차원 활동도다. Davies는 molality 기준이며 `gamma_c c = gamma_m m`, `m=c/w`에서 `gamma_c=gamma_m/w`를 적용한다. 용액 부피당 물의 질량을 kg-water/L-solution 단위로 호출자가 제공하고 그 환산을 검토해야 한다. 용액 밀도만으로 물 질량을 추정하지 않는다. 결과에는 molality·molarity 표준상태의 계수를 별도로 보존한다. Davies `A`는 온도·용매별 근거와 revision/digest를 호출자가 제공한다. 계산기는 물, 활동도계수, 평형상수, 전하식 또는 분석물질 수지를 추론하거나 보정하지 않는다.

이온강도 입력 상한은 최대 0.5 mol/kg-water이며 더 낮은 caller limit도 지정할 수 있다. 이 값은 Davies 근사 범위 밖의 농축 염수에 다른 활동도 모델을 자동 적용하지 않도록 막는다. 종 목록 완전성, 전하 균형식, 단일 액상 및 침전 부재를 별도 검토해야 한다. 중성종의 salting effect, 기액 평형, 다상 경쟁, 침전·보호 scale의 시간 변화, 부식률과 설계 판정은 범위에 없다.

예제 수치는 synthetic fixture이며 물성값이나 재료 권고값이 아니다. 공개 근거 등록은 `data/catalogs/sources.json`과 `THIRD_PARTY_NOTICES.md`에서 확인한다. 수치 테스트와 독립 실험 비교는 별도의 검증 작업으로 남아 있다.
