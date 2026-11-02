# 코드 범위 추적 상태

## 추적 커버리지

2026-11-01 재생성 결과, 101개 범위 행 모두가 소스 경로와 evidence 경로에 연결되고 각 경로의 파일 존재와 Python AST 파싱을 확인했다. 정적 추적은 **101/101행 (100.0%)**, **482/482 경로 현존·파싱**, **605/605 구성요소 매핑**, 명시 심볼 불일치 0건이다. 빈 evidence 경로가 있던 `structural.strain_life`는 선언된 구현 소스 두 경로를 직접 근거로 연결했다. 세부 필드와 source hash는 `data/catalogs/implementation_scope_audit.json`의 `trace_coverage`, `source_path_audit`, `code_symbol_evidence_audit`에 있다.

이 지표는 **코드 위치 추적률**이다. API가 실행됐는지, 수치 계산이 맞는지, 전체 물리가 구현됐는지, 재료/절차가 자격화됐는지를 나타내지 않는다. 별도 구현 분류에는 현재 `code_incomplete` 범위 1개(`degradation.crevice_chemistry`)가 남아 있다. 따라서 구현 범위의 100% 완료를 뜻하지 않는다.

## 남은 코드 구현 범위

`degradation.crevice_chemistry`의 현행 잔여 코드는 다음 세 가지다.

1. 고체 충전으로 변화하는 cell volume/aperture와 압력 구동 transient momentum·반응수송을 한 보존 체계에서 결합하고, 경계에서 밀려난 액체와 성분을 닫는다. `integration.crevice_moving_volume_liquid_continuity`는 caller aperture와 경계 유량에서 interval-mean 체적 연속을 닫고, `corrosion.crevice_moving_volume_hydraulic_history`는 그 부피율과 caller pressure를 reduced series momentum ODE에 넣어 면별 유량을 산출한다. species/component advection, deposit-to-aperture feedback, chemistry와 단일 BDF stage state는 아직 결합되지 않았다.
2. 전극 전위, double-layer charge/capacitance, Faradaic branch를 공간 component BDF와 함께 풀어 `I_total = I_F + dQ/dt`를 만족시킨다. `integration.crevice_dynamic_double_layer_faradaic_history`는 이 전류식을 독립 lumped cell별로 BDF 적분하지만 electrolyte ohmic 전위 및 component transport state에는 아직 연성되지 않았다.
3. seed threshold와 precipitation/dissolution kinetics를 cellwise spatial component BDF trial stages 안에 넣는다. 현재 API는 각 BDF interval이 끝난 뒤 kinetics를 적용하는 연산자 분할이다.

추가로 caller-reviewed reaction/phase candidate 계산과 caller-calibrated wall-flux 법칙은 존재하지만, 자동 thermochemical phase selection, procedure qualification, 독립 물리 검증은 별도 근거와 검증 과제로 남는다.

## 다시 생성하기

```powershell
.venv\Scripts\python.exe scripts\audit_partial_scope_sources.py
.venv\Scripts\python.exe scripts\build_implementation_backlog.py
```

두 명령은 정적 파일/AST/카탈로그 추적 문서를 갱신한다. 수치 모델 테스트나 qualification 시험은 수행하지 않는다.
