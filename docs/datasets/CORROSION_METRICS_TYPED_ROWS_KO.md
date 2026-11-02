# Corrosion Resistant Alloy Metrics typed row API

## 출처와 권리 범위

- Dataset ID: `corrosion-resistant-alloy-metrics`
- Figshare v2 DOI: `10.6084/m9.figshare.13038257.v2`
- Official record: https://figshare.com/articles/dataset/Electrochemical_Metrics_for_Corrosion_Resistant_Alloys/13038257
- Catalog rights review: CC BY 4.0 compilation license, checked `2026-10-27`
- Model ID: `data.figshare_corrosion_alloy_metrics_typed_rows`
- Source ID: `figshare_corrosion_alloy_metrics_typed_rows`
- Local workbook: `data/raw/corrosion-resistant-alloy-metrics/CRA_database_Scientific_Data_Publication_12102020.xlsx`
- Workbook size: 305,468 bytes
- Publisher MD5: `719900ece651461def03a2cb54a33b33`
- Acquired SHA-256: `d0ce5e9c4b42e0b5a20dbd5c4896791703c5f433ae19bc032674d5848d9d1438`

이 API는 기존 `corrosion_metrics_data.read_corrosion_alloy_metrics` parser를 재사용하고 호출 전에 파일명·크기·publisher MD5·acquisition SHA-256을 확인한다. 카탈로그가 확인한 CC BY 4.0은 compilation에 대한 것이다. 81개 underlying publication의 point observation redistribution rights는 아직 unresolved이며, row contract와 모든 audit에서 그 상태를 고정해서 기록한다. 계산 또는 row access는 `local_only`이고, 원 workbook/point rows는 public package로 복사되지 않는다. Caller attribution은 compilation DOI를 대상으로 한다.

## Python API

- `CorrosionMetricsReadAuthorization`: dataset DOI, compilation license scope, attribution, caller computational-use 승인, local-only 승인
- `CorrosionMetricObservationRow`: 기존 parser의 long-form row와 source identity·unit·censoring·source citation·Evidence·digest lineage
- `iter_corrosion_metric_observation_rows(path, authorization=...)`: parser가 정한 sheet/row/metric 순서대로 local typed rows 순회
- `CorrosionMetricsArchiveAuditRequest`: metadata-only audit 입력
- `audit_corrosion_metrics_workbook(request)`: source pin, row count와 rights metadata 반환; point values 및 local path는 숨김
- `specifications()`: metadata audit ModelSpec `data.figshare_corrosion_alloy_metrics_typed_rows`

## 원행 및 단위 보존

`source_order`는 parser의 기존 long-form 출력에서 0부터 증가한다. 각 row의 `source_sheet`와 1-based `provider_source_row`는 원 workbook 표의 위치를 나타내며, `source_number` 및 parser source observation ID도 유지한다. 한 provider row가 여러 metric/statistic으로 확장된 경우 각 metric record는 서로 다른 `observation_id`로 남긴다.

`raw_value`, `value_status`, `qualifier`, `reported_value`, `source_unit`, parser가 이미 만든 `normalized_value`/`normalized_unit`, potential reference, raw/normalized composition, test conditions, cited literature reference fields를 보존한다. Reader wrapper는 별도의 통계·순위·물리 모델을 적용하지 않는다. Composition/condition fields의 결측은 결측으로 유지한다. 각 typed row는 source workbook SHA-256, publisher MD5, caller authorization digest, CC BY compilation citation과 canonical row SHA-256을 갖는다.

## 해석 및 배포 한계

이 compilation은 서로 다른 pitting/repassivation/crevice potentials, critical temperatures, corrosion currents/rates와 시험조건을 함께 모은다. 그러므로 metric endpoints와 units를 구분한다. underlying observation rights가 출처별로 해소되지 않아 pointwise rows는 local-only로 취급한다. `physical_specimen_id`는 제공되지 않으며 각 row가 독립 시편임을 뜻하지 않는다. API는 material ranking, test validity, design acceptance, transferability 또는 failure probability를 도출하지 않는다.
