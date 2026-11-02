# Mendeley thermal-rod 실험 typed row API

## 출처와 범위

- Dataset ID: `thermal-rod-transient`
- DOI: `10.17632/sbcf36976g.1`
- Dataset license declaration: CC BY 4.0 ([official Mendeley record](https://data.mendeley.com/datasets/sbcf36976g/1), rechecked 2026-10-31)
- Model ID: `data.mendeley_thermal_rod_typed_rows`
- Source ID: `mendeley_thermal_rod_typed_rows`
- Catalogued local archive: `data/raw/thermal-rod-transient/sbcf36976g-1.zip`
- Pinned archive SHA-256: `9226632888404fe792358bc5a33cf2edacbb16e35352a36a6c0c1c4c155e723a`
- Pinned archive size: 2,099,328 bytes

이 모듈은 기존 `thermal_data.read_thermal_rod_series` 파서를 재사용하며, 그 앞에서 정확한 archive 파일명·byte 수·SHA-256을 확인한다. ZIP 원본과 pointwise 관측은 배포물에 포함하지 않는다. 공개 dataset metadata의 CC BY 4.0 표기를 기록하지만, attribution 외에 caller가 계산 이용 권한과 local-only 경계를 명시하도록 요구한다. 이 검토 입력은 권리의 법적 유효성을 대신 판정하지 않는다.

## API 계약

- `ThermalRodReadAuthorization`: dataset/DOI/license 고정값, caller attribution, computational-use 승인 및 local-only 승인
- `ThermalRodObservationRow`: source run의 한 CSV 행과 행/파일 계보, 단위, `Evidence`
- `iter_thermal_rod_observation_rows(archive_path, run_id, authorization=...)`: checksum이 고정된 archive 내 run을 source order대로 yield
- `ThermalRodArchiveAuditRequest`: metadata-only audit 입력
- `audit_thermal_rod_run(request)`: source path 또는 측정 point values를 반환하지 않고 archive/member checksum 및 row count 반환
- `specifications()`: metadata audit을 ModelSpec `data.mendeley_thermal_rod_typed_rows`로 제공

```python
from pathlib import Path

from matintegrity.thermal_typed_rows import (
    ThermalRodReadAuthorization,
    iter_thermal_rod_observation_rows,
)

authorization = ThermalRodReadAuthorization(
    attribution="Tomanek and Stutts, Mendeley Data, DOI 10.17632/sbcf36976g.1",
    computational_use_authorized=True,
    local_only_authorized=True,
)

for observation in iter_thermal_rod_observation_rows(
    Path("data/raw/thermal-rod-transient/sbcf36976g-1.zip"),
    run_id="caller-selected-run-id",
    authorization=authorization,
):
    # Store or process the typed row under the same local-use boundary.
    print(observation.provider_source_row, observation.time_s, observation.tc1_excess_temperature_K)
```

이 snippet은 사용자 로컬 archive를 전제로 하며 프로젝트 예제/패키지에 dataset 원행을 넣지 않는다.

## 행 ID와 데이터 의미

CSV 첫 행은 header다. API의 `source_row_order`는 자료 행 순서의 0-based 위치이며 `provider_source_row`는 header를 포함한 1-based CSV 행 번호로 2에서 시작한다. DataFrame의 원래 순서를 유지하고 시간 값을 재정렬하지 않는다. 각 row는 run ID, 내부 ZIP member명과 SHA-256, archive SHA-256, canonical row SHA-256, attribution digest 및 `Evidence`를 보존한다.

출력 단위는 시간 `s`, TC1–TC6의 ambient 기준 초과온도 차 `K`, controller 설정값 `count_on_1023_max_scale`이다. 음의 초과온도 차는 원자료 수치로 유지한다. 이 파서는 결측·비유한 source row가 있으면 실패하며, 행 삭제·보간·대체를 하지 않는다.

controller count는 W 또는 열유속이 아니다. 이 dataset은 봉 형상의 1차원 과도 열전달 실험이며, sensor 위치, rod geometry, 열입력 효율, 재료 상태 및 각 실험조건의 모델 적합성을 이 reader가 확정하지 않는다. 개별 run, thermocouple channel 또는 처리된 fit 결과를 독립 표본으로 취급하지 않는다. 열 이력에서 부식률, 벽두께 감소, 재료 허용값, 구조 수명 또는 integrity qualification을 추론하지 않는다.
