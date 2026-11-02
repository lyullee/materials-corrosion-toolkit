# Pipeline guided-wave typed sample API

## Dataset and rights

- Dataset ID: `guided-wave-pipeline-shm`
- Mendeley record: https://data.mendeley.com/datasets/ttb63krg6d/1
- DOI: `10.17632/ttb63krg6d.1`
- Catalog rights review: CC BY 4.0, checked `2026-10-27`
- Model ID: `data.mendeley_guided_wave_typed_sample_rows`
- Source ID: `mendeley_guided_wave_typed_sample_rows`
- Local archive: `data/raw/guided-wave-pipeline-shm/ttb63krg6d-1.zip`
- Pinned archive SHA-256: `cf24cb3f1bb79e7c3a37502f5f5c392b6ca8b1a0a35f6e2b04758a1ffa4340fb`
- Pinned archive size: 103,000,407 bytes

이 wrapper는 기존 `guided_wave_data.read_guided_wave_acquisition` parser를 재사용한다. parser의 pinned outer-archive digest와 bounded nested ZIP/workbook checks는 필수로 유지한다. HDF/ZIP/workbook 원자료와 pointwise rows는 public distribution에 복사하지 않는다. 호출자는 `GuidedWaveReadAuthorization`에 dataset attribution과 computational/local-only 승인을 별도로 제공한다. 이 입력은 license의 법적 해석이나 파생 row 공개 권한 판정을 대신하지 않는다.

## API

- `GuidedWaveReadAuthorization`: 고정 dataset DOI/license, attribution 및 local-only 계산 이용 선언
- `GuidedWaveSampleRow`: 하나의 frequency sheet 안에서 한 거리 측정 위치의 typed signal row
- `iter_guided_wave_sample_rows(...)`: 한 명시적 acquisition ID와 source frequency만 순서대로 순회
- `GuidedWaveArchiveAuditRequest`: metadata audit 요청
- `audit_guided_wave_acquisition(request)`: 선택한 acquisition/sheet의 파일 lineage와 count만 반환
- `specifications()`: `data.mendeley_guided_wave_typed_sample_rows` metadata audit ModelSpec

## Row identity, units, and missing metadata

행 번호는 selected source sheet의 row 2가 header이므로 `provider_source_row`는 3부터 시작하고, `sample_row_order`는 0부터 시작한다. row는 workbook 원본 순서대로 yield한다. distance가 반복되는 인접 sample도 보존하며 축을 정렬하거나 합치지 않는다. 각 record는 outer ZIP SHA-256, nested ZIP SHA-256, workbook member 경로·SHA-256, sheet 이름/순서, acquisition ID, caller specimen ID, source-row order, row canonical digest 및 authorization digest를 갖는다. `Evidence`에는 CC BY 4.0 source citation과 outer-archive digest가 기록된다.

수량 단위는 source schema를 따른다: distance `m`, torsional/flexural/provider pure-DAC channels `V`, excitation `Hz`, cycle count는 excitation cycles다. provider DAC는 독립 signal field로 보존하며 measured damage channel과 합치지 않는다. 각 행의 machining step, timestamp, 온도는 자료에서 이 reader로 연결되지 않으므로 `None`으로 남는다.

## Interpretation boundaries

이 자료는 하나의 실험 강관에 대한 repeated acquisition이다. acquisition이나 distance row는 독립 specimen/fleet 표본이 아니다. 자료의 207개 healthy-period signal 뒤의 순차 가공 손상 단계는 자연 부식시간 이력으로 해석되지 않는다. 이 reader는 waveform voltage에서 결함 치수, 남은 벽두께, 부식률, POD, failure probability 또는 허용성을 계산하지 않는다. 구조 상태 추정이나 FTA 연동에는 별도의 caller-reviewed calibration/uncertainty model과 명시적인 event evidence가 필요하다.
