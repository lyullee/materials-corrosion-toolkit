# 전기화학 손실에서 벽두께 이력으로 연결

`integration.electrochemical_metal_loss_wall_thickness_history`는 계산된 `integration.electrochemical_partial_current_metal_loss` 결과를 digest로 고정하고, 측정 벽두께 기준선에서 공급된 구간별 금속 손실을 빼 결정론적 잔여 두께와 요구두께 margin을 만든다.

## 입력 준비

- upstream metal-loss 결과의 전체 JSON 직렬화 SHA-256을 `metal_loss_result_sha256`에 제공한다.
- `ErosionCorrosionWallThicknessBaseline` 계약으로 측정값, 요구두께, 측정시각, 자산·위치·물리범위·재료·형상 식별자와 출처 Evidence를 고정한다. baseline 시각은 첫 손실 구간 시작과 같아야 한다.
- 공통 평가 벽 면적과 유효 밀도는 사용자가 공급한다. 밀도 공급자·revision·record ID·SHA-256과 일치하는 Evidence를 연결한다.
- 모든 반응을 projection 대상에 포함한다는 검토, 같은 벽 면적의 적용성 검토, effective density의 재료 적용성, anodic-only 비상쇄 관례, 계산 사용권 review를 명시한다.

```python
from matintegrity import default_registry
from matintegrity.contracts import canonical_digest
from matintegrity.models.electrochemical_wall_thickness import ElectrochemicalWallThicknessHistory

# metal_loss_result: computed AssessmentResult from the upstream model
# wall_baseline: Evidence-linked ErosionCorrosionWallThicknessBaseline
request = ElectrochemicalWallThicknessHistory(
    assessment_id="asset-17-wall-projection-2026-01",
    metal_loss_result=metal_loss_result,
    metal_loss_result_sha256=canonical_digest(metal_loss_result.model_dump(mode="json")),
    baseline=wall_baseline,
    assessed_wall_area_m2=0.012,
    effective_density_kg_m3=7850.0,
    wall_area_relative_tolerance=0.01,
    density_provider_id="caller-material-record",
    density_provider_revision="rev-1",
    density_record_id="density-record-17",
    density_record_sha256="<64-character-record-sha256>",
    density_evidence=(density_evidence,),
    material_to_effective_density_reviewed=True,
    complete_reaction_set_reviewed=True,
    common_wall_area_mapping_reviewed=True,
    anodic_only_noncrediting_projection_reviewed=True,
    computational_use_authorized=True,
)
result = default_registry().run(
    "integration.electrochemical_metal_loss_wall_thickness_history",
    request,
    metal_loss_result.context,
)
```

## 계산 의미와 범위

각 구간에서 반응별 `anodic_mass_loss_kg`를 합산해 유효 밀도와 공통 벽 면적으로 나눈다. cathodic metal-equivalent 및 signed net mass는 손실에서 상쇄하지 않는다. baseline 이후 각 구간 손실을 차감하고 시각별 요구두께 margin을 제공한다. 요구두께를 넘는 첫 구간은 bracket만 기록하며 구간 중간 교차 시각을 보간하지 않는다.

upstream branch 면적이 공통 벽 면적과 review 허용오차 안에서 맞아야 한다. 반응별 면적이 다른 일반 형상, 국부 부식·피팅, 용접부·열영향부의 비균질 밀도, 시간 사이 전류 재구성, 구간 밖 extrapolation은 다루지 않는다. 결과는 공급된 전기화학 기간 안의 두께 장부이지 부식률 자격화, remaining-life 예측, code acceptance, 구조 신뢰도나 고장확률이 아니다. FTA 연결 시 deterministic limit-state 관측치로만 취급하고 사건확률은 별도 모듈과 근거가 필요하다.
