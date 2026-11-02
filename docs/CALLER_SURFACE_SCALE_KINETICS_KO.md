# 호출자 보정 단일상 표면 scale 이력

`chemistry.caller_surface_scale_kinetics`는 식별된 한 고체상 scale에 대해 caller가 제공한 구간별 saturation ratio 끝점, 침전/용해 molar-flux 계수와 molar volume을 적분해 면적 평균 scale 두께 이력을 계산한다. 기본은 구간 내 상수 포화비이며 `saturation_ratio_end`를 추가하고 `linearly_varying_saturation_reviewed=True`를 선언하면 해당 구간의 양 끝을 잇는 선형 경로를 사용한다. 실제 포화화학 경로를 추정하지 않는다.

## 관계식

각 interval duration을 `Δt`, 선형 포화비 끝점을 `Ω_0`, `Ω_1`이라 한다. 침전 노출량은 `∫₀^Δt max(Ω(t)-1,0)^n_p dt`, 용해 노출량은 `∫₀^Δt max(1-Ω(t),0)^n_d dt`다. 계산은 포화비가 1을 통과하는 위치를 포함하는 양의 부분 거듭제곱을 해석적으로 적분한다. 상수 경로는 이 식의 특수 경우다. 각 노출량에 해당 계수를 곱해 면적당 양을 구한다. 감소 경로가 과포화에서 불포화로 바뀌면 crossing 전에 만들어진 침전물은 이후 용해에 쓸 수 있다. 반대로 증가 경로에서는 기존 scale만 먼저 용해할 수 있고, 구간 후반에 생길 침전량을 앞선 용해에 소급 사용하지 않는다. 매 interval의 용해량은 그 시간 순서에서 사용 가능한 scale inventory로 제한한다. `V_m`은 caller 공급 scale molar volume이며 누적량으로부터 `h(t)=h_0 + V_m [N_p(t)-N_d(t)]`를 반환한다.

## 입력과 경계

`k_p`, `k_d` 단위는 `mol m⁻² s⁻¹`, reaction order는 dimensionless, `V_m`은 `m³ mol⁻¹`, 두께는 `m`이다. 계수의 재료·용액·온도 적용성, phase identity, 표준상태와 computational-use 권한을 caller가 검토하고 source/configuration digests로 고정한다. 선형 endpoint 보간은 caller가 이미 제공한 포화비 이력의 구간 표현이며 열역학 상태 계산이나 saturation chemistry solver가 아니다.

기준온도의 속도상수를 재사용하려는 경우 `rate_reference_temperature_K`, `precipitation_activation_energy_J_mol`, `dissolution_activation_energy_J_mol`과 `minimum_rate_valid_temperature_K`/`maximum_rate_valid_temperature_K`를 모두 제공하고 `arrhenius_temperature_scaling_reviewed=True`로 검토한다. 두 rate constant는 각각 `k(T)=k(Tref) exp[-Ea/R (1/T-1/Tref)]`로 계산되며 실제·기준 온도 모두 선언 범위 안이어야 한다. 유효 계수는 결과에 명시한다. 활성화에너지나 온도 support가 없으면 원 계수는 요청 `temperature_K`에 직접 적용되는 값으로 해석한다. 이 옵션은 caller 계수의 제한된 온도 스케일링이며 반응 메커니즘이나 계수를 추정하지 않는다.

결과는 단일상·균일 scale 층의 volume-equivalent 평균 두께다. 경쟁 상, 핵생성 지연, porosity/roughness, 입자 이탈, 이동, 열화, mass-transfer 제한, 기재 보호 효과, 부식률/수명과 acceptance는 포함하지 않는다. 재료별 계수는 패키지에 포함하지 않고, synthetic 예제는 물성 권고값이 아니다. 수치 검증과 실제 시편 검증은 별도 작업이다.
