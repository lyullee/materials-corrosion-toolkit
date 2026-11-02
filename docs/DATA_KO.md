# 확보 데이터와 사용 범위

## 2026-10-31 최신 데이터 추가 및 카탈로그 상태

Mendeley Data v1의 [explosively welded multilayer plates fatigue record](https://data.mendeley.com/datasets/mc8bc9tm59/1)는 provider가 CC BY 4.0으로 표시한다. 기록의 third-party-content caveat를 그대로 유지하고, 라이선스 표기만으로 workbook 내 모든 자료의 재배포 권리를 단정하지 않는다. 선택 workbook `MultilayerPlatesData.xlsx`는 1,393,400 bytes이며 provider API의 SHA-256과 로컬 SHA-256이 일치한다. 원본은 ignored `data/raw/mendeley-explosive-weld-multilayer-fatigue/`에만 보관한다. 기본 유형화 reader는 원 셀·행 순서·source lineage를 보존하고 적층 구성, 단위, 피로법칙, 부식률, 성능 또는 적격성을 자동 추론하지 않는다. 별도 caller-mapped import는 명시된 sheet/header/행·열 선택, 의미·단위·역할 및 mapping Evidence가 일치할 때만 typed field를 내며, formula와 원값을 평가·환산하지 않는다. 자세한 범위는 [reader 안내](datasets/MENDELEY_EXPLOSIVE_WELD_MULTILAYER_FATIGUE_TYPED_ROWS_KO.md)와 dataset catalog를 참조한다.

2026-11-01 현재 dataset catalog는 83개 dataset record / 510개 asset record다. 재생성한 rights audit는 0 errors / 14 warnings를 기록했으며, catalog audit의 남은 주요 항목은 제공자 checksum 미제공 5개 asset이다. Mendeley MPEA 및 대기 탄소강 dataset은 record 수준 CC BY 4.0 표시만 확인되어 metadata_only로 남겼다. 실제 파일 manifest와 각 원문 관측치의 재사용 권리는 확인되지 않아 raw 자산·수치·보정 importer를 추가하지 않았다. 원본·파생·근거 데이터는 release boundary에서 제외하며, 이 감사는 법률 승인이나 과학적 적합성 판정이 아니다. 아래 과거 dataset별 기록은 각 기록 시점의 집계를 유지한다.

2026-11-01에는 Crevice 전기화학 자료 후보를 추가 조사했다. ETH Research Collection은 리벳 구조물의 핀별 ZRA 전류 이력과 XRD 파일을 CC BY 4.0 후보로 설명하지만 레코드는 검토 중/미검증 상태이고 현재 조사 환경에서 본문 접근이 차단됐다. Mendeley의 Ni계 합금 재부동태 전위 자료도 CC BY 4.0을 선언하나 이번 확인에서는 파일 manifest를 얻지 못했다. 둘 다 raw asset 목록·체크섬을 확인하기 전이라 dataset 카탈로그나 reader에 넣지 않았다. 조사 근거와 활용 경계는 [Crevice 전기화학 공개자료 후보 검토](datasets/CREVICE_ELECTROCHEMICAL_OPEN_DATA_CANDIDATES_KO.md)에 기록했다.

기준일은 2026년 10월 30일이다. 취득 장부에서 다운로드 완료 상태인 48개 데이터 ID의 고유 경로 222개, 합계 4,294,517,947바이트를 집계했다. 원본은 로컬 캐시에 있고 공개 저장소에는 출처·조건·해시와 조사 결과를 보존한다.

같은 기준일 카탈로그 감사는 메타데이터 63개 dataset record와 276개 asset record를 집계한다. 이는 취득 완료 수가 아니며, `metadata_only` 10건과 `do_not_download` 1건 등 조사·미취득 레코드도 포함한다. 카탈로그 감사 JSON은 `validation/dataset_catalog_audit.json`에 생성하며 publisher checksum 누락, 로컬 사본 검사 및 권리 상태를 별도로 기록한다. 감사 통과는 재배포 권리 허가나 과학적 적합성 승인을 뜻하지 않는다.

2026-10-30에 14개 선택 로컬 asset의 정확한 파일 크기/SHA-256을 catalog에 고정하고 `scripts/verify_local_dataset_asset_pins.py`로 재계산 대조했다. NIST CORR-DATA와 compiled pipe-burst의 기존 기록 checksum 두 건은 일치했고, 나머지 12개는 local snapshot pins다. 이 검사는 파일 무결성 반복 확인용이며 provider authenticity, license, redistribution rights 또는 scientific fitness를 증명하지 않는다. 상세 집계는 [dataset release rights audit](DATASET_RIGHTS_RELEASE_AUDIT_KO.md)와 `validation/local_dataset_asset_integrity.json`에 있다.

Dryad의 AlCoCrFeNi₂.₁ 적층제조 합금 피로·균열 자료(doi:10.5061/dryad.vq83bk48n)는 공개 record에서 fatigue-fracture, nanoindentation, surface-characterization archive와 README를 확인했다. 데이터 다운로드 endpoint의 이용조건은 Dryad 공식 API 문서가 파일 다운로드 요청에 API token을 요구한다고 명시하므로, 인증 없는 자동 취득은 수행하지 않고 `metadata_only`로 유지한다. 인증이나 다운로드 가능 여부가 바뀌면 원본 취득 전 dataset license와 개별 파일 인벤토리·checksum을 다시 확인한다. [공식 dataset record](https://datadryad.org/dataset/doi:10.5061/dryad.vq83bk48n), [Dryad API 다운로드 정책](https://github.com/datadryad/dryad-app/blob/main/documentation/apis/api_accounts.md).

2026-10-30에 Zenodo의 Ti-6Al-4V 음극 분극 연구 자료 중 `Fig1.csv`, 두 PDP ICP-AES intensity CSV, 제공자 README를 선택 취득했다. 공식 record는 CC0-1.0을 표시하며, 네 파일은 각 제공자 MD5와 대조했다. 원파일은 `data/raw/zenodo-ti6al4v-cathodic-corrosion/`에만 두고 공개 코드·문서에는 점별 관측값을 복사하지 않는다. [Zenodo record 12727325](https://zenodo.org/records/12727325), [CC0-1.0](https://creativecommons.org/publicdomain/zero/1.0/).

분극 파일은 PBS 및 33 mM H₂O₂ 첨가 PBS에서 전위와 전기화학 순전류밀도, ICP-AES 기반 Ti 용출 부분전류밀도를 별도 열로 제공한다. README에 기록된 시험 조건은 SCE 기준 전위, 23 °C, 1 mL/min 유량, 1 mV/s 주사다. 강제전위 실험의 순전류를 금속 용출률로 간주하지 않으며, intensity 원시 신호도 보정된 전류로 취급하지 않는다. H₂O₂와 PBS 파일은 동일 연구 안의 조건 비교 후보이지 독립 자료군이나 범용 재료성능 기준이 아니다. 상세 권리·파일 checksum·사용 한계는 `data/catalogs/datasets.json`과 `data/acquisition_log.json`에 기록했다.

해당 `Fig1.csv` 선택 조건을 SHA-256으로 고정해 읽는 `matintegrity.galvanic_data.import_ti6al4v_cathodic_polarization_csv`를 추가했다. source CSV row ID와 branch traversal order를 보존하며, 전위가 단조 감소할 때만 전체 배열을 역순화한다. 순전류와 Ti 부분용출전류는 별도 출력으로 유지한다. 이 데이터의 재사용 규칙과 합성 배선 예는 [분극 CSV 가져오기 설명](TI6AL4V_POLARIZATION_IMPORT_KO.md)에 있다.

2026-11-01 공개 corrosion-data 후보를 최신 metadata에 맞춰 정리했다. MPEA compilation version 3 (`10.17632/cfz68tkwfk.3`)은 CC BY 4.0이고, 탄소강 first-year atmospheric corrosion record version 1 (`10.17632/ysr7wy3y7z.1`)도 CC BY 4.0을 선언한다. 두 record 모두 조사한 landing page에서 자산 파일 목록/UUID/크기/checksum을 확인하지 못했고, 원문헌 observation의 row-level provenance와 재사용 권리는 더 확인해야 하므로 metadata-only로 유지한다. 공개 데이터 catalogue와 우선순위·사용 경계는 [MPEA/대기부식 후보 검토](datasets/MENDELEY_AM_MPEA_CORROSION_METADATA_REVIEW_KO.md)를 참조한다.

2026-10-30에는 FH Münster의 N₂-PSA 공정 데이터를 Mendeley 공개 API에서 취득했다. 제공자는 2019–2026 실험실 데이터와 관련 twin-bed PSA 연구를 설명하고 dataset license를 CC BY 4.0으로 표시한다. 원 workbook은 65,405 bytes이며 provider SHA-256 `2c9767b2423800e783dda01a9d319df0825233d70e10c311b2f860d26d713bc5`와 대조했고 `data/raw` 아래에 보관해 배포에서 제외한다. 구조 감사상 단일 sheet, 520개 data row, 18개 열이며 outer operating/cycle/inner settings와 reported results로 묶인 표다. 시간표본 transient가 아니고 experimental/simulated origin도 행별로 나눠 사용하지 않았다. 따라서 CSV 이력 입력기나 CO₂ 부식 모델의 검증자료가 아니며, 독립 run 계층과 행 수준 이용범위는 별도 확인이 필요하다. [Mendeley dataset](https://data.mendeley.com/datasets/d2vx7w6x74/1), [DOI](https://doi.org/10.17632/d2vx7w6x74.1).



2026-10-30에 TRI Energy & Materials Data의 [Aqueous electrolytes](https://data.matr.io/5/)를 조사했다. Dataset page는 CC BY 4.0을 선언하고 JSON/PKL을 제공한다. 공식 download endpoint에서 ZIP 1,252,996 bytes를 `data/raw/matr-aqueous-electrolytes/otto_data.zip`에 취득했다. 공급자 checksum은 공개되지 않아 archive SHA-256 `4fd633243504316d48b5e42482e5b870a21f3a551010833abae4dc2762184744` 및 JSON member SHA-256 `7cd0b865cfdec2c10a048e6f16b50d2a0c5232db388645e5e215b062ce275adf`는 로컬 snapshot 고정값으로만 쓴다. JSON 구조는 251개 고유 GUID, 21개 source RUN_ID, 각각 601시점의 60초 fixed-current stability trace, provider-native pH·conductivity·temperature와 feeder 조성 값을 포함한다. 논문 방법은 Pt/Ag-AgCl의 HER/OER fast assessment로 설명하고 있어 corrosion polarization curve·corrosion current·부식률 또는 SIT 계수 자료로 오인하지 않는다. conductivity·temperature 단위가 JSON에 없어 변환하지 않는다. 별도 reader와 aggregate-only [구조 감사 보고서](../validation/otto_electrolyte_archive_audit.json)를 추가했으며 원자료는 공개 패키지에서 제외된다. 논문 license notice와 dataset page의 CC BY 4.0 선언을 별도로 기록하고 논문 표현물은 복사하지 않는다.

2026-10-30에 TUDOdata 공식 Dataverse API를 조회해 평균 이온 활동도 계수 dataset의 v1 metadata를 확인했다. API는 dataset-level CC BY 4.0, 225개 파일, 총 512,400 bytes, 각 파일의 MD5 제공, restricted 표시 파일 0개를 반환했다. 그러나 dataset 설명은 원 관측 중 일부가 Lobo·Quaresma의 Elsevier 1989 handbook에서 발췌됐다고 밝히고 나머지는 파일 내부 문헌으로 추적하라고 한다. 또 파일 중 135개는 fit/model data라 독립 검증자료로 볼 수 없고, 관측량은 평균 이온 계수여서 단일 이온 SIT 계수와 직접 같지 않다. 이 때문에 다운로드·추출·모델 사용은 보류하고 카탈로그에는 metadata-only로 등록했다. TUDOdata의 deposit terms는 제공자가 제3자 권리를 보증한다고 설명하지만, 이는 각 발췌 관측의 출처와 권리를 우리가 검증했다는 뜻은 아니다. [공식 dataset API](https://data.tu-dortmund.de/api/datasets/:persistentId/?persistentId=doi%3A10.17877%2FRESOLV-2024-M4WGMZTG), [TUDOdata dataset terms 안내](https://fdm.tu-dortmund.de/en/rdm-at-tu-dortmund/technical-support/tudodata/).

2026-10-30 카탈로그의 직전 감사 스냅샷은 62개 dataset과 272개 asset을 검사해 `validation/dataset_catalog_audit.json`에 기록했다. 그 뒤 이번 Zenodo 기록과 선택 asset 네 개를 추가해 최신 catalog는 63개 dataset·276개 asset이다. 기존 감사 스냅샷의 133개 checksum 일치 로컬 asset, 제공자 checksum 없는 로컬 12개 파일 및 checksum 없는 asset 18개 집계는 새 네 asset을 포함하지 않는다. 새 파일 네 개는 공식 record의 제공자 MD5와 취득 시점에 각각 대조했으며 raw는 계속 배포 제외다. 다음 자료 감사 실행 때 validation snapshot도 갱신해야 한다.

S460 fatigue crack-growth 자료는 Mendeley v2의 dataset-level CC BY 4.0 및 provider SHA-256을 확인해 workbook 한 개를 로컬 취득했다. [`FCGR workbook importer`](FCGR_WORKBOOK_IMPORT_KO.md)는 원 workbook을 배포하지 않고, 명시한 CT sheet/열/행과 단위만 SI crack-growth curve로 변환한다. 시험 주파수와 세부 환경 조건은 workbook에 확인되지 않아 unknown으로 유지한다. 따라서 자료는 ΔK 대 da/dN-per-cycle 조회에는 사용할 수 있지만 주파수 정합을 요구하는 성장수명 계산에는 사용할 수 없다. 여섯 CT sheet는 하나의 연구 안 specimen이지 여섯 독립 연구 검증이 아니다.

NIST CORR-DATA는 NIST의 공개 레코드와 출처별 권리 제한을 분리해 등록했다. 354,591바이트 archive의 공급자 SHA-256을 확인하고, CSV 24,721행·15열, 239개 비어있지 않은 reference key 및 혼합 rate token 구조를 로컬 집계 감사했다. 제3자 원자료 권리가 확인되지 않은 포인트 관측값은 모델 적합·배포에 사용하지 않으며 archive는 공개 패키지에서 제외한다. [상세 감사와 권리 경계](NIST_CORR_DATA_KO.md).

304L chloride-induced SCC salt-loading 자료는 Mendeley Data version 1의 dataset-level CC BY 4.0 선언과 논문 인용을 확인해 로컬 제외 캐시에 보관했다. 제공자 ZIP은 81,799바이트, 내부 ZIP은 327,326바이트, Excel workbook은 327,096바이트이며 각각 관측 SHA-256을 기록했다. 제공자 checksum은 확인할 수 없어 local digest는 재현성 pin일 뿐 공급자 checksum 검증이 아니다. workbook은 5개 시트이고 수식 셀이 있어 계산 캐시·표 구조·시편 계층을 별도로 확인해야 한다. 구조 감사는 수식 수·시트 크기만 집계하며 headers·원자료 관측값을 공개 보고서에 복사하지 않는다. 제3자 권리와 physical replicate 구조 검토 전에는 수치 추출·모델 적합에 사용하지 않는다. [원자료 기록](https://data.mendeley.com/datasets/mrwrphjvjr/1), [연관 논문](https://doi.org/10.1016/j.mtla.2019.100509).

Thermal-spray 단면·두께의 다음 독립 검증 후보와 대용량 archive 취득 전 안전·권리 검토는
[`THERMAL_SPRAY_DATA_REVIEW_KO.md`](THERMAL_SPRAY_DATA_REVIEW_KO.md)에 기록한다.

BAM controlled wire-cut acoustic-emission 자료는 CC BY 4.0 Zenodo 기록
`10.5281/zenodo.22011152`에서 text waveform 11개, coordinate table과 event-feature table만 선별
취득했다. Waveform은 5 MHz·16,384표본씩 총 180,224표본이다. Source-label/coordinate 불일치와 C_A2
channel 10 누락을 유지하며 arrival pick·wave speed·event grouping을 추정하지 않는다. Binary DB와 PDF는
취득하지 않았고 localization, mechanism, severity, acceptance, life 또는 POD로 자동 변환하지 않는다.

Silicate/sol-silicate coating adhesion 자료는 CC BY 4.0 Zenodo 기록 `10.5281/zenodo.4777893`에서
README와 adhesion workbook만 선별 취득했다. `ADHESION` sheet의 35개 그룹·107개 raw replicate를
formula summary와 분리한다. 원본에 adhesion 단위, dolly 면적/force, break mode, calibration과 불확도가
없고 substrate가 wood이므로 provider-native 값으로만 보존하며 금속 코팅 자격화에 사용하지 않는다.

CREATE Year1 음극방식 자료는 CC BY 4.0 Zenodo 기록 `10.5281/zenodo.18735817`에서 OCP 3개,
potentiodynamic 2개와 CP workbook 1개만 선별 취득했다. DPlot CSV의 8곡선·11,922표본과 provider
checksum을 검사한다. Calomel 기준전위는 보존하지만 분극 current-axis 지수는 미확정이며, 노출·전극·
면적·불확도 metadata가 불완전해 보호기준, 부식전류 또는 부식률로 자동 변환하지 않는다.

ESCAPE‑1 통제 지하 천연가스 누출 [CC0 자료](https://doi.org/10.5061/dryad.8931zcrwq)의 11개
workbook과 README를 취득하고 provider MD5를 모두 확인했다. 118,606개 path-integrated methane
응답은 ppm·m, 시각은 provider Mountain Time의 time-of-day로 보존한다. README가 식별한
5·10·20 slpm의 기준 온도·압력과 trace별 release window가 없으므로 SI molar flow로 변환하거나
leak-response calibration에 자동 사용하지 않는다. 상세는 [기준누설 자료 경계](POLYMER_EROSION_LEAK_KO.md)다.

FABEST LCF v2는 CC BY 4.0 Zenodo 기록의 main archive와 update 안내를 제공자 MD5로 취득했다.
main archive는 24개 calibration experiment, 96개 수치 CSV, 25,213,349 data row와 7개 header
계열을 포함한다. Case 4-5 폴더에는 공개 outcome CSV가 없다. `fabest_lcf_data.py`는 archive를
추출하거나 provider 파일을 실행하지 않고 구조를 감사하고 검토된 header로 수치행을 streaming한다.
원 archive·보고서·template·점별 행은 공개 배포에서 제외한다.

316L 국부부식의 [SECCM-SEM/EBSD 공개 자료](https://doi.org/10.5281/zenodo.18668632)는
고정한 동반 저장소 README가 “Data: CC BY 4.0 via Zenodo”라고 선언한다. 다만 2026-10-29에 확인한
Zenodo HTML의 Rights 영역은 라이선스 식별자를 표시하지 않아 이 두 근거의 표시 차이를 catalog에 남겼다.
원 ZIP은 계속 배포물에서 제외한다. 9,683,560바이트 ZIP의 제공자 MD5와 프로젝트 SHA-256을 모두 확인했다. 열 개
구성 파일 중 raw chronoamperometry 표의 205개 map point, 각 7,782개 시간·전류 표본을 전수
검사한다. 시간은 0–59.9915 s에서 엄격히 증가하고 원 전류는 A 단위로 유지한다. 제공자 descriptor,
label, footprint, SEM/EBSD와 model table은 역할만 분리했으며 행·좌표 정합은 아직 자격화하지 않았다.
상세 범위는 [SECCM 자료 계약](SECCM_316L_PITTING_DATA_KO.md)을 따른다.

AA7050 한 시편의 2일·6일 국부 공식 형태와 micromechanical stress·strain MAT 네 파일을 제공하는
[CC BY 4.0 공개 자료](https://data.mendeley.com/datasets/hhf5sfk5bj/1)를 선택 취득 대상으로 등록했다.
네 파일 127,766,005바이트는 모두 제공자 SHA-256과 일치한다. 2일·6일 형태 배열은 각각
2,845×3,931과 2,849×3,968, strain 7개 배열은 851×1,199, stress 10개 배열은 230×291이다. 전 값은
유한하지만 형태 두 시점부터 shape가 다르므로 index-wise 차분은 구조적으로 차단한다. 좌표 정합,
단위, pit 정의 또는 시간 전이는 별도 근거 없이 추정하지 않는다. [자료 계약](AA7050_LOCAL_PITTING_DATA_KO.md)을 따른다.

표면영상 후보와 권리·시편·절차 경계는 `VISUAL_DATA_REVIEW_KO.md`에 기록한다. CC BY 4.0의
판재 균열 다시점 영상 자료를 optional 취득 대상으로 등록했으나, 전체 ZIP과 제공자 MD5 검증이
끝나기 전에는 위 취득 파일 수·바이트에 포함하지 않는다. 부분 다운로드는 연구 캐시에만 남고 공개
배포물에는 포함되지 않는다.

저합금강 용접금속의 [Aalto EBSD 자료](https://zenodo.org/records/5054204)는 Zenodo API가 선언한
CC BY 4.0 및 제공자 MD5를 확인해 선택 취득했다. ZIP은 53,622,850바이트이고 MD5
`52241fb4b5aef61c162e6dbc6b47a5b4`, 취득본 SHA-256
`9c02bf44f8bd34afff432e6f78d0bd4cf176a75a544fb18ac6d83938a667c436`이다. 안전한 archive 검사에서
`CV_3`, `HY_1`, `LA_1` 각 쌍의 Oxford `.cpr/.crc` 여섯 파일을 확인하고 ZIP CRC 검사를 통과했다.
CPR의 제공자 메타데이터는 각 map을 1245×934, X/Y grid-distance 값을 0.1로 기록하지만 그 물리 단위는
확정하지 않는다. 프로젝트에는 선택 DefDAP reader와 aggregate-only validation command가 추가됐으며,
reader 계산은 아직 실행하지 않았다. 원본 ZIP은 `data/raw` 제외 경로에만 보관한다. 향후 reader 성공도
label 의미·좌표 정합·독립 시편 수·ROI·면적 scale·측정불확도를 자동 자격화하지 않는다.

방사선투과검사 후보와 제외 근거는 `RADIOGRAPHY_DATA_REVIEW_KO.md`에 기록한다. X-weld Zenodo
archive는 공급자 metadata license와 checksum만 확인한 기본 비활성 후보이며, 촬영조건·물리 시편·
annotation truth가 없어 위 취득 파일 수·바이트나 검증 자료에 포함하지 않는다.

위상배열 공개자료 후보와 권리·시편·augmentation 경계는 `PHASED_ARRAY_DATA_REVIEW_KO.md`에
기록한다. ML-NDT는 고정 Git commit의 metadata를 전수 조사했지만 2.63 GB repository data를 공개
배포물이나 취득 완료 집계에 넣지 않는다. 별도 local clone reader는 UUID quartet·형상·label/JSON과
SHA-256을 검사하되 원자료를 취득하거나 복제하지 않는다. Strathclyde PAUT.zip도 provider checksum을 확보하고 실제
다운로드를 검증하기 전에는 취득 자료로 세지 않는다.

TOFD의 Mendeley `10.17632/sggn77wv29.1`은 CC BY 4.0의 2D 유한차분 용접부 simulation 후보지만
동적 file tree와 checksum을 아직 확보하지 못해 metadata-only다. 64개 기하 case는 계산 case이지
독립 물리 시편이 아니며 위 취득 집계에 포함하지 않는다.

도금강 분극의 공개 연구 파일을 선택 취득하고 6쪽 시험 방법과 실제 24곡선을 대조했다. 순서·부호·단위·기준 전극·명목/실제 끝 전위 차이를 보존하며 침지 깊이를 노출 면적으로 바꾸지 않는다. `scripts/inspect_polarization_data.py`가 제공자 체크섬·원 행·공개 메타데이터를 대조한다. `corrosion.mixed_potential`의 실제 결합 면적·저항·준정상 전달과 독립 결합 시험 검증은 남아 있다. [분극 설명](ELECTROCHEMISTRY_KO.md)을 따른다.

CMSX-6 자료는 [BAM 공개 자료 v1](https://doi.org/10.5281/zenodo.14750432), CC BY 4.0에서 workbook 1개와 LIS 12개를 취득했다. 제작·열처리한 단결정의 [001] 기준 방향 편차가 있는 시편이며 하나의 명목 온도 1253.15 K, 초기 명목 응력 140·170·200·230 MPa에서 각각 세 시편이다. 정하중의 초기 명목 응력은 시험 중 일정한 진응력과 다르다. 140 MPa의 세 시험은 시간 한도로 중지됐으며 파단으로 세지 않는다. 12개 처리 시계열의 140,032행과 중복 시각 23구간을 보존한다. LIS는 h·%·°C를 명시하므로 파일 단위를 사용해 SI로 변환한다. workbook의 경과시간 설명에 있는 s와의 차이도 로더 속성에 남긴다. 마지막 표본을 파단 시각으로 대체하지 않는다.

각 응력 수준에서 시편 ID SHA-256이 가장 작은 하나를 보류하는 고정 규칙을 사용했다. 보정 8개는 파단 6개·미파단 2개, 보류 4개는 파단 3개·미파단 1개다. `stress_only` 적합의 응력 지수는 약 6.1872, 로그 수명 산포는 약 0.04698이고 보류 파단의 자연로그 수명 RMSE는 약 0.02694다. 소규모 동일 출처 비교이며 독립 기관·재료·기구 검증이 아니다. 활성화에너지는 `null`로 남기고 실제 단일 온도 자료로 추정하지 않는다. 조사 집계에는 원 시편별 수명·잔차·파형을 포함하지 않는다. 라이선스·저자·변환 내용은 카탈로그와 제3자 고지에 유지한다.

| 자료 | 실제 확보·조사 | 허용된 초기 활용 |
|---|---|---|
| 탄소강 1년 대기부식 | 프로그램 617행·독립 연구 106행, 170개 site 및 16개 독립 연구, A/B/C 등급 보존 | ERA5 조화 공변량을 이용한 1년 평균 손실의 source-group 전이 진단. 원 관측 권리·시편 독립성·국부/다년 성장은 추정하지 않음 |
| 이질적 습식 CO₂ 부식 편집본 | 수치 427행·8열, 완전행 243개, 완전 중복 원값 3행. CSV는 단위를 생략했지만 연계 preprint에서 전 열 단위와 네 유형의 집계 수량 확인. 별도 CC BY 4.0 workbook과 처음 243행의 헤더·위치·8개 수치가 전부 정확히 일치 | 처음 243행만 하나의 모의 모델 출력 source group으로 표시한다. 물리 관측이나 독립 검증으로 쓰지 않는다. 나머지 184행은 행별 출처·시편·재료·노출시간이 없으므로 보정과 CoolProp 연결을 중지 |
| NORSOK M-506 모의 격자 | CC BY 4.0 workbook 243행, 8개 열과 단위표, SHA-256 `da4548f34ffb9c4fac2516b9d40eab18d57f6111f48f3aeb051ab092ccba2eae` | 이질적 편집본 처음 243행의 출처 대조에만 사용. NORSOK 규격·코드·표의 재배포 권리나 물리 검증으로 확대하지 않고 공개 surrogate는 별도 권리·적용성 검토 |
| HE-Austenite | 가스 수소 문헌 편집본 113행·9개 출처·31개 성분 연결 그룹 | 사전 충전/시험 중 노출·모재/용접 부위·미확정 단위·성분 충돌을 보존. 시편 독립성·원 문헌 권리 검토 전 보정·재배포는 보류 |
| 탄화물 수소 트랩 실험 | 전체 ZIP 2,644,569,048바이트·162개 파일, 제공자 MD5 대조 | DFT 표·APT·현미경·투과/TDS 자산 분류. OPJU 2개 내보내기와 TDS 질량 ppm 기준 검토 완료. 투과 기하·면적·전위 기준과 곡선별 시편은 미확정 |
| BAM CMSX-6 | 정하중 12시편: 파단 9·시간 한도 미파단 3, 처리 시계열 140,032행 | 단일 지정 온도의 검열 응력 수명 적합과 8/4 보정·보류 비교. 실제 다중 온도·활성화에너지·변동 이력 검증은 미완료 |
| NIST CORR-DATA | archive 구조감사: 24,721행·15열·239개 reference key. rate 열의 수치 scalar 5,896/5,823개, range 토큰 16/15개. | aggregate archive/schema 감사만 제공. 개별 행의 출처권리·조건 확인 전 조회·모델 적합·재배포는 보류 |
| COQTEL | 316L 부식 초음파 실험 2개, 166·263개 상태 | 전기화학 적분과 파형 변화 특징. 결함 깊이·POD 보정은 미완료 |
| CEIT 해안 노출 균일부식 | S355 표식 시편 1개, 2,715개 장치 레코드와 네 신호 배열 | 원 시계·ID·ToF·온도·ADC rail 보존. JSON 내부 단위·음속·경로·독립 치수 검증이 없어 두께·부식속도·수명으로 변환하지 않음 |
| Hannover 용접부 | 피로 248행과 형상·불완전부·FE·용접 토우 자료 | 시편·처리·응력비를 구분한 검열 수명 적합 |
| 수소 316L | 인장 시편 6개, 경도 시트 6개 | 적층제조·전해 충전 조건의 재료 관측. 가스 수소 설비로 일반화하지 않음 |
| MetroPT-3 | 실제 압축기 1,516,948행 | 운전 시계·신호·단위 연동. 부식 성장·고장빈도 정답은 없음 |
| BAM 복합결함 와전류검사 | CC BY 4.0 simulation CSV 12개와 laboratory DICONDE 10개, 제공자 MD5 및 로컬 SHA-256 대조 | 원 정수 component·좌표·frame별 rescale metadata의 구조 감사. 결함 치수 truth, POD, 합격판정 또는 상용 solver 재현으로 사용하지 않음 |
| 연속 pipeline ILI 이력 | CC BY 4.0, 공급자 SHA-256이 있는 4개 XLSX 269,180,366바이트와 README PDF 확보; 3,198,420행 전수 감사 | 처리·필터된 외부부식 이상 기록. `Year`는 실제 설비 나이가 아니며 raw MFL flux·센서 교정·lift-off·속도·excavation truth가 아님. 행을 자동 feature track이나 성장 정답으로 연결하지 않음 |
| HyMatBase 4130X 수소가스 피로 | provider MD5와 일치하는 workbook 55,972바이트, R·주파수별 4곡선·271점 | record 4.5 MPa와 workbook 45 MPa의 충돌을 보존. Rights 미기재로 원파일·점별 표는 재배포하지 않으며 시편 identity·시험 유효성 확인 전 성장곡선 보정에 사용하지 않음 |
| Steel Plates Faults | 제작 결함 특징 1,941행 | 제작·표면 결함 데이터 계약·분류 연구 |
| PEM 코팅 자료 | 초기 ZIP 2개 | 자료 구조 확인. 현재 선택한 자산은 수치 보정 테이블로 사용할 수 없음 |
| BAM P92 | 시험 3개, 파형 630,582행·기록 사이클 376/216/276개 | 최대·최소 표와 파형 peak 일치 확인. 열린 경로의 일과 끝점 차이를 보존 |
| FABEST | 60개 고주기 그룹 관측 663행, 변형률 수명 8행 | 정적 기준점 60개·회귀 출력점 2,885개 분리. break cycle 567·provider interruption 95·미확정 1행을 구분하고, 문자 접미사·주석·누락 END 기준을 검토 상태로 보존. 매크로 실행 없음 |
| FABEST HCF blind competition | v2.1.2 ZIP 46,329,584바이트, 목표조건 20행, 제출대상 20행 | 네 프로토콜 해시와 압력저하 끝점·runout·계통중단 재개 규칙 감사. 정답 피로강도·수명은 비공개이므로 입력·종료계약 검증에만 사용 |
| ECP 다축 피로 | FS/SWT 각 14파일·147행, 중복 제거 실험수명 147개, 조건 14개 | 같은 수명을 반복한 방법별 처리행 294개를 독립 시편으로 세지 않음. 물리 시편 ID·검열·끝점·국부 tensor/FE field는 미제공 상태로 보존 |
| 도금강 분극·표면 시험 | 산·염화물 3종, 24개 곡선·19,680개 측정점과 성분·코팅두께·경도·Tafel 요약 | 부호 있는 전류밀도 A/cm²를 A/m²로 변환. 저항의 면적 정규화와 Tafel 구간 선택은 별도 확인 |
| 부식저항 합금 전기화학 지표 편집본 | 6개 지표 시트·1,268개 원행·3,579개 지표 셀, 참조목록 85개 | Exact 1,605·문자 숫자 1·하한 14·상한 2·정성 44·누락 1,913을 분리. SCE 기준과 시험환경을 보존하고, 물리 시편·시험 유효성·원 관측 권리는 미확정 |
| Charpy 충격시험 편집 자료 | 4,961행·56열, 원 문헌 109개, 수치·형상이 유효한 4,871행 | 원 문헌·형상·방향·재료/조사 조건을 보존한 기술적 곡선 적합. 원본과 점별 파생 관측의 재배포는 보류 |
| WILLOW 합성 초음파 | 3·5 mm 두 영역, 특징 2,000행 및 501표본 파형 2,000개 | MAT 유효 기하와 특징표 SI 변환 전수 대조. 처리 성공 996·974행, 유한 원 파형 1,000·975개. 합성을 현장 실험으로 표시하지 않음 |
| 배관 유도초음파 SHM | 한 실험관의 acquisition 236개·5주파수 신호 1,180개·숫자 2,958,260행 | 건강 기간 207·가공 후 29 구간만 고정 원본에 적용. 가공 6단계 대응·두께·시각·온도·POD는 미확정이며 전압을 직접 두께로 쓰지 않음 |
| WILLOW HarshLab | 두 실제 노출 시편의 308·466개 반복 기록, 각 1,024표본 | 원 신호·특징표 시각 일대일 대조. 처리 성공 308·296개이며 초기 pit 치수는 시계열 참값이 아님 |
| 배관 파열 편집본 | 주 표 453행: 실제 시험 102건·FEM 351건, ZIP SHA-256 대조 | 보완 물성·추정 폭·미확정 문헌·지름 기준을 보존한 자료 계약. 원본·점별 파생값 재배포 및 자격 있는 파열압 검증은 보류 |

## 수용액 활동도 계수의 사용 경계

TUDOdata의 2024 mean ionic activity coefficient dataset은 공식 API에서 CC BY 4.0, 225개 파일, 225개 provider MD5가 확인됐지만, 실제 파일은 아직 취득하지 않고 `metadata_only`로 둔다. 제공자가 일부 계열의 출처로 1989년 상용 handbook 발췌를 명시했기 때문에 record별 원출처·권리와 fitted-model provenance를 먼저 해결해야 한다. 또한 자료량은 salt의 **mean ionic** coefficient이며, 질량작용 API의 종별 `activity_coefficient`와 같은 데이터가 아니다. 종별 γ로 변환하거나 그 자리에 대입하지 않는다. [`integration.aqueous_mass_action_vant_hoff_history`](AQUEOUS_VANT_HOFF_HISTORY_KO.md)는 caller가 별도 검토한 종별 coefficient vector를 절점마다 받을 수 있지만 이 공개 자료를 직접 소비하지 않는다. [공식 TUDOdata API record](https://data.tu-dortmund.de/api/datasets/:persistentId/?persistentId=doi%3A10.17877/RESOLV-2024-M4WGMZTG).
| 1D rod 과도 열전달 | 원시 77 run·215,001 시간행·1,290,006 열전대 관측, 처리 적합 77행 | 시간·TC1~TC6·controller setting·음수 초과온도 보존. 처리 계수는 같은 관측의 적합값이며 독립 검증으로 세지 않음 |
| C1/C2 crack-arrest | C1 9파일·C2 9파일, signed machine channel 79,341행 | 원 0.05초 시계·변위·힘·extensometer·cycle을 보존. 기하·유효성·reduction 검토 전 toughness나 FAD 검증값을 만들지 않음 |
| 전이구간 파괴인성 편집본 | training 448행·test 192행, 14재료, CT 394·SEB 165·PCCv 81행 | 보고 KJc·항복강도·형상과 분할을 보존. 논문 근거로 온도는 °C→K, W/B/a는 검토된 mm→m 변환을 하되 workbook 표기 부재·충돌을 기록. 논문 표의 출처 그룹은 정확 614·유력 변형 18·미해결 8행으로 구분하고 9개 서지 중 DOI 7개를 확인. 행별 원 문헌/시편 ID와 모든 원 관측 재배포 권리는 미확정이고 FAD 자동 연결은 중지 |

NIST·Charpy·배관 파열 편집본을 제외한 취득 묶음은 제공자가 CC BY 4.0으로 표시했다. NIST는 제품·기여자별 조건을 검토해야 한다. [Charpy 편집 저장소](https://github.com/avakanski/Charpy-Impact-Test-Dataset)는 MIT를, [배관 편집본](https://doi.org/10.17632/77t4k43y7g.1)은 CC0를 선언한다. [과도 열전달 자료](https://doi.org/10.17632/sbcf36976g.1)는 CC BY 4.0으로 표시된다. 이 선언을 각 원 문헌의 관측 전체에 대한 권리 확인으로 확대하지 않는다. 원 문헌 식별자를 보존하고 원본·점별 파생 관측은 공개 배포에서 제외한다. 재배포 조건은 다운로드 성공 여부와 별도로 `data/catalogs/datasets.json`에서 추적한다.

2026-10-19 버전 [AquaSolDB v2.1](https://doi.org/10.5281/zenodo.23470595)은 CC BY 4.0 컴파일 편집본이다. 제공자 라이선스 문서가 각 실험 측정값을 라이선스 대상에서 제외하고 원 논문 인용을 요구하므로, 고정 archive는 로컬 제외 저장소에만 둔다. CO₂ 용해도 7,194행 중 저압 순수물·partial-CO₂ 조건 후보는 탐색 필터 아래 41행·8개 출처지만 해당 값이 Henry 계수나 부식률 보정점으로 자격화됐다는 뜻은 아니다. 이 프로젝트는 점별 수치·원 논문 인용 문자열을 배포하지 않고, 상태/표식·매질·압력 기준과 범위 통계만 저작자·DOI 귀속과 함께 공개한다. 원자료는 `iter_aquasoldb_co2_solubility`가 provider digest로 검증해 사용자 프로세스에서 읽는다.

[ECP 다축 피로 자료](https://doi.org/10.5281/zenodo.14198237)는 CC BY 4.0이다. 28개
파일의 294행은 FS/SWT 처리쌍이며 실험수명은 147개다. 물리 시편 ID와 검열·끝점 정의가
파일에 없으므로 행 번호에서 만들지 않는다. [다축 피로 자료 계약](MULTIAXIAL_FATIGUE_DATA_KO.md)에
pair 검증, 공개 범위와 후속 조건을 기록한다.

[부식저항 합금 전기화학 지표 편집본](https://doi.org/10.6084/m9.figshare.13038257.v2)은
CC BY 4.0 workbook이다. 피팅·재부동태·틈부식 전위, 임계 피팅·틈부식 온도와 부식전위·
전류밀도·부식속도를 같은 점수로 합치지 않는다. 로더는 원행과 지표 통계량을 분리하고
`Transpassive`, `>800`, `<-2.5`, `NA`를 서로 다른 상태로 유지한다. 전위는 SCE 기준을
버리지 않은 채 V로, 온도·전류밀도·부식속도는 각각 K·A/m²·m/s로 변환한다. 공개 설명은
81개 문헌을 말하지만 workbook 참조 시트에는 번호 85개가 있고 지표 원행은 84개 번호를
사용하므로 이 차이를 보존한다. 참조번호·DOI는 source group이지 물리 시편 ID가 아니다.
편집 workbook의 라이선스는 각 원 문헌 관측의 재배포 허가로 확대하지 않으며 원본과 점별
변환 행은 공개 배포에서 제외한다. 집계 감사는 `validation/corrosion_alloy_metrics_package.json`에
있다.

## 데이터 품질 처리

C1/C2 [crack-arrest 원자료](https://doi.org/10.17632/g69875w65c.1)는 CC BY 4.0의 18개 CSV다. 파일명에서 읽은 온도 범위는 150.15~296.15 K이나 실제 시편 온도 로그와의 독립 대조 전에는 `filename_parsed_unverified`로 유지한다. 전체 79,341행의 시간 간격은 0.05 s이고 힘 채널의 음수 76,285개·양수 3,056개를 반전하거나 0으로 자르지 않는다. 한 파일의 전체 헤더 인용 형식만 정확한 열 이름으로 복구한다. machine/extensometer displacement의 원 zero와 부호를 유지하고 event picking·compliance correction을 하지 않는다. Crack arrest와 initiation toughness, FAD 경계와 실제 부품 파괴는 서로 다른 근거다. [파괴평가 기록](FRACTURE_ASSESSMENT_KO.md)을 따른다.

[전이구간 파괴인성 편집 자료](https://doi.org/10.17632/2vkgrbsy8j.1)는 CC BY 4.0으로 공개된 workbook 한 개다. 고정 ZIP SHA-256은 `d1007e9b3a3802594f169a15e72a94353a674cb72daf2faef93f9ae9fabdf66f`다. 640행의 reported KJc 범위는 36.1~255.4 MPa√m이고 항복강도 범위는 348.8~990.1 MPa다. Training과 test 사이 완전 동일 관측 행은 없지만 물리 시편 독립성을 뜻하지 않는다. 원 온도 열은 `K`로 표기됐으나 −160~100 값을 갖는다. [연계 논문](https://doi.org/10.1016/j.engfailanal.2020.104458)은 machine-learning의 시험 온도 특징과 재료별 온도 범위를 °C로 명시하므로 reader는 출처 충돌을 기록하고 113.15~373.15 K로 변환한다. Workbook의 W·B·a에는 단위가 인접 표기되지 않았지만 논문은 이를 폭·두께·균열길이로 정의하고 T 크기와 연구 두께를 mm로 명시한다. 전 행의 B 4.07~101.6이 그 척도와 일치하므로 기본 `article_mm`에서 0.00407~0.1016 m로 변환한다. 원 표기 부재와 검토 근거를 분리하며, 파생 workbook은 검토 비활성화 또는 명시적 override를 사용한다. 재료·시편형식·W/B를 3% 또는 0.1 mm 허용오차로 묶으면 34개 형상 조건 그룹이며 전부 training과 test에 함께 나타난다. 이 그룹은 분할 누설 점검용일 뿐 물리 시편 ID나 독립성 근거가 아니다. 같은 논문의 재료 표와 탄소량을 대조한 article-local 그룹은 614행이 정확히 맞고, `S55CFY2012` 18행은 표의 `S55C`와 이름·탄소량이 조금 달라 유력 변형으로만 둔다. 표에서 대응을 찾지 못한 `SS400` 8행은 미해결이다. 참고문헌 9개 중 DOI 7개를 확인했지만 workbook에 나타나는 것은 DOI 그룹 176행·보고서/학위논문 서지만 확인된 그룹 456행·출처 그룹 미해결 8행이다. 출판물의 공개 접근·TDM·논문 라이선스는 편집 관측의 재배포 권리와 다르므로 640행 모두 관측 권리는 미확정으로 둔다. 원 문헌 행·시편·유효성 연결도 별도 검토가 필요하다.

과도 열전달 자료 ZIP은 원시 CSV 77개와 처리 workbook 3개를 포함한다. CSV의 215,001개 시간행은 TC1~TC6의 1,290,006개 온도 관측을 제공하며, 주변온도를 뺀 값 중 음수 28,161개도 그대로 보존한다. controller의 `Power (1023 Max)`는 장치 설정값이므로 W·발열률·열유속으로 해석하지 않는다. 설정 변화가 있는 run은 현재 0개이고 주 시간 간격은 0.2 s이나 0.21 s도 존재하므로 원 시계를 사용한다. 처리 표의 열전도율·대류계수·전력·경계 ramp/delay는 같은 원시 run에 대한 적합 결과다. 원시 관측과 적합값을 독립 표본처럼 합치지 않는다. 로더·재현·남은 조건은 [열구배 설명](THERMAL_GRADIENT_KO.md)에 있다.

HE-Austenite는 [고정 공개 자료](https://doi.org/10.5281/zenodo.23107780)를 취득했다. CSV 파일명은 v1.0, 동봉 설명의 버전 표기는 v0.2이므로 이름만으로 내부 일치를 가정하지 않는다. 113행은 시편 수가 아닌 조건·물성별 보고 행이며 모재 53·전체 이음부 40·용접금속 20행, 사전 가스 충전 59·시험 중 가스 노출 54행이다. 서로 다른 물성이 같은 시험에서 나왔을 수 있고 97행은 heat ID가 없다. 편집자 검토 표식은 24행에 있으며 이 패키지의 원 문헌 재추출이 아니다.

성분표와 연결표는 31개 조성을 102행에 연결하지만 15행에서 주 CSV의 성분과 다르다. 두 값을 보존하고 임의 선택·평균·덮어쓰기를 하지 않는다. 65행에는 편집자가 일부 원소를 0으로 둔 파생 지표 가정이 있다. 원 성분의 미보고 항목은 누락으로 유지한다. 10행은 절대 물성 없이 보존비만 있고 17행의 비는 1보다 크므로 손실 방향으로 잘라내지 않는다. 소성 파단변형률 4행은 단위를 확인하기 전 SI 값으로 만들지 않는다. 압력은 total/partial·absolute/gauge 기준이 표에서 명확하지 않으며 충전 온도와 인장시험 온도도 다르므로 직접 기체 상태·수송 경계조건으로 바꾸지 않는다. 원 문헌별 권리와 시편·동일 조건/값 13행의 관계는 추가 검토 대상이다.

[탄화물 트랩 자료](https://doi.org/10.5281/zenodo.10416768)는 1차 [공개 연구](https://doi.org/10.1038/s41467-024-45017-4)의 데이터다. 전체 ZIP은 APT 4파일·DFT 139파일·투과/TDS 3파일·전자현미경 16파일을 포함한다. DFT workbook의 4개 시트는 에너지 행렬이며 투과 시계열이 아니다. `H Permeation test.opju`, `TDS.opju`는 공식 Viewer로 읽어 고유 CSV 9개·중복 2개를 기록했다. 투과 40,859행과 열탈착 18곡선 98,983점을 로더로 확인했으며 원시 채널·파생 적분·요약을 분리했다. 공개 보충자료로 TDS가 시편 질량 기준 수소 질량 ppm임을 확인했고, 투과 요약 오차 막대는 적어도 두 측정의 표준편차로 확인했다. 축의 표시 배율을 이중 적용하지 않고 시간 불일치·음수·누락·미충전 대조를 보존한다. [수치 내보내기 기록](HYDROGEN_EXPORTS_KO.md)에 따라 곡선별 시편·투과막 두께·전극 면적·전위 기준·경계조건을 더 검토해야 한다. 확장자만 OPJ로 바꾸거나 내장 스크립트를 실행하지 않았다. 제공자 CC BY 4.0과 실제 해시를 보존하며 원본·점별 관측은 공개 배포하지 않는다.

추가 후보 중 [LH2CRAFT](https://zenodo.org/records/21493116)는 현재 파일 공개 예정일이 2028년 12월 31일이므로 취득하지 않았다. [HyMatBase의 Sandia 연관 자료](https://hymatbase.stfc.ac.uk/records/j1e8n-2bz97)는 파일 권리 정보가 명확하지 않아 현재 카탈로그의 문서별 검토 경계를 유지한다. [2026년 격자변형 DFT 자료](https://doi.org/10.5281/zenodo.19038479)는 계산 자료이며 실험 투과 기록으로 분류하지 않는다.

등급·상한·하한·구간을 임의의 한 점 부식속도로 바꾸지 않는다. 반복 시편을 독립 표본으로 세지 않고, 미파단 시험은 검열 정보로 보존한다. 가공된 회귀 곡선을 원시 실험 관측으로 취급하지 않는다.

COQTEL의 전기화학 시간은 분 단위다. 시각과 전류·전위가 같은 반복은 명시된 정책으로만 보존해 적분한다. BAM은 같은 시각에 서로 다른 파형 값이 기록되는 경우가 있으므로 순서를 그대로 보존하고 시계 해상도 미확정을 표시한다. 이 자료를 더 미세한 시각으로 임의 보간해 시간 미분에 사용하지 않는다.

BAM의 최대·최소 표도 전체 시험의 모든 사이클을 포함하지 않는다. 세 파일의 기록 범위 안에서 각각 2,171·1,220·1,478개 사이클 번호가 관측되지 않는다. 기록된 사이클의 stress peak는 두 표에서 일치했다. ∫σdε는 시간 미분 없이 계산하지만, 각 경로의 양 끝 변형률이 같지 않으므로 그 값을 자동으로 닫힌 피로 사이클의 소산으로 사용하지 않는다.

FABEST의 663행 중 662행은 기본 끝점·수치가 있다. Provider `finished/interrupted`와 별도 break-cycle 열을 대조하면 break cycle 보고 567행, provider interruption 95행, 미확정 1행이다. 60개 곡선 sheet 모두 데이터 사전에 정의된 `END` 기준을 실제 곡선 메타데이터에 제공하지 않는다. 따라서 interruption을 runout으로, break-cycle 열을 독립적으로 확인된 완전 파단으로 자동 확정하지 않는다. 문자 접미사 54행은 재시험으로 정의되지 않아 `letter_suffix_semantics_unresolved`로 바꿨다. 끝점 주석 89행 중 15행은 interruption과 함께 있고, 나사부 관련 13·그립부 fretting 1·제외 표식 2·실수 1·buckling 의문 3·온도 문자열 8행을 검토 태그로만 보존한다. Break cycle과 `no crack` 계열 주석이 함께 있는 18행도 충돌을 제거하거나 한쪽으로 판정하지 않는다. 소규모 FAB005 적합은 선별된 행에서만 provider interruption을 우측 검열로 가정한 기술적 시범이며 서비스용 재료 곡선이 아니다. 상세 계약은 [피로자료 설명](FATIGUE_DATA_KO.md)에 있다.

MetroPT의 주된 기록 간격은 10초이며 9·12초 등도 섞인다. 실제 시각 열을 사용한다. 압력의 게이지·절대 기준은 미확정이므로 열역학·응력 모델에 투입하기 전에 외부 근거로 확정해야 한다.

Charpy의 보고 곡선 ID는 293개지만 재료·성분·처리·조사·형상·방향을 함께 대조하면 532개 조건 그룹으로 나뉜다. ID 6과 271에는 서로 다른 조사 조건이 들어 있으므로 ID만으로 합치지 않는다. 동일 보고 행 25개는 표식만 남기고 자동 삭제하지 않는다. 온도 누락·무효 5행과 불완전 형상 85행을 식별했다. 조건 그룹과 행 ID가 같거나 다르다는 사실만으로 시편 독립성은 증명되지 않는다.

원 곡선 1의 비조사 L 방향 14행에 한정한 시범 적합을 수행했다. 50 J 교차는 약 271.42 K, 잔차 RMSE는 약 12.39 J다. 50 J는 설명용 목표이며 규격 기준이 아니다. 이 값은 같은 관측을 적합한 결과로서 독립 검증·파괴인성·허용 사용온도를 제공하지 않는다. 공개 조사 기록에는 원 관측을 복원할 수 있는 점별 적합값·잔차를 넣지 않는다.

WILLOW의 [합성 자료](https://doi.org/10.5281/zenodo.22677451)와 [실제 노출 자료](https://doi.org/10.5281/zenodo.22673386)는 각각 별도 데이터 묶음이다. 합성 MAT의 길이와 표의 길이를 m·mm로 읽으면 깊이·폭·변환자 치수의 최대 차이는 약 4.34×10⁻¹⁹ m다. 두 형식에 공개된 파형 시간축은 없어 sample interval을 만들지 않는다. `valid`는 문자·숫자·bool을 명시적으로 해석하며 처리 성공과 개별 특징의 유효성을 구분한다. 일부 peak 특징은 처리 성공 행에서도 누락된다.

HarshLab 시각의 시간대는 미확정이다. 주 간격은 21,600초지만 V212의 최대 공백은 4,172,162초다. V116·V212에서 기록된 gain 설정은 각각 3·5개, filter 설정은 1·2개다. 원 파형의 같은 진폭 척도·열 보정·결함 변화로 자동 해석하지 않는다. 두 시편의 초기 가공 깊이는 각 자료에서 한 값으로 유지되며 매 시점의 실제 pit 깊이가 아니다. 공간적으로 동등한 독립 검사 블록이 없으므로 이 자료에 면적 극값 모델을 적합하지 않는다.

`data/data_inventory.json`에는 두께·변환자별 누락률과 합성 유효 깊이 대비 미보정 신호 특징의 오차 요약이 있다. 이는 특징 진단이며 검증된 결함 치수 공급자나 현장 POD가 아니다. 원 관측은 배포에서 제외한다.

[배관 유도초음파 자료](https://doi.org/10.17632/ttb63krg6d.1)는 CC BY 4.0이다. 고정 외부 ZIP의 SHA-256과 내부 ZIP·236개 workbook manifest를 기록하고 legacy XLS의 1,180개 sheet를 전수 검사했다. 실제 sheet는 모두 2,509×4이며 논문 설명의 2,057×4와 다르다. 9종의 sheet 순서, 각 sheet의 반복 거리 한 구간과 전부 0인 provider DAC 열을 삭제·정렬·수정하지 않는다. 상세 API와 한계는 [유도초음파 자료 계약](GUIDED_WAVE_DATA_KO.md)에 있다.

## 재취득과 조사

도금강 요약 시트는 분극 저항을 Ω로 표시한다. 전극 면적이 확인되지 않은 저항을 Ω·m²로 간주해 Stern–Geary 모델에 넣지 않는다. 양·음극 부호를 보존하고 자동으로 Tafel 구간을 골라 부식속도를 만들지 않는다.

```powershell
.\.venv\Scripts\python.exe scripts/fetch_data.py
.\.venv\Scripts\python.exe scripts/inspect_open_data.py
```

`register_zenodo.py`는 명시적으로 검토한 자료를 추가할 때 사용한다. 공급자 이용조건이 바뀌면 기존 파일과 새 리비전을 구분해 다시 검토한다. NIMS 서비스처럼 대량 수집 금지 조건이 확인된 자료는 자동 취득하지 않는다.

## 남은 자료 공백

수소 실험의 공개 본문과 보충자료에서 TDS의 유한 원통 형상, 시편 질량 기준 수소 질량 ppm, 명목 100 K/h 프로그램을 확인했다. IP0→TiC와 IP2→(Ti,Mo)C는 파일 간 크기·요약 대조로 얻은 유력 대응일 뿐 물리 시편 ID가 아니다. 투과막 치수·전극 면적·전위 기준과 원시 요약의 곡선 대응은 별도 검토 대상이다. 충전 전류 크기는 흡수된 H flux가 아니며, 명목 가열률은 측정 표본 clock이 아니다. `protocol_review`는 확인한 사실과 누락을 분리한다. 유한 평판과 반경–축 유한 원통의 독립 수학 검증은 [수송 설명](HYDROGEN_TRANSPORT_KO.md)에 있으며 실제 TDS 보정으로 취급하지 않는다.

현재 확보 목록은 염화물·암모니아 SCC 성장, 가스 수소 피로의 폭넓은 재료·온도·압력 조건, 현장 국부감육의 검사 검출확률, 장기 크리프 파단 및 제작·열처리 규격별 허용값을 모두 충족하지 않는다. 해당 기능은 사용자 제공 자료 또는 추가로 허용된 원시시험·정식 공급자로 확장하며 기본 추정값을 만들어 검증 완료로 표시하지 않는다.

## 배관 파열 편집본의 구조

[배관 파열 편집본](https://doi.org/10.17632/77t4k43y7g.1)의 파일 API는 인증을 요구했지만 일반 공개 화면에 ZIP 주소와 SHA-256이 표시됐다. 그 경로로 76,500바이트를 취득해 제공자 해시와 대조했다. 원 요청 주소는 재취득에 사용하고, 공개 장부의 최종 응답 주소에서는 만료되는 query·서명·자격정보를 제거한다.

주 표 453행은 실험 102건·FEM 351건과 일치했다. 두 보조 시트는 추가 독립 시편으로 합치지 않는다. 색상 범례에 따라 항복강도 62셀·탄성계수 326셀이 참조 물성으로 보완됐고 폭 302셀이 기하 규칙으로 추정됐다. 같은 입력·압력 조합 9행은 모두 FEM에 있으며 자동 삭제하지 않는다. 14개 참조 표식 중 `Ma13Otros` 23행은 주 문헌 목록과 직접 연결되지 않는다. 편집 행 번호는 실제 시편 독립성의 증거가 아니다.

주 표의 지름 열에는 내경/외경이, 압력 열에는 절대압/차압 기준이 명시되지 않아 각각 `not_explicit_in_primary_table`로 남긴다. EXP의 시험 파열압과 FEM의 해석 실패압도 서로 다른 공급자 보고 역할로 보존한다. 깊이비는 0.8보다 명확히 큰 행이 16개, 0.8 부근의 반올림 경계가 3개다. 제공자 설명의 '19개 깊은 결함'과 이 차이를 함께 기록한다. 이 집계 허용오차는 설계 합격 기준이 아니다. 입력 형식·색상·단위 로더를 적용했지만, 문헌·지름·형상·보정 공급자 검토 전에는 실제 파열압 검증을 완료했다고 표시하지 않는다.

[Ma 등 원 논문의 출판사 페이지](https://doi.org/10.1016/j.engfailanal.2013.03.015)는 공개된 설명에서 문헌으로부터 전척 파열시험 79그룹을 수집했다고 밝힌다. 편집본에는 범례 문헌에 직접 연결되는 실험 79행 외에 `Ma13Otros` 23행이 따로 있다. 두 79라는 수의 일치는 행별 동일성이나 23행의 원 문헌·중복·시편 독립성·재배포 권리를 증명하지 않는다. 따라서 `Ma13Otros`는 Ma 논문과 관련된 편집 표식까지만 확인하고 원 관측 출처는 계속 미해결로 둔다.
Sapphire–copper reciprocating tribology 자료의 [Zenodo 기록](https://doi.org/10.5281/zenodo.7923128)은 CC BY 4.0이다. Zenodo에 직접 게시된 RDF Turtle 57개 파일 15,578,599바이트의 제공자 MD5를 전부 확인했다. 이 파일들은 experiment series, 장비, 시편, 소모품과 software metadata이며 원시·가공 측정값은 별도 기관 RO-Crate 링크에 있다. 따라서 현재 reader는 metadata 완전성과 digest만 감사하며 wear volume, Archard 계수, 독립 시편 또는 수명자료를 만들지 않는다. 상세는 [마모·경도·인장 계약](WEAR_HARDNESS_TENSILE_KO.md)이다.

Pressure-decay leak-test [Zenodo 자료](https://doi.org/10.5281/zenodo.20582921)는 API metadata에서 CC BY 4.0을 선언한다. Workbook 78,721바이트의 provider MD5를 확인하고 다섯 gas, 두 capillary length의 10개 series·310 pressure-temperature 표본을 감사했다. 설명에는 reference 상태와 ambient/internal gas temperature가 있지만 workbook에는 reference series가 없고 temperature 열도 series당 하나뿐이다. Gauge pressure, 미제공 vessel volume·blank·불확도 때문에 누설률, 결함치수, 합격 또는 확률로 변환하지 않는다. [상세 경계](CERTIFICATE_VACUUM_DISSIMILAR_WELD_KO.md)를 따른다.


## 라이선스 검토 시점 재확인

`data/catalogs/datasets.json`의 `checked_on`은 제공자 권리 근거를 마지막으로 검토한 날짜다. `scripts/audit_release_rights.py`는 ISO 날짜를 검증하고 기본 365일을 넘긴 자료를 구조 감사 통과 여부와 별도로 `review_date_freshness.status=older_than_threshold` 및 데이터셋 ID로 보고한다. 재현 실행은 `--as-of YYYY-MM-DD --freshness-days N`을 사용한다. `within_threshold`도 날짜가 설정한 기간 안이라는 뜻뿐이며 권리 검토 완료나 재배포 권한을 의미하지 않는다. 오래된 표시는 재검토 알림이다. 구조 검사가 통과해도 법적 clearance를 의미하지 않는다.

2026-10-29에 Zenodo 공식 record API를 다시 조회해 WILLOW 합성 pitting 초음파(22677451)와 HarshLab 현장 초음파(22673386)의 metadata license ID가 모두 `cc-by-4.0`임을 확인했다. 권리 근거 URL을 API record metadata로 연결하고 검토일을 갱신했다. 전자는 기하 truth가 붙은 시뮬레이션 자료이고 후자는 전처 pit 두 시편의 반복 현장 모니터링 자료이므로 독립 실험/일반 POD 자격화로 승격하지 않는다.

2026-10-31: UCI MetroPT-3 (DOI 10.24432/C5VW3R, dataset page CC BY 4.0) now has a local-only pinned archive audit and lazy typed CSV reader. The raw cache remains excluded; the channels are railway air-compressor process/predictive-maintenance context, not corrosion observations. A separate typed sample-row view now exposes the CC BY 4.0 Zenodo pressure-decay workbook (DOI 10.5281/zenodo.20582921) through the existing 31-knot parser. It retains provider-described gauge-pressure/temperature meaning and attribution, and does not infer leak rate because a reference state, volume and pressure basis remain unresolved. See the dataset-specific guides for hashes, exact fields and use limitations.
