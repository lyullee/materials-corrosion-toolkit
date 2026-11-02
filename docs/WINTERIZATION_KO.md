# 겨울철 유체 재고 온도 여유

`fabrication.winterization_inventory`는 정지 상태의 잘 섞인 유체 재고에 대해 구간별 열수지를 계산한다. 각 구간의 외기 온도, 전체 열손실 컨덕턴스, heat tracing 전력과 유효 정압비열은 입력에서 명시한다. 기존 `thermal.planar_layers`와 `thermal.cylindrical_layers`가 열저항을 공급할 수 있지만 자동 연결하거나 형상을 추정하지 않는다.

## 계산 범위

한 구간에서 입력량을 일정하게 유지하며 다음 식의 해를 사용한다.

`m cp dT/dt = Qtrace - UA (T - Tamb)`

`UA > 0`이면 지수 해를, `UA = 0`이면 선형 가열 해를 사용한다. 저장 에너지 변화, tracing 공급 에너지와 환경으로 나간 부호 있는 에너지를 함께 반환한다. 환경이 더 따뜻해 열이 유입되면 환경 열손실은 음수다. 사용자가 검토한 최소 허용온도를 처음 통과하는 시간은 동일한 구간 해에서 계산한다.

## CoolProp 조합

`thermo.winterization_inputs_from_coolprop(...)`는 각 구간의 검토 온도와 절대압에서 `Cpmass`와 phase를 조회한다. backend, CoolProp 버전·리비전, 유체, 압력, 평가온도, phase, 비열을 상태 digest에 포함한다. 계산기는 이 명시적 배열을 받아 실행되므로 이후에도 사용 물성을 재현할 수 있다.

CoolProp의 유체 상태식은 금속·단열재 물성, 열손실 컨덕턴스, heat tracing 성능 또는 보존 절차를 공급하지 않는다. 특히 이 계산기는 고체 형성, 잠열, 과냉각, 배관 내 자연대류, 유동, 반응이나 국부 냉점을 예측하지 않는다. 최소 허용온도는 동결점으로 자동 생성하지 않으며 호출자가 서비스·혼합물·운전 근거를 검토해 공급한다.

## 검증과 실행

`scripts/validate_winterization.py`는 상수 계수 닫힌해, 기준온도 통과시간, 구간 에너지 보존과 CoolProp 물 상태 조합을 검사한다. 결과는 `validation/winterization_math.json`에 기록한다. 이는 실제 설비나 절차의 검증이 아니며, 전체 회귀는 `hpc/task_manifest.json`의 누리온 작업 배열에 포함한다.
