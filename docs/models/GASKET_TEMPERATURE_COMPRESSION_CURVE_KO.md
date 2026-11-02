# 측정 온도 사이 가스켓 압축 응답 곡선 전달

## 목적

`fabrication.gasket_temperature_compression_curve_transfer`는 동일한 specimen, 재료 조건, compression loading branch와 변형률 knot에서 얻은 두 caller 측정 응력–변형률 곡선을 사용해 bracket 내부 온도의 준정적 압축 곡선을 계산합니다. 계산된 점에는 caller 면적과 초기 두께를 적용하여 조립 해석에 넣을 수 있는 공칭 force–compression 변위 curve도 함께 반환합니다.

## 계산

strain grid가 정확히 일치하는 두 온도 곡선에 대해 각 strain knot에서 stress를 온도에 대해 선형 보간합니다.

```text
fraction = (T_target - T_low) / (T_high - T_low)
stress(T_target, ε_i) = stress_low(ε_i) + fraction * [stress_high(ε_i) - stress_low(ε_i)]
force_i = stress_i * caller_loaded_area
compression_displacement_i = ε_i * caller_initial_thickness
```

응력–변형률 사이의 하중 일은 선분별 trapezoidal rule로 누적합니다. interval 접선계수와 secant 계수는 응답 curve 기울기 요약입니다. 입력곡선은 compression strain/stress가 증가하는 측정 loading branch이어야 합니다.

## Caller 입력과 검토 사항

- 동일 시험 specimen·material condition·loading branch를 가진 낮은 온도 및 높은 온도 측정곡선
- 두 곡선에서 동일하고 증가 순서인 strain knot와 각 곡선의 공급자·revision·record ID·digest·Evidence
- 목표온도, 초기 두께 및 유효 압축 면적을 결합한 별도 geometry record와 Evidence
- 두 온도 사이에서 응력을 선형 보간한다는 가정, 온도 bracket의 재료 조건 일치, 시험 loading path 일치와 사용 권한 검토

목표 온도는 측정 두 온도 범위 내부에 있어야 하며 strain grid가 다르면 자동 재격자화를 수행하지 않습니다. 점 사이의 stress–strain 응답은 이 transfer 단계에서 새로 곡선 맞춤하지 않습니다.

## 적용 경계

- 온도 사이 선형 관계는 caller가 검토하는 보간 규칙입니다. 일반적인 엘라스토머·섬유 가스켓 물리법칙으로 가정하지 않습니다.
- 온도 범위 밖 외삽, 온도 의존 unloading/reloading, 히스테리시스, creep/relaxation, 압축 set, 열팽창, 두께·접촉면적 변화와 손상 진화를 계산하지 않습니다.
- 하나의 측정조건에서 여러 target-temperature curve를 만든 결과는 독립값이 아니며 보정오차/시험 반복 변동을 전파하지 않습니다.
- 계산 curve는 이후의 assembly/contact solver에서 쓸 후보 데이터입니다. 자동으로 적합한 gasket property, leakage limit, seal acceptance 또는 qualification이 되지 않습니다.

## 독립 참고자료

- “Development of Test Equipment for Measuring Compression Characteristics of Sheet Gaskets at Elevated Temperature,” *Journal of High Pressure Institute of Japan* 46(6) (2008). [DOI: 10.11181/hpi.46.363](https://doi.org/10.11181/hpi.46.363)
- H. Willis and A. Fatemi, “An Experimental Investigation of Compressive Behavior of a Gasket Material,” SAE Technical Paper 930119 (1993). [DOI: 10.4271/930119](https://doi.org/10.4271/930119)

문헌은 가스켓 압축 응답의 시험 측정 배경만 뒷받침합니다. 문헌에서 계수나 곡선을 가져오지 않았으며, 각 curve와 온도 사이 전달 규칙은 caller 자료 및 검토에 의존합니다.

## API와 source ID

- Model ID: `fabrication.gasket_temperature_compression_curve_transfer`
- Schema: `matintegrity.gasket_temperature_compression_curve_transfer.v1`
- Evaluator: `evaluate_gasket_temperature_compression_curve_transfer(request)`
- Source IDs: `caller_gasket_temperature_bracket_loading_curves`, `caller_gasket_specimen_geometry_and_condition`, `linear_temperature_interpolation_at_fixed_compression_strain`, `quasi_static_gasket_force_compression_curve_transfer`
