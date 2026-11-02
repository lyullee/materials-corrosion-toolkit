# 외부 compliance 기반 비선형 gasket 접촉장

`fabrication.flange_nonlinear_contact_field`는 구조해석 provider가 제공한 상대 flange compliance, gasket 반력 제외 자유 닫힘량, node별 접촉 면적과 압축력–압축량 곡선으로 circumferential 접촉장을 계산한다. 좌표, 하중 합성, FE 경계조건, 재료 곡선 검토와 계산 사용 권한은 호출자가 제공한다.

각 node의 gasket 곡선은 `(compression_m, force_N)` 점으로 표현한다. 원점에서 시작하고 압축량과 힘이 모두 엄격히 증가하는 가역 piecewise-linear curve여야 한다. 이 조건으로 힘에서 압축량을 유일하게 역산하고, active contact node에 대해

`C q + c(q) = u0`

를 푼다. `q`는 비음수 접촉력, `C`는 상대 flange compliance, `c(q)`는 caller curve의 역함수로 얻은 gasket 압축량, `u0`는 gasket 반력이 없을 때의 닫힘량이다. 접촉 중이 아닌 node는 `q=0`이며 `Cq-u0 >= 0`이어야 한다. 양의 접촉력·간극 조건을 확인하고 허용 잔차 내에서만 결과장을 반환한다.

감쇠 Newton 반복은 caller curve support 안에서만 허용한다. 곡선 끝을 넘는 힘, 미수렴 또는 비양의 compliance는 `out_of_scope`로 처리한다. 128 node, node별 최대 1,000 curve point, 반복 및 line-search 예산으로 계산량을 제한한다. 입력과 구조 provider의 configuration/result digest가 출력에 유지된다.

## 적용 한계

곡선은 단일 가역 경로이므로 unloading/reloading hysteresis, viscoelastic branch, 온도/속도 의존성, creep와 손상은 포함하지 않는다. 이 API는 flange compliance를 생성하거나 FEA solver를 대신하지 않는다. 평균 node 압력은 force/area이며 국부 peak stress, flange element stress, 누설률, seal 성능, code acceptance나 설계 qualification을 뜻하지 않는다. 제공 예제는 synthetic fixture이고 실행 검증 및 외부 solver 비교는 아직 수행하지 않았다.
