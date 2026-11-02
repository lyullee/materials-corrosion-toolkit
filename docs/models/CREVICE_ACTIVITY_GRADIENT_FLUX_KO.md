# 간극 활동도 기울기 보정 영전류 이온 플럭스

## 용도

`integration.crevice_activity_gradient_nernst_planck_flux_1d`는 사용자가 지정한 한 면의 좌우 농도와 단일 이온 활동도계수, 확산계수 및 유속으로 종별 몰 플럭스와 무차원 전위 기울기를 계산한다. 전위 기울기는 대류를 포함한 전하 플럭스 합이 0이 되도록 대수적으로 닫는다.

종 (i)의 면 플럭스는 다음 이산식으로 평가한다.

\[
J_i=-D_i\left[\frac{c_{i,R}-c_{i,L}}{\Delta x}
+\bar c_i\frac{\ln\gamma_{i,R}-\ln\gamma_{i,L}}{\Delta x}
+z_i\bar c_i\frac{\Delta\psi}{\Delta x}\right]+v c_{i,upwind}.
\]

여기서 ψ는 열전압으로 나눈 무차원 전위다. 코드가 활동도계수나 열역학 모델을 생성하지 않는다. caller는 각 좌우 상태에서 농도와 감마의 표준상태·단일이온 관례를 정하고 근거와 적용범위를 제공해야 한다.

## API

```python
from matintegrity.crevice_activity_gradient_flux import (
    CreviceActivityGradientFluxRequest,
    CreviceActivityGradientSpecies,
    evaluate_crevice_activity_gradient_flux,
)

request = CreviceActivityGradientFluxRequest(
    assessment_id="screen-01", asset_id="asset-01", physical_scope_id="crevice-A",
    face_id="face-3", face_distance_m=1e-4, axial_velocity_m_s=0.0,
    species=(...), provider_id="activity-provider", provider_revision="rev-1",
    provider_evidence=(...), rights_evidence=(...),
    activity_standard_state_and_single_ion_convention_reviewed=True,
    activity_gradient_thermodynamic_consistency_reviewed=True,
    diffusivity_and_face_mapping_reviewed=True,
    local_electroneutrality_and_zero_current_reviewed=True,
    computational_use_authorized=True,
)
result = evaluate_crevice_activity_gradient_flux(request)
```

입력 종은 양·음 전하 종을 포함해야 하며 양쪽 상태 각각 전기중성이어야 한다. 수송률은 모든 종에 동일한 방향의 면 유속을 쓰고, 대류항은 유속 부호에 맞춰 상류 농도를 고른다. 감마는 양수여야 하며 기울기는 좌우 γ의 로그 차분으로 구성한다. 출력에는 종별 플럭스, 전위 기울기, 전류 잔차와 입력 digest가 포함된다.

## 경계와 제한

- 이 계산기는 한 면의 국소 flux law이며 공간 적분기나 간극 전체 수송해석기가 아니다.
- 조화평균, 활동도 법칙 선택, 단일 이온 감마의 측정 가능성, 농도 표준상태 변환은 자동 추론하지 않는다. 현재는 산술 평균 농도와 로그 감마 차분을 사용한다.
- 영전류 폐쇄는 회로가 강제하는 전류나 전하 축적을 다루지 않는다. 적용 대상이 국부 전기중성·영전류 조건을 만족하는지 사용자가 검토해야 한다.
- 반응, 산염기/착물 speciation, 고체상 선택, 석출·용해, 벽 반응, 부식률, 수명, 위험확률, 합격 판정을 계산하지 않는다.
- 출력의 작은 전류 잔차는 식의 대수적 폐쇄를 나타낼 뿐 실험 검증이나 모델 자격인정이 아니다.
