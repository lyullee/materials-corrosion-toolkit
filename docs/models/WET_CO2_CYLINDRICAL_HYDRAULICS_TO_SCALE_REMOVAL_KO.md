# 원통형 hydraulics에서 scale 제거 전단 schedule로 전달

## 목적/API

`integration.wet_co2_cylindrical_hydraulics_to_scale_removal`은 원통형 정상 hydraulics 계산의 wall shear 결과를 기존 shear-limited scale removal 요청에 연결한다. 새 역학 상관식을 도입하지 않으며 caller가 만든 detachment threshold, 속도계수, 지수와 그 calibration digest는 바꾸지 않는다.

- 요청: `WetCo2CylindricalHydraulicsToScaleRemoval`
- 평가: `evaluate_wet_co2_cylindrical_hydraulics_to_scale_removal`
- 명세: `specifications()`

입력 hydraulics 결과는 `integration.wet_co2_cylindrical_steady_hydraulics`의 계산 완료 결과여야 하고, 정확한 결과 hash가 `Evidence`에 연결되어야 한다. `assessment_id`, asset/location, 계산 geometry 결과 digest와 시간 knot가 shear-removal 요청과 정확히 일치해야 한다. caller는 같은 범위 및 inner wetted-area basis임을 확인한다.

## 매핑 규칙

shear-removal contract는 비음수 응력을 받으므로 adapter는 hydraulics 결과의 `wall_shear_stress_magnitude_Pa` 필드만 전달한다. signed wall shear는 provenance output에 그대로 저장하고, 제거량 계산 입력으로 보내지 않는다. 시간점·단위·숫자 크기는 변환하지 않는다. 새 `WetCo2ScaleShearKnot`마다 source hydraulic result digest와 mapped knot digest를 기록한다. 결과 내부에서 기존 shear-removal evaluator를 실행하므로 호출자는 완성된 scale-removal 결과와 매핑 lineage를 한 응답으로 얻는다.

## 한계 및 계보

source IDs: `caller_cylindrical_steady_hydraulics_result`, `caller_calibrated_cylindrical_scale_shear_removal_request`. hydraulic 결과의 signed shear와 magnitude 및 상위 결과 해시를 보존한다. adapter가 사용하는 입력 표면적 기준이 맞는지 caller review가 필요하다. 값이 어떤 부식/scale 계면에서 발생했는지 adapter가 자동 판단하지 않는다. 계산은 별도의 steady 단상 hydraulics 가정 및 caller 보정 shear 제거 법칙의 한계를 그대로 물려받는다. 이는 계면 부착력, 박리 또는 erosion의 검증을 추가하지 않는다.

코드와 문서만 추가했으며 테스트/패키징/HPC 검증은 실행하지 않았다. 향후 검증은 scope/geometry/time 불일치 거부, shear magnitude와 signed lineage 보존, calibration record digest 불변, zero/reversal flow에서 제거 schedule 동작, Evidence/hash 위변조 차단, nested removal 결과의 상태 전달을 확인해야 한다.
