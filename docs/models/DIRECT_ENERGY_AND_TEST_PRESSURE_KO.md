# 직접 에너지 입력과 관 시험압력

| API | 입력 | 출력 |
|---|---|---|
| `welding.measured_energy_per_length` | 측정 source energy J, 용접 길이 m, 효율 | source energy/length J/m, net heat J/m |
| `welding.power_travel_energy` | 일정 source power W, 이동속도 m/s, 효율 | source energy/length J/m, net heat J/m |
| `inspection.pipe_membrane_test_pressure` | 외경 m, 두께 m, 항복강도 Pa, 사용자 강도비와 적용 근거 | 외경 막응력 기준 차압 Pa, 사용한 응력 Pa |
| `inspection.reference_energy_mass` | 입력 에너지 J, 사용자 기준 비에너지 J/kg, 기준 ID와 에너지 의미 | 기준 질량 kg, 기준 ID와 에너지 의미 |

직접 에너지 API는 전압이나 전류를 임의로 만들어 입력할 필요가 없다. 효율을 1로 지정하면 source energy/length와 net heat가 같아진다. 파형 변화가 중요하면 `welding.waveform_energy`를 사용하고, 동일한 관측구간의 에너지와 용접 길이를 연결한다.

관 시험압력은 항복강도에 사용자 비율을 적용한 뒤 두께와 외경으로 막응력 평형을 계산한다. 형상·재료·계수 적용성을 검토하지 않으면 압력을 반환하지 않는다. 등급별 기본계수·반올림·나사 연결저항·시험 승인과 안전 절차는 자동 판단하지 않는다.

에너지 질량환산은 주어진 에너지를 사용자 기준 J/kg으로 나누는 정규화다. 내장 폭약 상수, 폭풍 효율, 과압 또는 안전거리를 적용하지 않는다. 가스 팽창 일로부터 연결할 때도 입력 에너지의 물리적 의미를 보존한다.

실행 예제는 `examples/engineering_correlations.py`에 있다. 모든 예제 파라미터는 API 연결 설명용 합성값이다. Python에서는 `registry.run(model_id, typed_request, context)`, JSON에서는 `registry.run_json(model_id, json_text, context)`를 사용한다. JSON을 단순 dict로 바꿔 strict Python 검증에 전달하는 방식과 명시적 JSON 검증을 혼용하지 않는다.
