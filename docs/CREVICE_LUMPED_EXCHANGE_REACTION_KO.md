# 크리비스 단일 성분 lumped 교환·소모 모델

`degradation.crevice_lumped_exchange_reaction_history`는 caller가 정의한 일정 체적의 완전혼합 control volume 안에서 한 용존 성분의 농도 변화를 계산한다. 각 시간 구간에서 교환 유량 `Q`, 외부 bulk 농도 `C_b`, 1차 소모 계수 `k`를 상수로 둔다. 입력 단위는 각각 `m³/s`, `mol/m³`, `1/s`이며 control volume은 `m³`다.

구간별 상태 방정식은 다음과 같다.

```text
dC/dt = (Q/V)(C_b - C) - k C
λ     = Q/V + k
C∞    = (Q/V) C_b / λ                 (λ > 0)
C(t+Δt) = C∞ + (C(t) - C∞) exp(-λ Δt)
```

`λ=0`이면 농도는 해당 구간에서 유지된다. 모델은 각 구간을 폐형식으로 전파하고, 같은 정확해를 적분해 구간 순교환량과 반응 소모량을 따로 기록한다.

```text
Δn_inventory = V(C_end - C_start)
Δn_exchange  = Q ∫(C_b - C)dt
Δn_sink      = V k ∫C dt
residual     = Δn_inventory - (Δn_exchange - Δn_sink)
```

매 구간에 일정 체적, 완전혼합, 상수 구간 입력, 1차 소모식, 종 정체성·농도 단위, 계산 사용권한 검토가 필요하다. 데이터 또는 수식 lineage는 Evidence와 provider ID/revision으로 남긴다. review가 빠지면 `needs_data`를 반환한다. 비유한 수치, 음의 상태 등 지원 범위를 벗어나면 완료된 구간 prefix와 실패 구간을 포함해 `out_of_scope`로 닫는다.

이 API는 caller가 선택한 단일 용존 성분용 lumped screen이다. 공간 농도구배, 다성분 이동도, 전기이동, 평형 종분화, 침전·용해, 유동장 계산, 확산 경계층, 벽 반응식 추정, 금속 손실이나 규격 판정은 포함하지 않는다. 이 목적에는 기존 공간별 `solve_restricted_transport` 및 mass-action/kinetics API를 별도로 결합해야 한다. 예제 입력과 검증 결과는 아직 등록되지 않았으며, 본 증분에서는 테스트·계산 실행을 하지 않았다.
