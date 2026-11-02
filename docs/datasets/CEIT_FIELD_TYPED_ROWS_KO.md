# CEIT 해안 노출 강재의 typed 관측 행 API

## Dataset 및 권리

- Dataset ID: `ceit-uniform-corrosion-field`
- Official record: https://zenodo.org/records/13897090
- DOI: `10.5281/zenodo.13897090`
- Catalog rights review: CC BY 4.0, checked `2026-10-27`
- Model ID: `data.zenodo_ceit_uniform_corrosion_field_typed_rows`
- Source ID: `zenodo_ceit_uniform_corrosion_field_typed_rows`
- Local source file: `data/raw/ceit-uniform-corrosion-field/UniformCorrosionExperiment_Ceit.json`
- Catalog MD5: `6db405ab03922aeaf5560ed634cd94df`
- Acquired source SHA-256: `87033b35f7964eb34265e6e4e5f0e1252b2214480b6f39871029811e3e3dbf1b`
- Source size: 49,918,087 bytes

이 adapter는 기존 `ultrasound_data.read_ceit_uniform_corrosion_field` parser를 재사용하고, parser를 호출하기 전에 filename·byte count·MD5·acquisition SHA-256을 모두 확인한다. 원본 JSON과 pointwise observation은 public distribution에 포함하지 않는다. `CeitFieldReadAuthorization`은 caller attribution, 계산 이용 승인, 로컬 전용 경계를 요구한다. 이 선언은 rights status의 법적 해석이나 별도 배포 권한을 대신하지 않는다.

## API

- `CeitFieldReadAuthorization`: dataset DOI/license, attribution 및 caller의 computational/local-only declaration
- `CeitFieldObservationRow`: 하나의 provider JSON observation record와 signal vectors, Evidence/digest lineage
- `iter_ceit_field_observation_rows(...)`: caller가 명시한 ToF 단위, 온도 단위, sample interval basis로 기존 parser를 호출하고 source array 순으로 typed record를 yield
- `CeitFieldArchiveAuditRequest`: metadata audit 입력
- `audit_ceit_field_archive(request)`: 경로 및 point values 없이 source digest·행 수·선택된 unit/time basis를 반환
- `specifications()`: `data.zenodo_ceit_uniform_corrosion_field_typed_rows` ModelSpec 제공

## 행 계보와 단위

Source JSON array의 0-based `source_order`와 `provider_array_index`를 그대로 보존한다. parser가 요구하는 provider timestamp는 timezone이 없는 ISO calendar time이며 시간대는 미해결로 표시한다. 비증가 timestamp, schema 불일치, 비유한 또는 길이가 부적절한 signal vector는 parser에서 거부하고 정렬·보간·행 삭제하지 않는다.

각 typed record는 source MD5/SHA-256, filename/size, `series_id`, ID fields, authorization digest, canonical observation digest, license/citation이 포함된 `Evidence`를 보존한다. signal vector는 원본 1차원 sample 순서대로 tuple에 담긴다. 별도 검토한 sample interval이 제공되지 않으면 `sample_time_s`는 `None`이다. ToF와 온도 단위가 caller에 의해 지정되지 않으면 정규화된 `tof_s` 및 kelvin 필드는 `None`이다. 그러한 선택은 digest에 포함된다.

ToF·compensated ToF·온도·battery·amplitude와 `raw`, `fil`, `cor`, `env` signal은 장치가 보고한 값으로 남는다. signal amplitude/ADC scale은 정규화된 물리 단위가 아니다. `tofref`, reference convention, sample clock 간격, 측정 footprint, wave speed, 경로 길이, calibration 및 독립 destructive thickness truth를 이 reader는 보충하지 않는다.

## 해석 한계

Provider는 한 강재 시편을 해안 근처에서 약 6개월간 관찰한 것으로 설명한다. 반복 기록은 새 시편이나 현장 모집단의 독립 표본이 아니다. 장치 ToF에서 남은 벽두께, 벽두께 손실, 부식률, 측정 불확도, remaining life 또는 failure probability를 계산하지 않는다. Provider의 134 μm/year summary도 여기서 데이터 행 또는 모델 prior로 승격하지 않는다.
