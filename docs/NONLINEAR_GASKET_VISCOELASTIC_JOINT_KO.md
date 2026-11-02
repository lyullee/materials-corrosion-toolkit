# 비선형 가스켓 점탄성 조인트 이력

`fabrication.nonlinear_gasket_prony_joint_history`는 caller가 제공한 가스켓 평형 응력–변형률 backbone과 각 generalized-Maxwell branch의 비선형 backbone을 시간 의존 branch 상태 및 볼트 힘–변위 곡선과 결합한다. 각 시간 knot에서 단일 자유도 축방향 조인트의 폐합형 force balance를 구한다.

## 구성식과 수치 경로

평형 branch와 점탄성 branch는 모두 원점에서 시작하는 단조 비감소 piecewise-linear `stress_Pa(compressive_strain)` 곡선이다. 각 Maxwell branch는 고유의 양의 relaxation time `τᵢ`와 초기 내부응력 `qᵢ(0)`을 갖는다. 각 시간 구간의 변형률은 knot 사이에서 선형으로 변한다고 선언한다. 이 경로가 branch 곡선의 절점을 통과하면 해당 절점에서 구간을 분할한다. 분할된 한 선형 구간에서 branch backbone 응력 변화량이 `Δσᵢ`이고 지속시간이 `Δt`이면 상태는 다음 식으로 갱신한다.

`qᵢ,new = qᵢ,old exp(−Δt/τᵢ) + (Δσᵢ/Δt) τᵢ [1 − exp(−Δt/τᵢ)]`

branch 응력 합과 equilibrium backbone 응력으로 가스켓 힘을 계산한다. 볼트 force-change 곡선은 초기 기준 신장으로부터의 변화량을 반환하며, 각 knot에서 아래 잔차가 0이 되도록 strain을 bracket 후 이분 탐색한다.

`R(ε) = Fbolt,initial + ΔFbolt((εinitial − ε) h − Δlfree) − A[σeq(ε) + Σqᵢ(ε)] − Fseparating`

여기서 `A`는 압축 유효면적, `h`는 가스켓 압축 높이다. 곡선 지지구간 밖에서는 외삽하지 않고 `out_of_scope`를 반환한다. 초기 branch 상태, 재료 조건/공급자 계보, 응력 backbone과 볼트 curve는 입력 digest로 함께 고정된다.

## 입력 검토와 한계

평형 곡선·각 branch 곡선의 실험 해석, 시간/온도/압축률 적용성, branch 초기응력, 볼트 곡선의 유효 support, 힘 부호와 접촉 면적을 별도 검토해야 한다. 요청에는 각 검토 gate와 계산 이용권한 확인값을 명시한다. 예제는 합성 값이며 재료 데이터나 자격화 증거가 아니다.

이 API는 선언된 변형률 knot 사이의 선형 재구성, 선형 dashpot 감쇠와 piecewise-linear spring backbone으로 이루어진 비선형 generalized-Maxwell 축약 모델이다. 접촉 분리·재접촉, 인장 전달, 압력 분포, 비축대칭/플랜지 휨, 열·유체 누설, sealing 기준, curve fitting/조건 전이 또는 규격 적합을 계산하지 않는다. 접촉 이력을 계산하려면 별도 `fabrication.unilateral_nonlinear_gasket_prony_joint_history`를 사용할 수 있다. 이 확장은 zero-compression 상태에서 gasket force를 0으로 제한하고, 분리 중 Maxwell branch 상태는 고정한다. 전이 시각을 계산하지 않고 요청에 선언된 시간 knot에서만 open/reclose를 기록하므로 시간 mesh 의존 사건 경계다. 분리 상태의 branch 고정 가정과 knot 사이 선형 분리 외력 해석을 별도 검토해야 한다. 공간 플랜지 휨, 접촉 압력 분포, 누설 및 sealing 판정은 여전히 범위 밖이다.
