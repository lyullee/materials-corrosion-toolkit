# 다층 scale의 확산 저항 한계

`chemistry.layered_scale_diffusion_limit`는 지정한 용질의 bulk 농도와 계면 농도 사이 정상상태 확산 한계를 계산한다. 호출자는 bare solution film과 순서가 있는 scale layer마다 두께, 유효확산계수와 solution-to-layer 분배계수를 공급한다. 한 층의 농도기준 확산저항은 `L/(D_eff K)`이고, bare film 저항과 scale 저항을 직렬 합산한다.

scale-covered patch의 flux는 농도차를 전체 저항으로 나눈다. 미피복 patch는 bare-film 저항만 적용한다. 두 flux를 caller의 covered-area fraction으로 병렬 혼합하고, 지정한 transported-species 당 electron equivalent로 Faraday 환산 전류 밀도 상한을 계산한다. 결과는 scale reference, material/solution condition, 공급자 revision 및 입력 digest에 결속된다.

## 두께 이력과 연결

`layered_scale_transport_request_from_history()` adapter는 계산이 완료된 `chemistry.caller_surface_scale_kinetics` `AssessmentResult`와 transport 요청을 받아, 사용자가 선택한 **정확한 시간 knot**의 scale 두께를 지정한 layer 하나에 연결한다. 물리 scope, 기판/용액 조건과 scale phase가 일치해야 한다. layer mapping review가 필수이며, 결과에는 완전한 source assessment digest, 선택 시간, phase·layer ID가 보존된다. knot 사이 시간 보간은 하지 않는다.

```python
from matintegrity.adapters import layered_scale_transport_request_from_history

bound_request = layered_scale_transport_request_from_history(
    scale_assessment,
    transport_request,
    selected_time_s=3600.0,  # scale_history에 실제 있는 시간이어야 함
    scale_layer_id="inner-scale",
    scale_state_to_layer_mapping_reviewed=True,
)
```

이 연결은 한 균일 scale phase가 사용자가 정한 한 transport layer와 일치한다고 선언할 뿐이다. 이력 모델은 다른 층을 생성하지 않으며, 두께에서 기공률·피복률·확산계수·분배계수도 추정하지 않는다.

## 입력 검토와 적용 범위

분배계수의 농도 기준, 각 층의 유효확산계수, 층 순서, 국부 계면농도, 면적 피복률과 전자 당량은 caller가 근거와 함께 검토해야 한다. 균일 직렬층 및 covered/uncovered 평행 patch 가정을 명시적으로 요구한다. 예제의 숫자는 synthetic 입력이다.

이 계산은 확산 한계 상한이다. 실제 반응 flux는 이보다 작을 수 있으며, 본 API는 scale 침전·형상·기공률·접착·coverage를 예측하지 않는다. Butler–Volmer kinetics, 전하 균형, 실제 부식전류, 금속손실, 수명 또는 합격 판단으로 승격하지 않는다. 계산 시험과 scale 실험 기반 qualification은 별도 검증 과제다.
