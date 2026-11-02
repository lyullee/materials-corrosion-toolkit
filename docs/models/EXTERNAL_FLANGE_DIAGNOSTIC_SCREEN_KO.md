# 외부 FE 결과 진단 지표의 caller 기준 스크리닝

`ExternalFlangeDiagnosticScreenRequest`는 `StructuralProviderResultReceipt` 안에 고정된 equilibrium, convergence, uncertainty 또는 verification 진단값을 사용자가 작성한 한계와 비교합니다. 기존 외부 flange compliance receipt의 행렬 축약과 병행할 수 있는 진단 근거 화면입니다.

## 판정식

각 기준은 정확히 하나의 진단 ID, 범주, 지표 ID·정의 및 단위와 일치해야 합니다. 검토자가 지표 의미와 불확실성 비교 가능성을 확인한 뒤에만 다음 값을 산출합니다.

```text
screen_value = abs(provider_value) + provider_expanded_uncertainty
pass when screen_value <= caller_limit
```

한계와 증거는 호출자가 제공합니다. 패키지에는 solver tolerance, 코드 허용값, 수렴 적합성 규칙을 내장하지 않습니다. `needs_data`는 지표 부재·미보고·검토 누락을 나타내고, `out_of_scope`는 계약/단위 불일치나 한계 초과를 나타냅니다.

## 연결 경계

외부 solver가 force residual 또는 displacement correction을 `StructuralDiagnosticEvidence`로 기록하면 호출자는 정확한 정의·단위와 승인한 threshold를 이 API에 연결할 수 있습니다. 결과에는 receipt payload digest와 각 provider 진단 record digest가 남습니다. 기본 receipt contract는 payload digest도 검증합니다.

이 화면은 FE 결과를 재실행하거나 행렬을 변경하지 않고, 보고된 진단값의 실제 측정·수렴·정확도를 보증하지 않습니다. 통과는 solver qualification, mesh convergence, gasket sealing 또는 설계 승인과 다릅니다. 공급자별 parser와 실제 교환 fixture는 별도 구현·검증 대상입니다.
