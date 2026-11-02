# 호출자 다축 경로 손상 provider

`evaluate_caller_multiaxial_damage`는 시간 이력이 있는 3D stress/strain tensor cycle에 사용자 제공 순간 손상률을 적분한다. Tensor 성분 순서는 `[xx, yy, zz, xy, yz, zx]`이다. 호출자는 `CallerMultiaxialDamageRequest`에 cycle별 유일 ID, 표본 이력과 SHA-256, material condition, calibration identity, provider revision/configuration digest, tensor/shear convention, 보간 방식, 허용 closure 오차 및 적분 오차·작업 상한을 선언한다.

## Provider callback

Callback signature:

```python
damage_rate(time_s, stress6_Pa, strain6, stress_rate6_Pa_s, strain_rate6_s_inv, context) -> damage_rate_s_inv
```

Synthetic API wiring example: [`examples/multiaxial_damage_provider.py`](../examples/multiaxial_damage_provider.py). Its constant-rate callback demonstrates only the call shape and must not be used as a fatigue material law or validation evidence.

`context`는 분석, cycle, 재료 상태, 위치, calibration digest, shear convention 및 경로 재구성 식별자를 담은 읽기 전용 mapping이다. Callback 함수에는 다음 속성이 요청값과 정확히 일치해야 한다.

```python
damage_rate.provider_id
damage_rate.revision
damage_rate.configuration_sha256
```

호출자는 callback의 재료 적용성, 배포권, 결정성, memoryless rate 해석을 확인해야 한다. 반환률은 매 평가점에서 유한한 0 이상 값이어야 하며 단위는 `s^-1`이다. 누적 internal state를 갱신하는 callback은 이 quadrature adapter와 호환되지 않는다.

## 적분 동작

각 인접 표본 구간을 따로 평가한다. piecewise-linear 재구성에서는 구간별 상수 시간 미분을 사용한다. cubic-Hermite는 cycle마다 호출자 제공 endpoint tensor 미분을 사용한다. `piecewise_pchip`은 SciPy가 아닌 내부 Fritsch–Butland knot 기울기 재구성을 사용하고, `piecewise_periodic_cubic_spline`은 선택형 SciPy 의존성으로 주기 spline과 그 미분을 callback에 전달한다. 주기 spline은 입력 양 끝 응력·변형률이 정확히 같아야 하고 `periodic_spline_reviewed=True` 및 응력률·변형률률 폐합 허용치를 요구한다. 모든 cubic 재구성은 주기 경계의 계산된 응력·변형률 기울기 차이를 caller 허용치와 비교한다. 각 구간의 시간 적분에 composite Gauss-Legendre quadrature를 쓰며 panel을 2배씩 늘려 연속 추정치 차이가 caller absolute-plus-relative tolerance 아래인지 확인한다. 요청에는 최대 provider 평가 수가 포함되며, 기본 2,000,000회·최대 20,000,000회 한도를 넘기기 전에 중단한다. 허용 panel 수 안에 수렴하지 않거나 provider 값, 경계 closure 또는 aggregate가 지원 범위를 벗어나면 전체 damage aggregate를 내지 않고 실패 cycle을 기록한다.

## 책임과 한계

이 API는 다축 피로 법칙이나 계수를 내장하지 않는다. Provider가 정의하는 순간 손상률, calibration, 단위의 물리적 타당성, 적용성 및 cycle separation은 독립적으로 근거를 갖춰야 한다. Cycle 간 sequence interaction, 기억 효과, 상태변수 진화, cycle 추출/rainflow, 규격상 합격 판정과 실제 부품 qualification은 제공하지 않는다. 적분 결과의 status가 `computed`여도 사용자가 검토한 provider 계산을 뜻하며, 보편적 fatigue damage 법칙 또는 실험 검증을 뜻하지 않는다.

실행 예와 계산 회귀는 후속 검증 단계에 둔다.
