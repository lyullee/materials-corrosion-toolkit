# 수용액 반응망 열역학 cycle audit

`chemistry.aqueous_thermodynamic_cycle_audit`는 caller가 지정한 종·반응·평형상수 집합에서 원소/전하 균형과 선형 반응 cycle의 log10(K) 닫힘을 검사한다. 종 또는 상을 자동 발견하거나 평형 speciation을 계산하지 않는다.

## 계산 정의

종을 행, 반응을 열로 놓은 화학량론 행렬 `S`를 만든다. 반응 cycle 계수 `c`는 `S @ c = 0`을 만족한다. 이에 대응하는 평형상수는 `c · log10(K) = 0`이어야 한다. 구현은 `S`의 SVD로 caller가 검토한 상대 rank tolerance를 적용해 orthonormal 오른쪽 null-space basis `N`을 구성하고 `||N @ log10(K)||₂`를 closure 잔차로 반환한다. 이 norm은 cycle basis의 직교 회전에는 불변이지만, 판정은 선택된 rank와 caller tolerance에 의존한다.

각 반응은 입력한 원소식과 전하가 균형이어야 한다. 공급한 식, 반응 방향, 활동도 표준상태, 온도와 평형상수의 일치는 caller가 검토한다. 계수와 source record ID는 Evidence source ID 및 그 Evidence 원자료 파일 SHA-256에 묶인다. 공개 dataset Evidence는 이용조건/라이선스를 함께 기록해야 한다.

## 상태 해석과 한계

- `computed`: 입력 검토가 모두 완료되고 반응 균형을 통과했다. dependent reaction이 있으면 선언한 cycle residual이 허용치 이하여야 한다. cycle이 없으면 `cycle_closure_status=no_reaction_cycles_to_check`이며 이 경우 평형상수 cycle consistency 자체를 시험하지 않았다. 평형상수의 정확도나 독립 검증을 보증하지 않는다.
- `needs_data`: 검토 누락, 원소/전하 불균형 또는 선언 허용치보다 큰 cycle residual이 존재한다.
- `out_of_scope`: 유한 수치 지원을 벗어나거나 rank 분해가 실패했다.

Cycle 공간은 선언된 반응 matrix만 사용한다. 종 목록 누락, 잘못된 반응식, 다른 표준상태/온도 데이터 혼합은 자동 발견하지 않는다. cycle consistency는 모델 유일성, 상 안정성, 실험적 타당도, 부식속도 또는 재료 적합성을 뜻하지 않는다. 수용액 mass-action의 반응식·평형상수 사용에 대한 공개 방법 문서는 [USGS PHREEQC Version 3 문서](https://water.usgs.gov/water-resources/software/PHREEQC/Phreeqc_3_2013_manual.pdf)에서 확인할 수 있다. 구현은 자체 행렬 연산이며 PHREEQC 코드/parameter database를 포함하거나 호출하지 않는다.

registry 합성 입력은 `examples/model_inputs.json`의 `chemistry.aqueous_thermodynamic_cycle_audit`를 참조한다. 값은 모두 대수 wiring 예제이며 실제 화학 평형 상수가 아니다. 수치·외부 solver 비교는 후속 일괄 검증에서 수행한다.

이미 `AqueousMassActionSystem`을 갖고 있다면 `integration.aqueous_mass_action_cycle_audit`를 사용해 종·반응 입력을 재사용할 수 있다. 이 adapter는 모든 반응 ID가 정확히 한 번씩 바인딩되는지 확인하고, 각 `source_record_id`와 `Evidence` 파일 SHA를 묶은 후 같은 cycle evaluator를 호출한다. 기존 system에 원소식이 없으면 조성을 추정하지 않고 `needs_data`로 남긴다. 합성 연결 입력은 `examples/model_inputs.json`의 해당 integration ID에 있다.
