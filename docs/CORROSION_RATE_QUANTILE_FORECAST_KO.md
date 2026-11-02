# 표본 부식속도 분위수 기반 두께 시나리오

`corrosion.rate_quantile_forecast`는 한 출처·조건에 속한 시편별 단일 부식속도 요약값과 현재/요구 두께를 받아, 선택한 **경험 분위수 하나**를 고정 속도로 가정한 선형 잔여두께 시나리오를 계산한다. 이는 기술적 연결 편의다. 표본 분포를 운전 이력이나 미래 속도분포로 자동 외삽하지 않는다.

호출자는 `selected_quantile_level`을 표본 요약의 `quantile_probabilities` 중 하나와 정확히 일치시켜야 한다. 재료 상태 호환성, 시험조건에서 설비 조건으로의 전이, 고정 선형 손실 가정을 각각 검토하고 해당 검토 ID를 공급해야 실행된다. 결과는 선택 분위수, 계산에 사용한 속도, 시편·관측 ID, 검토 ID, 조건/source group 및 조건 서명 digest와 함께 기존 `corrosion.uniform_forecast`의 잔여두께·임계두께 교차시각 값을 반환한다. 기간 내 두께가 0 아래로 예측되면 기존 모델과 같이 `out_of_scope` 상태로 남긴다.

입력 표본에 쿠폰 계측 표준불확도 또는 전체 measurement-error covariance가 있으면 결과에 해당 행별 값, 평균 및 표본 산포 요약, covariance digest를 보존한다. 미래 두께의 계측·표본 불확도를 이 결정론적 분위수 시나리오에 전파하지 않는다.

```python
from matintegrity.contracts import RunContext
from matintegrity.models.corrosion import CorrosionRateQuantileForecast
from matintegrity.registry import default_registry

scenario = CorrosionRateQuantileForecast(
    sample={
        "observations": [
            {
                "observation_id": "coupon-01-rate",
                "physical_specimen_id": "coupon-01",
                "material_id": "alloy-X",
                "rate_m_s": 2.0e-9,
                "condition_signature": {"temperature_K": 333.15},
                "condition_group_id": "test-01",
                "source_group_id": "campaign-01",
                "measurement_method": "weight_loss",
            }
        ],
        "quantile_probabilities": [0.5],
    },
    selected_quantile_level=0.5,
    current_thickness_m=0.012,
    required_thickness_m=0.009,
    horizon_s=31_536_000.0,
    material_state_compatibility_reviewed=True,
    condition_transferability_reviewed=True,
    linear_loss_model_reviewed=True,
    material_state_review_id="review-material-01",
    condition_transfer_review_id="review-transfer-01",
    linear_loss_model_review_id="review-model-01",
)
result = default_registry().run(
    "corrosion.rate_quantile_forecast",
    scenario,
    RunContext(asset_id="loop-01", location_id="coupon-rack", time_basis="one-year scenario"),
)
```

분위수 수준은 신뢰수준·고장확률·FTA 기본사건 확률이 아니다. 결과는 합격판정이나 기간 최초고장 확률을 제공하지 않는다. 분위수 선택은 보수성을 자동 보증하지 않으며, 미래 운전 조건이 시험 자료와 다르면 사용자가 그 전이성 근거를 별도로 검토해야 한다. 실제 위험도/FTA 연결에는 시간 범위·사건·생존 조건을 갖춘 별도의 신뢰성 계산 결과를 사용해야 한다.

## 검증 상태

batch63은 독립 분위수 기대값, provenance 유지, 정량 분위수 선택, 전이성 review gate를 다룬다. batch69는 측정오차 공분산·표본 산포를 별개로 유지하고 시나리오가 이를 예측에 섞지 않는지 확인한다. 이 작업들은 아직 실행하지 않았다.
