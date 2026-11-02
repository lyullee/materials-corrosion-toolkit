# 사용자 프로필 기반 재료·검사·SCC 작업

이 문서는 공개 배포물에 규격표나 제3자 합격기준을 넣지 않고 사용자가 보유한 데이터와 승인 기준을 연결하는 방법을 설명한다. 모든 프로필에는 식별자·개정·근거와 digest를 기록한다. 계산 결과는 입력한 범위에만 적용하며 규격 적합성이나 현장 자격을 자동으로 주장하지 않는다.

## 재료 규격명과 인증서

`SpecificationDesignation`은 namespace, designation, edition, product form, condition을 모두 분리한다. `resolve_specification_alias`는 `SpecificationProfile`에 명시된 exact alias만 canonical designation으로 바꾼다. 철자 유사도, 판본 간 동등성 또는 재질 대체를 추론하지 않는다. Unknown과 여러 profile이 동시에 일치하는 ambiguous 상태는 그대로 반환한다.

`reconcile_material_certificates`에는 인증서 측정값, heat/lot, 사용자 요구범위와 `CertificateUnitRule`을 함께 전달한다. 단위 변환은 명시한 source/canonical 조합만 허용한다. 측정값의 expanded uncertainty 구간이 요구 경계를 넘는 경우 단순 합격으로 축약하지 않고 행별 mismatch/unknown 근거를 보존한다. 요구범위는 사용자가 합법적으로 사용할 수 있는 기준에서 작성해야 하며 라이브러리에는 표준 chemistry나 strength 표가 없다.

## 표면 indication 판정

`assess_surface_indications`는 visual, liquid-penetrant, magnetic-particle 자료에 공통으로 사용할 수 있다. 입력은 검사 방법별 procedure parameter, examined region, indication geometry와 uncertainty, caller grouping, negative-observation/review evidence를 포함한다. `CallerAcceptanceProfile`의 exact unit numeric rule과 prohibited reported-class rule만 실행한다.

판정 의미는 다음과 같다.

- `accept`: 적용 가능한 caller rule이 모두 통과하고 필요한 근거가 있다.
- `reject`: 적용 가능한 caller rule이 명시적으로 실패했다.
- `review`: profile 적용범위 밖이거나 사람이 검토해야 한다.
- `insufficient_evidence`: procedure, negative observation 또는 필수 metric 근거가 부족하다.

Reported class와 indication group은 재분류하지 않는다. 이 결과는 수명, PoF 또는 검사 procedure qualification이 아니다.

## SCC 사용자 rule

등록 모델은 `degradation.chloride_scc_user_screening`, `degradation.ammonia_scc_user_screening`, `degradation.alkaline_scc_user_screening`이다. `SCCScreeningFact`로 environment/material/stress fact와 source digest를 제공하고, `SCCMechanismProfile`에 AND condition과 OR rule을 정의한다. Exact unit이 다르면 자동 변환하지 않고 unknown으로 처리한다.

`unknown_policy=indeterminate`는 불완전 evidence를 `needs_data`로 유지한다. `screen_in`은 보수적으로 potentially-applicable로 올릴 수 있지만 screen-out에는 사용할 수 없다. 결과는 applicability screening일 뿐 initiation threshold, crack growth, remaining life, acceptance 또는 qualification이 아니다.

## POD 캠페인 사전 감사

`audit_pod_campaign`은 POD 곡선을 적합하기 전에 캠페인 coverage를 확인한다. 사용자가 정한 최소 observation/hit/miss/flaw-size bin, 필수 operator/material/geometry/access group, blind 여부와 specimen 반복 여부를 검사한다. 모든 조건을 만족한 `ready_for_model_fit`도 POD procedure qualification을 의미하지 않는다. 실제 곡선 계산은 등록된 hit/miss 또는 signal-response POD 모델에 별도로 전달하고, 독립 시편·operator 효과·false-call evidence와 적용성 검토를 추가해야 한다.

## 재현성과 공개 배포

각 경로는 canonical input/result digest를 만든다. 원 인증서, 유료 기준, 사내 procedure와 승인 profile은 공개 저장소 밖에서 관리하고 공개 예제에는 합성 자료나 재배포 가능한 자료만 사용한다. 공개할 때는 profile 자체의 사용 권리를 별도로 확인하고, 결과 digest만으로 원문 사용 권리가 생기지는 않는다는 점을 유지한다.
