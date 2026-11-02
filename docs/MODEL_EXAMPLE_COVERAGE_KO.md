# 계산기 예제 커버리지

2026-10-30 정적 카탈로그 기준 registry에는 407개 계산기가 등록되어 있고 `examples/model_inputs.json`에는
400개의 standalone JSON 입력이 있다. 일부 prior-result-dependent 계산기는 Python wiring example을 제공하고,
standalone payload가 없는 항목은 model reference에서 표시한다. B-dot self-consistent speciation과 exact-knot history 입력을 이번 갱신에서 추가했다.
각 입력은 API 계약 예시이며 재료 권고값, 설비 판정 또는 실험 자격화가 아니다.

예제는 synthetic 근거와 최소 동작 계약을 보여주며 실제 설비 적합성이나 과학적 검증을 대신하지 않는다.
도메인별 테스트 fixture에서 입력을 구성해 계약 필드와 review gates를 유지하고, 실행 시 example에 선언된
asset/location/time basis를 run context에 사용한다. 모델 payload에 포함할 수 없는 context는 root-level
`run_contexts`에서 분리해 관리하고 예제 harness가 이를 `RunContext`로 전달한다. 신규 모델 추가 시 input schema,
계산 테스트, 실행 예제, context identity를 한 변경으로 유지한다. 전체 registry/example 집합 일치와 각 예제의 finite versioned result는
`tests/test_model_examples.py`에서 검사하며 실제 결과는 누리온 manifest의 pytest 작업에서 확인한다.


보조 사용 예제로 시간변화 flange compliance와 접촉전이 샘플링/재생 입력 배선(xamples/flange_time_varying_compliance.py, xamples/flange_contact_transition_sampling.py)을 제공한다. 이는 계산기별 fixture의 합성 입력을 확장하는 사용 패턴 예이며 추가 계산기 수로 세지 않는다.

stateful multiaxial damage provider 예제(`examples/stateful_multiaxial_damage.py`)는 고정 RK4와 caller-reviewed adaptive step-doubling 설정을 같은 합성 시퀀스로 구성하는 사용 예를 포함한다.
