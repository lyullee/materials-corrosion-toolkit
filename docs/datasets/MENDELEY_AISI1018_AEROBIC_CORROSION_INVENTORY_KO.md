# Mendeley AISI 1018 호기성 미생물 부식 데이터 파일 인벤토리

## 출처와 재사용 조건

- 공식 버전 기록: [Mendeley Data v1](https://data.mendeley.com/datasets/zyy3yktzpf/1), DOI [10.17632/zyy3yktzpf.1](https://doi.org/10.17632/zyy3yktzpf.1)
- 버전·파일·권리 메타데이터 API: [Mendeley 공개 API](https://data.mendeley.com/public-api/datasets/zyy3yktzpf)
- 제공자는 CC BY 4.0을 표시한다. 재사용 시 출처, 라이선스 링크와 변경 여부를 표시해야 한다. 제공자 라이선스 문구는 자료 안에 제3자 소유로 표시된 내용에 별도 허가가 필요할 수 있다고 명시한다. 따라서 원시 파일, 행 데이터와 그림을 재배포하기 전에 개별 자료의 권리와 출처를 확인해야 한다.
- 원본 22개는 `.gitignore`가 적용된 `data/raw/mendeley-aisi1018-aerobic-consortium-v1/`에만 둔다. 데이터 원본은 릴리스에 넣지 않는다. 데이터 목록과 파일별 제공자 ID·크기·SHA-256은 `data/catalogs/datasets.json`과 로컬 `local_manifest.json`에서 확인한다.

## 자료 구조 검토 및 해석 제한

자료 기록은 AISI 1018 강의 호기성 세균 컨소시엄 부식 및 억제 조건 실험 데이터라고 설명한다. 제공 목록은 텍스트 17개와 Origin 프로젝트 `.opj` 5개로 구성된다. 텍스트 파일은 ACM Instruments 형식 설명과 ZView 형식 설명이 섞여 있고, 공통 열 스키마·단위·시험편/반복 매핑이 모든 파일에 명시돼 있지 않다. 특히 일부 ZView 텍스트의 내부 헤더에는 1993년과 `demo.z`가 표시되어, 같은 자료 묶음의 2024–2025 계측기 텍스트 정보와 맥락이 일치하지 않는다. 이 불일치는 확인되지 않았다.

따라서 이 API는 **파일 단위 인벤토리만** 제공한다. 텍스트 값이나 OPJ 내부 표를 읽지 않으며 EIS/LPR 열, 부식 전류, 부식률, 시편, 처리조건, 반복 또는 단위를 추정하지 않는다. `.opj`를 열거나 변환하는 Origin 소프트웨어도 의존성으로 포함하지 않는다. 제공된 데이터의 실험 의미를 확인하려면 연구 논문·실험 프로토콜·파일별 열 설명을 별도로 확보해 교차 검토해야 한다.

## 로컬 인벤토리 API

`matintegrity.mendeley_aisi1018_aerobic_inventory`는 고정된 22개 파일명에 대해 제공자 파일 ID, 바이트 크기와 SHA-256을 검증한다. 출력에는 이 메타데이터와 CC BY 4.0 출처 Evidence만 포함되며 파일 내용은 반환하지 않는다. 호출자는 선택적으로 파일별 설명을 직접 붙일 수 있지만 그 문구와 Evidence는 사용자 선언으로 남는다. 파일명은 데이터 의미의 증거로 간주하지 않는다.

```python
from matintegrity.contracts import Evidence
from matintegrity.mendeley_aisi1018_aerobic_inventory import (
    AISI1018FileMapping,
    AISI1018InventoryRequest,
    AISI1018ReadAuthorization,
    audit_aisi1018_dataset_inventory,
)

authorization = AISI1018ReadAuthorization(
    attribution="Mendeley Data v1, DOI:10.17632/zyy3yktzpf.1",
    computational_use_authorized=True,
    local_only_authorized=True,
)
mapping = AISI1018FileMapping(
    source_filename="Agua.txt",
    caller_label="caller reviewed label",
    mapping_basis="caller provided this label; experimental meaning not inferred",
    evidence=Evidence(
        source_id="caller_aisi1018_corrosion_file_mapping",
        origin="user_declared",
        citation="caller mapping note, revision 1",
    ),
)
inventory = audit_aisi1018_dataset_inventory(AISI1018InventoryRequest(
    local_data_directory="data/raw/mendeley-aisi1018-aerobic-consortium-v1",
    authorization=authorization,
    file_mappings=(mapping,),
))
```

이 결과는 데이터의 정확성, 단위, 실험 재현성, 부식 메커니즘, 재료 적용성, 위험도, 수명 또는 설계 적합성을 검증하지 않는다. 제3자 권리 검토가 완료되지 않았으므로 추출값과 프로젝트 파일을 공개 배포하지 않는다.
