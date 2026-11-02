# Ti-6Al-4V 음극 분극 CSV 가져오기

`matintegrity.galvanic_data.import_ti6al4v_cathodic_polarization_csv`는 [Zenodo record 12727325](https://zenodo.org/records/12727325)의 `Fig1.csv` 형식에서 선택한 한 전해질 조건의 전위·전기화학 순전류·Ti 용출 부분전류를 provenance를 유지하며 가져온다. 해당 record는 dataset license를 CC0-1.0으로 선언한다. 논문 표현물의 권리조건은 dataset record와 별도이므로 이 프로젝트는 논문 문장·그림·표를 복사하지 않는다.

## 입력과 결과

이 reader는 일반 CSV reader가 아니라 Zenodo record의 고정 `Fig1.csv` 스냅샷 전용이다. 예상 및 실제 SHA-256은 `b119b00c03068f8e217c4ec7ae8f52dd079d6a69f52bda44221c077f6d9e9800`와 일치해야 한다. 호출자는 매질 (`pbs` 또는 `pbs_h2o2`), surface condition, protocol, electrolyte, 기준전극, 온도, 조건/단위 검토 표식도 지정한다. Evidence에는 동일 source ID·record 인용·CC0-1.0·파일 SHA-256을 묶어야 한다. 파일 헤더가 선택 조건의 열과 일치해야 하며 입력 CSV 한도는 2 MB이다. 다른 데이터에는 일반 `PolarizationCurve` 계약을 구성해 사용한다.

제공자 전류밀도 단위 `μA/cm²`는 `A/m²`로 환산한다. factor 0.01을 적용하고, electrochemical `je`는 `PolarizationCurve.signed_net_current_density_A_m2`로, ICP-AES 기반 Ti dissolution `jTi`는 별도 aligned result array로 돌려준다. `je`의 부호는 importer에서 anodic-positive라고 추정하지 않는다. 실제 노출 면적도 dataset 표에서 얻을 수 없으므로 mixed-electrode current 계산 전에 사용자가 별도로 공급해야 한다.

`PolarizationCurve` 계약은 전위 증가 순서를 요구한다. CSV의 선택 branch가 엄격 단조 감소할 경우 전체 배열과 원래 CSV row ID를 함께 뒤집어 해당 계약에 맞춘다. 단조 증가 branch는 그대로 둔다. 반복/비단조 potential은 cycle을 정렬하거나 재구성하지 않고 `out_of_scope`로 반환한다. 선택 `je` 누락 행은 원 행 번호와 함께 `omitted_rows`에 남고, 용출 전류 값이 빈 행은 `None`으로 보존한다.

## 적용 범위

제공자 README에 설명된 조건은 SCE 기준, 23 °C, flow-cell 유량 1 mL/min, scan rate 1 mV/s이다. importer가 이 조건을 자동 대입하지 않으며 API 호출자가 실제 사용 조건을 검토하고 명시해야 한다. 한 파일은 한 연구의 두 매질 곡선을 포함하지만, importer는 시편 독립성·자료 분할·전위 응답 부호·동적 안정성·부식률·설계 허용치·현장 전이를 검증하지 않는다. 순전류를 금속 용출 부분전류로 바꿔 사용해서는 안 된다.

실행 예는 `python examples/ti6al4v_polarization_import.py <local-Fig1.csv> --medium pbs`다. 원자료는 [Zenodo record](https://zenodo.org/records/12727325)에서 별도로 취득하고 checksum을 확인한다. 공개 스키마는 [`Ti6Al4VCathodicPolarizationImportRequest`](schemas/Ti6Al4VCathodicPolarizationImportRequest.json), 데이터 권리와 제공자 checksum은 dataset/source catalog 및 `data/acquisition_log.json`에 기록한다. 원본 파일은 ignore 대상인 `data/raw/`에만 두며 배포물에 복사하지 않는다.
