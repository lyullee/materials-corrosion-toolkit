# 직접 에너지 입력과 기초 공학 계산 검증

검증일: 2026-11-01. 아래 명령은 로컬에서 22개 테스트를 통과했다.

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_direct_weld_energy.py tests/test_engineering.py tests/test_extended_physics.py::test_offset_yield_exact_intersection_and_unbracketed_status --junitxml=artifacts/validation/scope_reset_energy_engineering.xml
```

새 API `welding.measured_energy_per_length`와 `welding.power_travel_energy`는 직접 함수 및 공개 registry 경로로 호출했다. 1 kJ를 1 cm 길이에 공급하는 기준값, 동일 공정을 총에너지·출력·전압/전류·파형으로 표현했을 때의 에너지 일치, 관측구간을 같은 비율로 나눴을 때의 단위 길이 에너지 불변성을 확인했다. 음수 에너지, 영 길이/속도와 허용 범위 밖 효율은 입력 단계에서 거부했다.

기존 기초 계산의 검증에는 쿠폰 질량감소의 체적 및 연간 감육 환산, 얇은 원통 해가 두꺼운 원통 해의 극한에 접근하는 성질, 원통 표면 압력 경계와 등방 압축 극한, 기록된 인장곡선의 오프셋 교점 및 교점 부재 처리가 포함됐다. 같은 실행에는 Paris 적분, 단위 변환과 일부 신뢰성 계약의 기존 회귀 사례도 포함되어 있다. 따라서 22라는 숫자는 검증한 물리 모델 수가 아니다.

이 결과는 명시한 수학적 사례와 API 계약의 소프트웨어 검증이다. 실제 용접 열효율, 재료 데이터 적합, 시험 절차 자격화 또는 전체 모델의 실험 검증을 의미하지 않는다. 공개 저장소에서는 위 테스트와 실행 명령으로 재현할 수 있으며, 로컬 JUnit 기록은 배포 대상에서 제외하는 artifacts 경로에 저장한다.
