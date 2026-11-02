# 평면 간극의 lumped transient 유동 이력

`corrosion.planar_slit_transient_hydraulic_history`는 caller가 제공한 일정 구간별 압력차와 간극으로, 넓은 평행판 간극을 흐르는 비압축성 Newtonian 유체의 signed 체적 유량을 계산한다. 기존 steady `PlanarSlitHydraulicFlow`는 구간별 압력 평형만 계산하지만, 이 모델은 한 차원 lumped fluid inertance를 추가해 입력 변화 뒤 유량이 연속적으로 완화되도록 한다.

## 모델식

각 구간에서 모든 cell의 길이·폭·간극이 고정되고 압력차가 상수라고 둔다. 직렬 slit-cell의 준정상 laminar resistance와 유체 기둥 inertance는 다음과 같다.

```text
R = Σᵢ 12 μ Lᵢ / (w hᵢ³)
I = Σᵢ ρ Lᵢ / (w hᵢ)
I dQ/dt + R Q = Δp
```

구간 내 해는 닫힌 형태다.

```text
λ = R/I
Q∞ = Δp/R
Q(t+Δt) = Q∞ + (Q(t)−Q∞) exp(−λΔt)
∫Q dt = Q∞Δt + (Q(t)−Q∞)(1−exp(−λΔt))/λ
```

입력 절점에서 압력 또는 aperture가 바뀌어도 유량 상태 `Q`는 이어진다. 음수 압력차, 음수 유량과 구간 내 역류를 보존하고 역류 검토 gate와 교차 시각을 출력한다. 각 구간은 독립적으로 piecewise-constant coefficient로 풀며, 입력 시간창 바깥을 외삽하지 않는다.

## 입력·자료 lineage

요청은 asset/location/physical-scope/time basis, 순서가 고정된 고유 cell ID와 길이(단일 셀도 허용), 각 구간의 양의 aperture, transverse width, signed pressure history, 초기 signed flow, 고정 밀도·점도, 최대 Reynolds 기준을 받는다. geometry, pressure, fluid-property 원천은 각각 provider ID/revision, record SHA-256와 이에 일치하는 `Evidence`가 필요하다. 출력의 셀별 위치/속도 배열은 이 순서를 따른다. 사용권 Evidence와 license ID, geometry/clock, pressure sign/reference, property support, wide-slit·laminar·lumped-inertance 적용성, flow reversal 및 계산 사용 review도 별도 확인한다.

## 적용범위와 한계

- 셀 횡방향 폭은 간극보다 충분히 크고, 모든 셀에서 caller가 검토한 Reynolds 한도를 넘지 않아야 한다.
- 저항은 완전 발달 평행판 Poiseuille 관계이고 inertance는 1차원 fluid-column 근사다. 이 모델은 시간의존 Navier–Stokes, Womersley 속도분포, compressibility, entrance/roughness/minor losses, 난류 또는 유동 불안정 계산이 아니다.
- aperture와 pressure는 외생 입력이다. 유동이 간극을 변화시키거나 화학·부식·질량전달과 동시에 수렴하지 않는다.
- 시각별 유량은 구간 내 analytic solution이다. 구간별 적분 체적과 초기 0을 기준으로 한 부호 포함 누적 체적을 함께 반환한다. 유량 또는 Reynolds 지원범위를 처음 벗어나면 완료 구간 prefix와 실패 index 및 누적량 prefix를 가진 `out_of_scope`를 반환한다.
- 출력은 caller 모델의 계산 결과이며 외부 실험 검증, 설계 승인, 부식률, 구조 건전성 또는 안전성을 뜻하지 않는다.

## Restricted transport 연동

`matintegrity.bind_planar_slit_transient_hydraulic_interval()`은 계산 완료된 유량 `AssessmentResult`와 그 결과 digest, 구간 index, 해당 구간의 local-clock `RestrictedTransportRequest`를 받아 `(bound_request, velocity_callback)`을 반환한다. callback은 solver가 요구하는 각 local time에서 구간의 해석식 `Q(t)`를 평가하고, 간극별 유량을 face velocity로 변환한다. transport 구간의 시간창은 hydraulic interval 하나와 정확히 일치해야 하며 외삽은 거절한다.

여러 구간에는 `matintegrity.bind_planar_slit_transient_hydraulic_history_series()`를 사용한다. 요청 순서와 hydraulic interval 순서는 일치해야 하며 upstream input/result digest는 한 번 검증한 뒤 각 구간 binding에 재사용된다. 반환값은 각 구간의 `(bound_request, velocity_callback)` 튜플이며, callback은 그 구간의 local time을 받는다. 선택 interval의 저항·관성·평형 유량·시작/끝 유량이 digest-pinned 입력과 결과 기록에 맞는지 다시 대조해 일관되지 않은 결과를 거부한다. 이는 결과 내용의 무결성/자기일관성 검사이며 solver 실행 provenance나 실험 정확도를 대신하지 않는다.

공간 face aperture는 인접 cell 간극의 cell-width 가중 선형 재구성으로 결정하므로 `face_aperture_interpolation_reviewed=True`를 명시해야 한다. request에도 time-varying advection 및 flow continuity review가 필요하다. 역류 interval은 distal inflow 조성과 역류 검토가 요구된다. 아래는 연결 형식 예시이며 실행 검증된 수치 결과가 아니다.

```python
from matintegrity import bind_planar_slit_transient_hydraulic_interval
from matintegrity.restricted_transport import solve_restricted_transport

bound_request, velocity = bind_planar_slit_transient_hydraulic_interval(
    transport_request,
    hydraulic_history_result,
    hydraulic_result_sha256,
    interval_index=0,
    face_aperture_interpolation_reviewed=True,
)
transport_result = solve_restricted_transport(
    bound_request,
    reaction=reaction_callback,
    axial_advection_velocity=velocity,
)
```

이는 기존 transport solver에 계산된 과도 유동을 단방향으로 전달하는 operator split이다. 유량 모델은 transport 농도·반응·부식 손실에 되먹임되지 않는다.

합성 예제, 수치 실행과 회귀 검증은 아직 수행하지 않았다. 공개 배포 전 analytic limiting cases, interval refinement, steady-limit, pressure reversal, aspect-ratio/Re rejection, mass continuity boundary coupling을 별도로 확인해야 한다.
