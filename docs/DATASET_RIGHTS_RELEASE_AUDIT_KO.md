# 데이터 권리 및 공개 경계 감사

`data/catalogs/datasets.json`의 출처 선언과 `MANIFEST.in`의 선언상 파일 경계를 대조하려면 다음 정적 명령을 실행한다.

```powershell
.venv\Scripts\python.exe scripts/audit_dataset_release_rights.py
```

이 도구는 각 데이터셋의 citation, license label/URL, rights status, acquisition policy, checked date, limitations, asset filename/URL/checksum을 `data/catalogs/dataset_release_rights_audit.json`에 그대로 기록한다. 누락된 checksum, 중복 파일명, 미확정 권리와 선언상 제외 경계를 별도 표시한다. checksum 확인은 문자열 형식 검사뿐이며 원격 원본과 실제 대조하지 않는다.

`acquisition_policy`는 파일 취득 정책이고 재배포 허가 판정이 아니다. 공개 접근, dataset 단위의 license declaration, compiler가 배포한 표와 그 표에 포함된 논문 관측값의 저작권도 서로 다른 문제다. 따라서 보고서는 `not_approved_for_redistribution`으로 명시된 항목만 그 상태를 그대로 표시하고 나머지도 이 감사 자체의 `not_assessed_by_this_audit`로 남긴다. 자동으로 배포 허가를 부여하지 않는다.

현재 `MANIFEST.in`은 JSON catalog metadata를 포함하도록 선언하고 `data/raw`, `data/derived`, `data/evidence`를 제외하도록 선언한다. 이 보고서는 manifest 규칙을 읽은 정적 확인이다. 실제 sdist와 wheel을 만들거나 그 내부 파일을 검사하지 않았으므로 배포 직전에는 별도 archive-content 검토가 필요하다.

## 현재 정적 인벤토리

2026-10-30 기준 보고서는 63개 dataset record와 276개 asset record를 읽었다. 필수 메타데이터·asset 경로/checksum 문자열 형식 및 manifest 경계에서 구조 오류는 없었다. 이번 로컬 snapshot 보강에서는 정확한 `data/raw/<dataset-id>/<filename>` 경로에서 확인한 14개 파일에 대해 checksum/byte metadata 16개 필드를 채웠다. 그중 NIST CORR-DATA와 compiled pipe-burst의 기존 SHA-256은 실제 로컬 파일에서 재계산한 값과 일치했다. 나머지 12개 checksum은 이번 로컬 바이트를 고정한 값이며 제공자 checksum 검증으로 해석하지 않는다. 갱신된 metadata audit의 경고는 checksum 미제공 6개, byte size 미고정 6개, 여러 dataset record 간 basename 중복 3건이다. 로컬 파일 hash는 출처 진위나 재배포 권리를 증명하지 않는다.

선택된 로컬 snapshot의 바이트 길이와 선언 hash를 재검사하려면 아래 명령을 사용한다. 이 검사는 명시한 7개 dataset ID의 catalog-relative exact-path assets 14개를 다루며 원격 다운로드를 하지 않는다. 보고서는 `validation/local_dataset_asset_integrity.json`에 남기고, catalog와 local hash 모두 `match`인 14개를 확인했다.

```powershell
.venv\Scripts\python.exe scripts/verify_local_dataset_asset_pins.py --dataset-id nist-corr --dataset-id hannover-weld --dataset-id metropt3 --dataset-id steel-plates --dataset-id compiled-pipe-burst --dataset-id mendeley-304l-chloride-scc-salt-loading --dataset-id matr-aqueous-electrolytes
```

취득 정책 값은 `allowed` 45, `allowed_selected_assets` 6, `allowed_selected_text_assets` 1, `metadata_only` 10, `do_not_download` 1개다. 이 숫자는 취득 정책의 분포만 요약하며 배포 권리 승인 수가 아니다. `not_approved_for_redistribution`으로 명시된 `nims-creep`만 해당 선언을 그대로 보고했고, 나머지 record도 underlying-observation 권리를 이 도구가 승인하지 않는다.

## 2026-11-01 최신 카탈로그 감사

`data/catalogs/datasets.json`에는 83개 dataset record와 510개 asset record가 있다. 최신 release-rights audit는 0 errors / 14 warnings를 기록했다. catalog audit의 취득정책 분포는 `allowed` 53, `allowed_selected_assets` 15, `allowed_selected_text_assets` 1, `do_not_download` 1, `metadata_only` 13이다. 제공자 checksum이 없는 asset 5개는 별도 finding으로 남아 있다. Mendeley MPEA 부식 compilation 및 대기 탄소강 dataset은 provider record의 CC BY 4.0 선언만 확인했고 파일 manifest와 개별 문헌 관측치의 권리는 미확정이므로 metadata-only다. 이 결과는 법률 검토나 재배포 권리 승인을 대신하지 않는다.

