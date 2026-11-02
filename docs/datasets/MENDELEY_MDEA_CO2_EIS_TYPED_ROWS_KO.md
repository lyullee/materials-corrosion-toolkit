# MDEA 수용액의 CO₂ 보호막 EIS 자료: local typed reader

## 레코드와 권리

- Mendeley Data, version 3: [10.17632/6tscvfjycn.3](https://doi.org/10.17632/6tscvfjycn.3)
- 공식 dataset record: <https://data.mendeley.com/datasets/6tscvfjycn/3>
- 파일 목록/API: <https://data.mendeley.com/public-api/datasets/6tscvfjycn/files?folder_id=root&version=3&%24start=0&%24limit=1000>
- 논문 DOI: [10.1016/j.corsci.2022.110859](https://doi.org/10.1016/j.corsci.2022.110859)
- provider dataset license: CC BY 4.0. 재사용 시 dataset과 article attribution, license URL 및 변경 고지를 보존한다.

공식 record는 80 °C의 CO₂ 포화 aqueous methyldiethanolamine(MDEA)에서 탄소강 표면막을 연구한 실험 및 계산 EIS 자료를 제공한다고 기술한다. 실험 기록은 BioLogic potentiostat/EC-Lab 취득 데이터이며 전위 기준은 saturated KCl의 Ag/AgCl 전극이라고 제공자 설명이 명시한다. 연구 요약은 anoxic CO₂-MDEA-H₂O 조건에서 FeCO₃ 보호막과 산소 유입 시 다른 표면 상이 형성되는 점을 설명한다. 이것은 특정 용액과 시편에 대한 실험 자료이며 일반 carbon steel 또는 pipeline wet-CO₂ 성능을 증명하지 않는다.

## 파일과 local-only 경계

Version 3의 root file listing은 13개 `.txt` 파일의 이름, file ID, byte 수, SHA-256, content type 및 direct download URL을 반환한다. 전체 파일을 로컬에서 내려받아 provider SHA-256과 대조했다. 파일들은 `data/raw/mendeley-mdea-co2-eis/`에 보관하며 `data/raw/`는 배포에서 제외한다. 이 디렉터리의 `local_manifest.json`은 provider file listing을 정리해 보존하고, reader는 manifest와 각 asset의 SHA-256을 확인한다.

파일 이름의 `Experimental`과 `Simulated` 구분을 유지한다. 일부 파일은 `initial`, `final`, MDEA 농도 토큰을 포함하고, 하나는 O₂ 대조 조건 이름을 포함하지만 reader는 파일명 이상의 조건이나 그룹을 추정하지 않는다. Experimental 파일은 18개 열, simulated 파일은 13개 열이며, 모든 파일은 70줄 안팎의 tab-separated point records를 담는다. Header의 마지막 tab은 값 열을 하나 더 뜻하지 않아 parser는 마지막 빈 header token만 정렬 과정에서 생략한다. 원 header line과 나머지 열 이름·순서, 각 raw token, 행 순서, source line digest는 결과에 남는다. `µ` 기호는 Windows-1252 텍스트 인코딩으로 읽는다.

## Python interface

- `MDEAEISReadAuthorization`: CC BY 출처와 계산 이용·local-only 승인을 표현
- `MDEAEISCell`: 원 문자열 token과 같은 값의 finite numeric parse 또는 값 종류를 유지
- `MDEAEISPointRow`: dataset/source/file IDs, 파일 digest, experimental/simulated 종류, 행 및 열 계보
- `iter_mendeley_mdea_eis_rows(directory, authorization=..., include_simulated=True)`: 버전 파일을 provider 목록과 순서대로 읽는다. `include_simulated=False`이면 simulated 파일은 건너뛴다.
- `audit_mendeley_mdea_eis_directory(...)`: 숫자 point values를 내보내지 않고 고정 파일, digest, 헤더 및 행 수를 보고한다.
- Model/interface ID: `data.mendeley_mdea_co2_eis_typed_rows`
- Source ID: `mendeley_mdea_co2_eis_version3`

예시:

```python
from matintegrity.mendeley_mdea_co2_eis_rows import (
    MDEAEISReadAuthorization,
    iter_mendeley_mdea_eis_rows,
)

auth = MDEAEISReadAuthorization(
    attribution=(
        "Sadeek et al., Corrosion Science (2023), DOI 10.1016/j.corsci.2022.110859; "
        "Mendeley Data DOI 10.17632/6tscvfjycn.3, CC BY 4.0"
    ),
    computational_use_authorized=True,
    local_only_authorized=True,
)
for point in iter_mendeley_mdea_eis_rows(
    "data/raw/mendeley-mdea-co2-eis", authorization=auth, include_simulated=False
):
    print(point.source_filename, point.provider_line_number, point.ordered_cells[0].numeric_value)
```

이 모듈은 local typed import only다. JSON Schema, default registry, capability/source catalog에는 중앙 연결되어 있다. 원 자료는 `data/raw/`에 남고 공개 배포 경계에서 제외된다.

공급자 열을 명시적으로 지정해 complex impedance를 계산하는 후처리는 `matintegrity.mendeley_mdea_eis_complex`의 `MDEAEISComplexConversionRequest` 및 `evaluate_mendeley_mdea_eis_complex_conversion()`을 사용한다. 예를 들어 제공자의 `freq/Hz`, `Re(Z)/Ohm`, `-Im(Z)/Ohm` 열을 쓰더라도 상상축 부호는 caller가 Evidence-backed mapping으로 명시해야 한다. optional `|Z|/Ohm` comparison은 선택 열·상대 허용차가 caller 검토된 경우에만 수행한다. 계산은 행을 정렬하거나 주파수 누락을 채우지 않고, experimental과 simulated spectra를 합치지 않는다. EIS magnitude/phase 변환만 하며 Nyquist circuit fitting, film identification, kinetic calibration 또는 corrosion-rate 산출은 하지 않는다.

`mendeley_mdea_eis_column_mapping_digest(...)`가 선택 헤더, 선언 단위, 허수축 multiplier, data kind, optional magnitude column 및 tolerance의 canonical digest를 만든다. 같은 digest를 `column_mapping_sha256`와 mapping `Evidence.sha256`에 넣어 계약과 Evidence를 결속한다. 출력점에는 원 provider magnitude(선택된 경우), 성분으로 계산한 magnitude 및 상대 불일치량이 보존된다.

## 데이터 의미와 사용 한계

Reader는 impedance 계산, Nyquist 변환, equivalent-circuit fitting, time/frequency alignment, 실험/모의 결과 비교 또는 부식률 산출을 하지 않는다. 숫자 값은 원래 헤더가 붙은 값과 단위를 유지하며 단위 변환·부호 변경·정렬을 수행하지 않는다.

- EIS 행을 corrosion penetration, metal loss, corrosion rate, repassivation 또는 pit growth로 바꾸지 않는다.
- 제공 자료의 simulated spectrum을 experimental measurement나 독립 validation로 취급하지 않는다.
- 파일명 토큰만으로 고정된 농도/시점/시험 조건을 해석하지 않는다. 조건 join은 별도의 reviewed mapping 필요.
- calibrated BV parameter, surface-film kinetic law, CO₂ speciation constant, scale growth coefficient 또는 generalized film-protection multiplier를 추정하지 않는다.
- 하나의 연구계, 하나의 특정 carbon-steel/MDEA 계열 및 시험장치에 대한 자료다. pipeline water/brine, acid gas, chloride, flow, metallurgy, geometry, field condition에 일반화하지 않는다.
- rows/files를 독립 specimen 또는 독립 replicate로 해석하지 않는다. sample IDs, replicate allocation, uncertainty propagation은 파일명/수치에서 추론하지 않는다.
- Reader의 checksum/dimension 일치는 로컬 자산 계보 확인이며 과학적 재현성·모델 적합성·물리 qualification을 의미하지 않는다.

원 XLSX/raw row values는 package, public fixture, public example 또는 배포 catalog snapshot에 포함하지 않는다. 공개 자료를 후속 연구에 사용하기 전 원 논문 방법과 dataset의 각 file metadata, units 및 실험/모의 분류를 다시 확인한다.
