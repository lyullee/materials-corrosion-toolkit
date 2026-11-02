# 시편별 부식속도 표본 요약

`corrosion.rate_sample_summary`는 사용자가 검토해 공급한 **시편별 단일 균일손실 속도 요약값**을 동일 재료·시험 조건·방법·출처 그룹 안에서 요약한다. 속도는 SI `m/s`로 입력한다. 각 행에는 observation ID와 physical specimen ID가 필요하고 한 시편은 한 번만 나타날 수 있다. 조건이 다르거나 출처 그룹이 다르면 별도 실행으로 나눈다.

기본 분위수는 0.25, 0.5, 0.75이며 호출자가 `[0,1]` 범위의 오름차순 확률 목록으로 바꿀 수 있다. NumPy의 선형 분위수 정의를 고정해 사용하고 입력 순서대로 확률·속도 쌍을 반환한다. 결과에는 전체 시편 및 관측 ID, 표본 수, 최솟값·최댓값, 조건 서명과 digest, 선택한 분위수 확률을 담는다.

측정불확도가 있으면 각 `CorrosionRateObservation`에 `rate_standard_uncertainty_m_s`와 근거 basis를 둔다. 계산은 arithmetic mean, between-specimen sample SD와 측정 표준불확도를 분리한다. 시편 간 계측오차 의존성을 알 때만 `measurement_error_covariance_m_s2`에 관측 입력 순서와 같은 N×N 공분산 행렬을 전달한다. 대각값은 각 시편 표준불확도의 제곱과 일치해야 하며 행렬은 대칭 PSD여야 한다. 그때만 균등 가중 산술평균의 계측 표준불확도 `sqrt(1ᵀΣ1)/N`을 반환한다. 행별 오차 또는 평균의 계측 불확도는 경험 분위수와 sample SD에 합쳐지지 않는다. 이 평균의 계측 표준불확도는 표본 평균의 신뢰구간이나 예측구간도 아니다.

이 계약은 [범용 CSV/JSONL importer](TABULAR_CONTRACT_IMPORT_KO.md)의 `examples/corrosion_rate_sample_import_profile.json`으로 그룹 단위에서 바로 가져올 수 있다. JSONL 한 행이 한 material·condition·method·source 그룹의 완성된 표본이어야 한다. 합성 예시는 `examples/corrosion_rate_samples.synthetic.jsonl`과 import helper에서 확인한다. CSV는 `examples/corrosion_rate_observation_csv_profile.json`으로 시편당 하나의 검토된 관측 행을 가져오고, 공분산과 그룹을 검토한 뒤 집계 계약을 구성한다.

```python
from matintegrity.models.corrosion import CorrosionRateSampleSummary
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

sample = CorrosionRateSampleSummary(
    observations=[
        {
            "observation_id": "coupon-01-rate",
            "physical_specimen_id": "coupon-01",
            "material_id": "alloy-X",
            "rate_m_s": 2.0e-9,
            "condition_signature": {"temperature_K": 333.15, "chloride_mol_L": 0.05},
            "condition_group_id": "test-condition-01",
            "source_group_id": "campaign-01",
            "measurement_method": "weight_loss",
        },
        {
            "observation_id": "coupon-02-rate",
            "physical_specimen_id": "coupon-02",
            "material_id": "alloy-X",
            "rate_m_s": 2.7e-9,
            "condition_signature": {"temperature_K": 333.15, "chloride_mol_L": 0.05},
            "condition_group_id": "test-condition-01",
            "source_group_id": "campaign-01",
            "measurement_method": "weight_loss",
        },
    ],
    quantile_probabilities=[0.1, 0.5, 0.9],
)
result = default_registry().run(
    "corrosion.rate_sample_summary",
    sample,
    RunContext(asset_id="loop-01", location_id="coupon-rack", time_basis="168 h exposure"),
)
```

이 계산은 독립성·측정오차·표본 대표성을 추정하지 않는다. 분위수는 신뢰구간이나 예측구간이 아니며, 부식 기구·다른 조건으로의 전이·수명·합격 또는 고장확률을 나타내지 않는다. 한 물리 시편에 여러 위치나 반복 측정이 있으면 사용자가 정당화된 방식으로 시편 수준 요약을 먼저 만들고 원 측정 및 요약방법의 계보를 별도 보존해야 한다. 검증 전에는 중복 측정행을 독립 시편처럼 넣지 않는다.

## 검증 상태

예정된 검증은 표본 분위수의 독립 계산값, 사용자 지정 분위수, 단일 시편·영 분산 경계, 중복 ID, 조건·재료·방법·출처 그룹 혼합 거부, 사용자 cross-specimen covariance로 산출한 평균 표준불확도와 독립적인 표본 SD, 비대칭·비PSD covariance 거부 및 레지스트리 API 계약을 다룬다. 관련 작업은 batch69에 등록했으며 누리온 실행 전에는 검증 완료로 간주하지 않는다.
