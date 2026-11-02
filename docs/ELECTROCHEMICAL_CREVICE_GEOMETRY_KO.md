# 전기화학 금속손실에서 틈새 간극 이력으로의 연결

`integration.electrochemical_metal_loss_to_crevice_geometry`는 계산 완료된 `integration.electrochemical_partial_current_metal_loss` 결과를 digest로 고정하고, reaction별 signed 누적 질량을 Evidence-linked 밀도로 나눈 체적으로 변환한다. 각 reaction의 체적은 입력자가 각 시간 knot마다 제공한 셀별 누적 배분율로 분배한다. 배분율은 모든 knot에서 1이어야 하며, 계산은 upstream reaction별 체적, 배분 체적 총합 및 closure residual을 기록한다. 첫 입력 source time은 초기 geometry 시각으로 삼아 elapsed time 0으로 변환한다. 시작시각이 0이 아니면 초기 형상 기준으로 시계를 옮긴다는 review가 필수이며, source/elapsed 시각 대응을 보존한다. caller aperture support 또는 finite geometry 범위를 벗어나면 `out_of_scope`와 함께 마지막으로 수용된 geometry prefix 및 최초 실패 interval을 보존한다. Prefix는 불완전 결과이므로 후속 transport campaign에서 완전한 geometry history처럼 사용할 수 없다.

## 입력과 명시적 책임

- upstream 전체 `AssessmentResult`와 SHA-256, 같은 material condition 및 asset/location/time basis
- axial 셀 폭, 초기 aperture, 횡방향 폭, reference cross-section, 활성 face 수 및 형상 자료 digest
- upstream에 포함된 모든 reaction을 대상으로 한 셀별 누적 체적 배분율. 자동 균등분배나 전류분포 추정은 하지 않는다.
- reaction-to-face 대응, 셀 배분 근거, 체적 보존, 합산 활성면적 기준, cell-center/face 대응 및 형상 가정에 대한 명시 review. 양쪽 face를 활성화하면 같은 face recession 가정도 필수다.
- aperture provider 지원 범위와 계산 사용 승인

결과는 셀 체적을 caller가 지정한 combined reactive wall area로 나눠 recession으로 만들고, 기존 `planar_slit_aperture_history` 순차 remap을 사용한다. aperture 이탈, digest 불일치, mapping 누락, 불연속 clock, 체적 보존 실패는 유효 geometry 결과로 승격하지 않는다. 성공한 각 knot은 이후 transport 재계산을 위한 geometry 상태이며, 이 API 자체는 transport를 자동 호출하지 않는다.

## 수치와 경계

시각 k, reaction r, 셀 i에서 upstream signed 질량 m, caller 밀도 rho, 배분율 f라 하면 체적은 `V[r,k] = m[r,k] / rho[r]`, 셀별 합은 `V[i,k] = sum_r(V[r,k] * f[r,i,k])`이다. 면적은 caller가 지정한 활성 face 수 Nf, 횡방향 폭 w, 셀 폭 dx를 이용해 `A[i] = Nf*w*dx[i]`로 정한다. 셀 평균 recession은 `V[i,k]/A[i]`다. 중간 knot의 국부 전류, 구간 내 moving boundary, 반응 선택도, 흐름·화학·형상의 동시 연성은 풀지 않는다.

누적 배분율은 각 knot에서 signed 순 체적을 보존하는 데 사용한다. 시간에 따라 순 질량이 상쇄될 때 gross anodic volume의 국부분포를 뜻하지 않는다. 재부착·침전·박리의 개별 공간분포가 필요하면 해당 ledger에 맞는 별도 caller law/adapter가 필요하다. 실패 시 geometry를 임의 보간하거나 구간을 자동 분할하지 않는다.

## Python API와 예제

```python
from matintegrity import evaluate

geometry = evaluate(
    "integration.electrochemical_metal_loss_to_crevice_geometry",
    request,
    run_context,
)
```

계약은 `docs/schemas/ElectrochemicalCreviceGeometryHistory.json` 및 `docs/schemas/ReactionCellVolumeAllocation.json`에서 확인한다. 합성 배선 예제 `examples/crevice_electrochemical_composition.py`가 금속손실 결과를 geometry adapter에 전달하는 형식을 보인다. 예제 숫자와 50/50 공간 분배는 합성 fixture일 뿐 사용 기본값이나 재료 데이터가 아니다.

## 구현 상태

현재 제공 범위는 코드/API·registry·schema·catalog 수준의 operator-split wiring이다. 합성 계산, 독립 수치 비교, 회귀 테스트, 실제 측정/공개 데이터 validation 및 물리 qualification은 수행되지 않았다. 공개 배포 전 caller 데이터의 사용권, 개별 reference 및 적용범위를 검토해야 한다.
