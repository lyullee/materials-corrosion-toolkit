# 재료별 부식속도 비교

`corrosion.material_rate_contrast`는 호출자가 공급한 두 균일 부식속도를 비교한다. 두 속도와 부호를 보존한 차이, 비율, 로그 비율, 재료 ID, 조건 그룹·출처 그룹, 입력 조건 서명의 digest를 반환한다. 속도 단위는 SI `m/s`이며 음수가 아니어야 한다. 기준 속도가 0이면 비율은 `null`, 분자 속도가 0이면 로그 비율은 `null`로 둔다.

```python
from matintegrity import evaluate
from matintegrity.contracts import RunContext

result = evaluate(
    "corrosion.material_rate_contrast",
    {
        "comparison_id": "temperature-60-C",
        "numerator_material_id": "CT110-weld-metal",
        "reference_material_id": "CT110-base-metal",
        "numerator_rate_m_s": 0.8216 * 1e-3 / (365.25 * 24 * 60 * 60),
        "reference_rate_m_s": 0.4166 * 1e-3 / (365.25 * 24 * 60 * 60),
        "condition_signature": {
            "temperature_C": 60,
            "co2_partial_pressure_MPa": 0.3,
            "total_pressure_MPa": 4,
            "pH": 5.6,
            "exposure_h": 96,
        },
        "condition_group_id": "temperature_sweep_co2_0.3_mpa",
        "source_group_id": "doi:10.1371/journal.pone.0244237#weight-loss-corrosion-tests",
        "measurement_method": "weight_loss",
    },
    RunContext(asset_id="CT110-study", location_id="60-C-condition", time_basis="96 h exposure"),
)
```

## 공개 실험 관측 예제

`validation/ct110_weld_corrosion_rates.json`(설치본: `matintegrity/catalog_data/ct110_weld_corrosion_rates.json`)의 예제 관측값은 Liu 외(2021), DOI `10.1371/journal.pone.0244237`의 CC BY 4.0 보충자료에서 왔다. 온도 조건 3개와 CO₂ 분압 조건 3개에서 각각 용접금속과 모재의 부식속도를 제공한다. JSON은 출처를 표시하고 원본 mm/year와 Julian year 기준으로 변환한 SI m/s를 함께 보존한다. 원본 spreadsheet는 로컬 `data/raw/`에 두며 패키지 빌드에는 넣지 않는다. `scripts/inspect_ct_weld_corrosion_rates.py`는 로컬 원본의 제공자 MD5·축 조건·수치와 공개 fixture를 대조한다.

연구에는 CT110 제품과 단일 시험 출처가 보고되지만 보충자료에는 실제 coupon ID, 반복 수, 속도의 불확실성이 없다. 따라서 여섯 행은 독립적인 재료 자격 데이터 여섯 개가 아니라 **하나의 연구 사례**이며, 다른 재료나 조건에 전이 가능한 용접부 배수를 만들 근거가 아니다. 90 °C 온도 사례에서 정밀 속도값의 비는 약 1.249이며, 논문에 보고된 소수 첫째 자리 비율 1.2와 일치한다.

설치된 자료는 `matintegrity.ct110_data.read_ct110_weld_corrosion_dataset()`로 읽는다. 반환 계약은 JSON schema를 확인하고 제공자 파일 해시, attribution, 라이선스, 조건, 독립성 제한을 함께 보존한다. `dataset.contrast_input("temperature-60-C")`는 해당 관측을 `MaterialCorrosionRateContrast` 입력으로 바꾼다. 모르는 비교 ID는 오류로 반환하며 다른 행을 대신 선택하지 않는다. 전체 실행 예제는 `examples/ct110_weld_corrosion_data.py`에 있다.

모델은 입력값에 대한 산술만 수행한다. 노출시간, 수질, 재료 상태, 용접절차, 면적, 측정법이 일치하는지는 확인하지 않는다. 산출 비율은 기술 통계이며 인과적인 용접 효과, 기구 기반 부식 예측, 설계 수용 판정, 잔여수명 또는 확률이 아니다. 다른 조건 그룹의 결과를 결합하거나 신뢰성·FTA 모듈로 넘기기 전에 출처의 시험 조건과 조건 서명을 검토해야 한다.

## Rights and reuse

두 보충자료는 CC BY 4.0 라이선스를 표시한다. 공개 재사용 시 저자 표시, DOI, 라이선스 링크와 단위 변환 정보를 유지해야 한다. 데이터셋 라이선스는 인용하지 않은 별도 문헌의 권리까지 허가하지 않는다. 원본 workbook과 비공개 근거는 배포물에서 제외한다. 프로젝트는 출처와 변환 기록을 남기지만 후속 이용에 대한 법률 보증을 제공하지 않는다.
