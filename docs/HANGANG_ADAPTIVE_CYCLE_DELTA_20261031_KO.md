# Adaptive cycle-block 전용 검증 증분

합성 caller ODE와 metadata를 두 독립 작업으로 검사한다. `numeric`은 일정률·지수·이차 감쇠의 닫힌 해, DOP853 nonlinear reference와 tolerance sweep, 동일 law block 분할 및 순서 의존성, 함수 호출 예산과 accepted prefix, 최소 step에서 해결되지 않는 오차, state bound와 damage threshold bracket을 확인한다. Event bracket을 정확한 crossing이나 수명으로 승격하지 않는다.

`metadata`는 세 schema, runtime provider 의존성, ModelRegistry의 명시적 callback 주입, callback 단위 불일치·실행 중 calibration metadata 변경·extra failure key의 거부, source/parent/package metadata 일치와 source 파일 hash를 검사한다. 최소 dependency closure에서 이 ModelSpec만 등록하여 실행한다. 전체 builtin registry/전체 pytest 또는 material law calibration을 실행하지 않는다.

Snapshot에는 관련 source/core import 파일, 세 schema, 설명서, source/package catalog의 해당 row 및 capture 시점의 전체 파일 hash 선언만 넣는다. Catalog 전체와 raw/dataset/evidence는 제외한다. 결과는 수학/소프트웨어 계약 검증이며 물리적 qualification이 아니다. 고정 hash·task·stage·job ID는 `hpc-results/hangang-adaptive-cycle-*/dispatch.json`에 기록한다. 이전 job과 source snapshot을 변경하지 않는다.
