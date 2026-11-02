# caller scale coverage kinetics

`chemistry.caller_scale_coverage_kinetics`는 포화비에 따라 caller가 정한 attachment와 detachment 속도상수·차수를 적용해 면적 평균 피복률 `θ`와 누적 inventory balance를 계산한다. 포화비가 구간 상수이면 닫힌형 적분을 사용하고, caller가 선형 포화비 경로를 검토한 경우 coverage와 attachment/detachment 누적량을 adaptive RK4 step doubling으로 적분한다.

## 구간별 온도 이력

`ScaleCoverageKineticInterval.temperature_K`에 절점 왼쪽 온도를 지정하면 구간 내에서는 그 온도가 일정하다고 해석한다. 모든 구간에 온도를 지정하고 `interval_temperature_profile_reviewed=true`로 mapping을 검토해야 한다. 온도가 기준 `temperature_K`와 달라지면 기준온도·별도 활성화에너지·유효 온도 범위 및 Arrhenius review가 필요하고, 각 interval 온도는 support 안이어야 한다. 모델은 구간별로 두 effective rate를 재평가하며 온도 자체를 구간 사이에서 보간하지 않는다.

## 선택적 온도 보정

속도상수는 기존처럼 `temperature_K`에서 유효한 caller 입력으로 줄 수 있다. 기준온도 자료를 재사용하려면 두 속도에 각각 활성화에너지를 제공하고 `rate_reference_temperature_K` 및 `minimum_rate_valid_temperature_K`/`maximum_rate_valid_temperature_K`를 설정한다. 두 속도는 아래 Arrhenius factor로 target temperature에 환산한다.

```text
k(T) = k(Tref) * exp[-Ea/R * (1/T - 1/Tref)]
```

Target/reference temperature가 선언 support 안에 있어야 하며 `arrhenius_temperature_scaling_reviewed`와 기존 rate/temperature review가 필요하다. 한 방향의 활성화에너지만 주는 경우는 허용하지 않는다. 수치 overflow/underflow는 범위 밖 상태로 닫는다. 이 계산은 사용자가 준 경험 계수의 온도 scaling이며 kinetics를 데이터에서 추정하거나 universal한 corrosion/scale 반응을 의미하지 않는다.

결과에는 원래 참조 계수, 적용 온도에서의 effective rate 상수, support와 rate-scaling 정책, 입력 전체 digest를 남긴다. Arrhenius scaling을 선택하지 않으면 기존 rate constants는 선언된 `temperature_K`의 계수로 해석된다. 합성 배선 입력은 `examples/model_inputs.json`의 `chemistry.caller_scale_coverage_kinetics`다. 수치 실행과 계수 자격화는 별도 작업이다.
