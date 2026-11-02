# 가스켓 누설률 압력구간 포락선

`fabrication.gasket_calibrated_leakage_rate_envelope`는 한 시각의 접촉 절점별 평균 접촉압력·차압 구간을 caller 보정 누설 flux 표에 적용해 면적가중 총 누설률의 최솟값과 최댓값을 계산한다. `GasketLeakageHistory`가 각 절점의 대표값 이력을 적분하는 동안, 이 API는 입력 압력의 구간 범위가 결과에 주는 결정론적 상·하한을 제공한다.

## 계산법

각 표 셀에서 bilinear interpolation은 `q(u,v)=a+bu+cv+duv` 꼴이다. 내부 stationary point가 존재하더라도 Hessian은 indefinite이므로 strict interior maximum/minimum은 될 수 없다. 셀 경계에서는 함수가 선형이어서 극값은 셀 모서리에서 발생한다. 입력 직사각형을 보정표의 압력·차압 knot로 자르고 각 subcell corner를 평가하면 해당 입력 구간에 대한 flux extrema를 정확히 찾는다. node별 면적을 곱한 bound를 합산한다.

입력 각 node의 접촉압력 구간과 차압 구간은 **서로 독립**인 직사각형 지원범위로 해석한다. 따라서 node별 bound를 독립적으로 더한 총 bound는 이 계약의 uncertainty set에 대한 exact bound다. 압력 범위를 벗어나는 외삽은 허용하지 않는다. `maximum_corner_evaluations`가 전체 node에 걸친 꼭짓점 평가 예산을 제한하며 초과 시 부분 envelope를 완결 결과로 보고하지 않는다. table은 고정된 것으로 취급한다.

## 의미와 한계

결과는 확률분포, 신뢰구간 또는 통계적 추정이 아니다. calibrated flux 표, 접촉면적, 압력 구간의 측정 불확실성은 별도 입력하지 않는다. node 간 공통 차압 상관이나 구조 solver의 접촉압력 상관을 보존하지 않으므로 각 node 구간이 실제로 동시에 가능한지 caller가 검토해야 한다. 시간이력 적분, 누설 수용기준, 씰 성능, 재료/조인트 간 calibration transfer 및 설계 자격화는 다루지 않는다.

합성 사용 예시는 [`examples/gasket_leakage_rate_envelope.py`](../examples/gasket_leakage_rate_envelope.py)다. 예시 숫자는 API 배선 전용이다.
