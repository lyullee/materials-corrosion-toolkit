# 가스켓 조인트 볼트 명목강도 비교

`fabrication.gasket_bolt_nominal_strength_screen`은 계산된 `fabrication.gasket_multi_bolt_sector_equilibrium` 결과의 각 절점별 볼트 축력으로부터 재현된 명목 인장응력을, caller가 제공한 볼트별 온도 의존 proof-strength 자료와 비교한다.

기본 관계는 `sigma_nom = F_tension / A_tensile`이며, `A_tensile`은 digest가 재계산된 upstream 입력에서 가져온다. 온도 보정강도는 caller 곡선의 두 인접 점 사이에서만 piecewise-linear interpolation으로 계산한다. 커브 밖 온도는 추정하지 않고 `out_of_scope`로 닫는다. 출력에는 절점별 stress, caller strength, 차이, 무차원 비와 source curve lineage를 반환한다.

## 입력 요구

- 계산된 다중 볼트/가스켓 sector quasi-static equilibrium 결과가 필요하다. Model ID·version·inputs·RunContext를 이용해 upstream input digest를 다시 확인하고, result의 nominal stress가 입력 bolt force area와 맞는지 확인한다.
- Downstream RunContext의 asset, location, time basis와 request의 physical scope를 upstream joint 결과와 일치시켜야 한다.
- 각 bolt ID마다 동일한 물리 볼트/재료조건에 적용 가능한 proof-strength 온도 곡선, ordered knots, curve SHA-256, Evidence, 강도 정의 검토와 bolt/material mapping 검토를 제공한다.
- 온도 절점 수는 upstream load-step 수와 일치해야 한다. 강도 곡선 사이 보간의 적용가능성도 caller가 확인한다.

## 해석 한계

이 결과는 caller 수치와 명목 축응력의 결정론적 비교다. 계산된 볼트 nominal stress는 나사산 뿌리 응력, 굽힘·비틀림·좌굴·베어링·local FE stress가 아니다. Caller strength 값도 표준 허용응력으로 자동 승격되지 않는다. 음의 margin 표시는 비교값 초과를 뜻할 뿐 코드 합격·불합격, proof-load qualification, safety factor, 실패확률, 피로·creep·부식 영향 또는 joint acceptance 판정이 아니다.

본 계산 및 문서는 공개 배포를 위해 새로 작성했다. 이 API의 수치 통합시험과 독립 재료/조인트 검증은 별도 수행 대상이다.
