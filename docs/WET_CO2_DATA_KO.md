# 습식 CO₂ 부식 편집 자료의 현재 사용 경계

## 확보 자료

Harvard Dataverse의 *Heterogenous CO2 Corrosion Dataset*, DOI
`10.7910/DVN/1ZIEO4`의 원 CSV를 고정했다. Dataverse API가 표시한 라이선스는 CC0 1.0이며,
원파일은 14,823바이트, 제공자 MD5 `68fe64b902a0402cc97e35b2120de8e0`, 프로젝트 SHA-256
`8581f6e29e12956f2fbf4fb1d46cd659540bf6878bf30beb48f340e4c9ca546e`이다.

파일은 427행과 다음 8개 수치열을 가진다: Temperature, Flow velocity, CO2 pressure, Internal
pressure, Corrosion Inhibitor efficiency, Shear stress, pH, Corrosion rate.

## 별도 확인한 단위와 구성

CSV 자체에는 단위가 없다. 이 자료의 연계 preprint인 Ejeta 외, *Ensemble Machine Learning for
CO2 Corrosion Rate Prediction with Heterogeneous Datasets*, DOI
`10.21203/rs.3.rs-8896642/v1`의 Table 1을 별도로 검토했다. 논문은 열 순서와 동일한 통계값을
제시하며 단위를 Temperature °C, Flow velocity m/s, CO₂ pressure bar, Internal pressure bar,
inhibitor efficiency %, shear stress Pa, pH 무차원, corrosion rate mm/year로 명시한다. 논문은
CC BY 4.0이며 문장·표·그림은 복제하지 않고 사실인 단위 선언과 인용만 기록한다.

논문은 전체 구성도 집계 수준에서 밝힌다.

- NORSOK M-506으로 생성한 시뮬레이션 243개
- 오토클레이브 중량감소 실험 50개
- 중국 동부 하이난 해저 배관 현장값 60개
- 나이지리아 Egua-2 다상 유동 배관 현장값 74개

합계는 CSV의 427행과 일치한다. 그러나 논문과 CSV 어느 쪽도 이 네 그룹을 개별 CSV 행 번호에
연결하지 않는다. 파일의 배열과 결측 패턴만 보고 행별 그룹을 지정하지 않는다.

## 243개 시뮬레이션 행의 정확한 외부 대조

Khakzad와 Khakzad의 Mendeley Data 자료 *Simulation data for CO2 corrosion rate of oil pipeline*,
DOI `10.17632/4nydhxjymw.1`, CC BY 4.0의 고정 workbook을 별도로 취득했다. 제공자 SHA-256은
`da4548f34ffb9c4fac2516b9d40eab18d57f6111f48f3aeb051ab092ccba2eae`이다. Workbook은
243개 NORSOK M-506 기반 모델 출력과 열별 단위표를 가진다.

`match_wet_co2_simulation_source`는 workbook의 단일 sheet, 첫 8개 header, 단위표, 243행의
위치와 모든 수치값을 고정 CSV와 대조한다. Workbook 2–244행은 편집 CSV 2–244행과
243/243개가 위치·8개 값 모두 정확히 일치했다. 따라서 이 행들만
`source_group_id="doi:10.17632/4nydhxjymw.1"`, `provider_data_type="simulated_model_output"`으로
연결한다. 수량·범위·결측 패턴만으로 연결한 추정이 아니다.

이 243행은 물리 시편이나 실험 관측이 아니라 제공자 모델의 결정론적 출력이다. 물리 부식모델
보정이나 독립 검증으로 쓰지 않는다. 데이터셋의 CC BY 4.0은 workbook 재사용 근거이지만 NORSOK
규격·프로그램·표·코드의 재배포 권한으로 확대하지 않는다. 이 출력으로 공개 surrogate를 만드는
일도 적용성·파생 권리 검토 전에는 진행하지 않는다.

## 오토클레이브 문헌 후보의 제한적 행 대조

연계 preprint가 오토클레이브 자료의 근거로 인용한 Abbas 외 논문, DOI
`10.1016/j.psep.2018.07.006`의 저자 accepted manuscript를 별도 로컬 근거로 검토했다. 저장소가
표시한 문서 라이선스는 CC BY-NC-ND 4.0이므로 PDF와 부록 표의 점별 전사는 공개 배포하지 않는다.
부록에는 학습 16행과 최종시험 6행, 합계 22행이 있으며 연계 preprint가 그 문헌에서 가져왔다고
보고한 50개와 수가 일치하지 않는다.

온도·유속·pH·부식속도의 22행 순서를 전체 편집본에서 검색하면 provider source row 334–355에
유일한 후보가 있다. 부록의 CO₂ 압력 MPa를 명시적으로 10배 하여 편집본의 검토된 bar 열과
비교하면 19행은 일치하지만 세 행은 다르다. Source row 346은 233 bar 대 203 bar이고, source
row 349와 355는 각각 82.7 bar 대 827 bar다. 이 차이는 자동 수정하거나 단순 오타로 확정하지
않는다. 22행 후보가 있다는 사실도 나머지 28개 오토클레이브 행의 위치, source group 또는 물리
시편 독립성을 정하지 못한다.

`WetCo2LiteratureEvidenceRow`, `WetCo2LiteratureFieldMap`과
`audit_wet_co2_literature_row`는 호출자가 합법적으로 보유한 근거 행을 넣어 단일값 affine 변환과
복수값 산술평균 affine 변환을 명시적으로 비교한다. 원값·변환값·편집값·허용오차·결측·불일치를
모두 보존하고 편집 자료를 수정하지 않는다. 출판물 라이선스, 기초 관측 재배포 권리, 서지 연결,
편집 행 연결과 시편 ID는 서로 다른 필드다. 모든 선언 필드가 맞더라도 보정 가능 상태를 만들지
않는다. 공개 검증 파일에는 점별 표가 아니라 행 수·후보 범위·필드별 일치 수와 세 불일치만 남긴다.

## 동부 하이난 현장자료의 5행 한정 대조

원 논문 DOI `10.1016/j.jngse.2020.103716`은 동부 하이난 해저 배관의 60개 위치 자료를 보고하지만
전체 표를 합법적으로 확보하지 못했다. 공식 PipeChina 논문 DOI
`10.6047/j.issn.1000-8241.2025.10.006`은 그중 위치 1~4와 60만 표에 재수록한다. 고정한 공식 API
응답에서 이 다섯 행만 읽고, 압력 kPa를 편집본 bar로 0.01배하며 액상·기상 벽면 전단응력의
산술평균을 편집본 전단응력과 비교했다.

온도·총압·CO₂ 분압·유속·pH·평균 전단응력의 여섯 비응답 필드로 검색하면 각 재수록 행은 각각
provider source row 245~248과 304에 유일한 후보를 만든다. 여섯 필드는 모두 일치하고 위치 1~4의
부식속도도 일치한다. 그러나 위치 60은 재수록값 3.11 mm/year와 편집값 2.86 mm/year가 다르다.
이를 수정하지 않는다. 다섯 행만으로 나머지 55행의 위치·값·독립성이나 전체 source group을
확정하지 않으며, 원 관측 재배포 권리와 물리 위치 식별도 미확정이다. 공개 기록에는 집계와 이 한
불일치만 있고 API 응답·점별 표는 없다.

## Egua-2 출판사 미리보기의 한계

Egua-2 근거 논문 DOI `10.4028/p-brqaI1`의 출판사 미리보기는 12쪽이다. 페이지 4 목차에는 대상
논문이 27쪽부터 시작한다고 표시되지만, 페이지 5부터 제공되는 본문은 1쪽부터 시작하는 다른
논문이다. 텍스트 추출과 페이지 4·5 렌더링을 함께 확인했으며 대상 DOI와 관측 표는 미리보기에
없다. 따라서 이 파일로 74개 행을 대조하거나 조건을 채우지 않는다. PDF는 출판사 권리표시를
따라 로컬 근거에만 두고 공개 검증에는 해시·페이지 수·부재 판정만 기록한다.

## 해결되지 않은 핵심 메타데이터

나머지 184행의 원 문헌, 현장·실험 구분, 물리 시편 ID, 재료·열처리, 노출시간, 수화학 조성,
측정법과 검열 상태는 여전히 없다. 논문의 50·60·74 집계 수량은 이 행들의 source group 또는
보정/보류 partition을 만들 근거가 아니다.

결측은 Internal pressure 51행, inhibitor efficiency 184행, shear stress 124행이다. 완전행은
243개이고 완전 중복 원값 행은 첫 행 이후 3개다. 이것들은 삭제·평균하지 않는다. 제공자 설명은
현장·시뮬레이션·문헌 실험의 혼합이라고 명시하지만 어느 행이 어느 유형인지는 파일에 없다.

## Python 계약

`read_unresolved_wet_co2_compilation`은 고정 해시와 정확한 열 순서를 검사하고, 원 수치와 결측을
`UnresolvedWetCo2CompilationRow`로 반환한다. 각 행은 다음을 명시적으로 보존한다.

- `provider_units_status="not_supplied"`
- `provider_data_type="unresolved_field_simulated_or_experimental"`
- source group·시편·재료상태·노출시간은 `None`
- `mechanistic_calibration_ready=false`
- 원 관측 권리는 별도 검토 필요

따라서 이 로더는 원값 조회·감사 인터페이스이며 부식속도 계산기나 보정 모델이 아니다.

`wet_co2_si_observation_from_compilation_row`은 호출자가 정확한
`doi:10.21203/rs.3.rs-8896642/v1#table-1` 단위 근거를 명시적으로 승인한 경우에만 SI view를
만든다. °C→K, bar→Pa, %→fraction, mm/Julian-year→m/s를 변환하고 CSV에 단위가 없었다는
상태와 논문 근거를 함께 보존한다. 변환 결과도 source group·시편·재료·노출시간이 없으며
`empirical_calibration_ready=false`, `mechanistic_calibration_ready=false`이다. 단위 변환은 자료
독립성이나 모델 적합성을 해결하지 않는다.

## 다음 자격화 조건

나머지 184행은 원 문헌 또는 제공자의 행별 data dictionary에서 데이터 유형, source group, 재료·수화학,
노출시간과 측정법을 확보해야 한다. 같은 물리 시험에서 나온 반복·파생·시뮬레이션 값을 분리하고,
원 관측 이용권을 검토한 뒤에만 보정/보류 분할을 설계한다. 편집표의 CO₂ pressure 값을 자동으로
fugacity나 모델 입력으로 쓰지 않는다.

## 별도 검토 입력을 통한 fixed-fugacity 화학 경로

`chemistry.fixed_fugacity_carbonate_equilibrium`은 편집 데이터 행을 직접 받지 않는다. 사용자가
독립적으로 검토해 공급한 CO₂ fugacity, 같은 용매 조성의 Henry 용해도 계수, 활동도 평형상수와
총알칼리도로 pH 및 탄산 종을 푼다. `CO2_FIXED_FUGACITY_EQUILIBRIUM_KO.md`에 계약, 식, source
links와 한계를 기록했다. 이 모델이 기상 수를 보존하거나 fugacity 계수를 계산하지는 않으므로 실제
기체 상태 물성 공급자 필요성은 그대로다. 이 화학 closure는 부식속도 예측 또는 공개자료 보정이 아니다.

## AquaSolDB v2.1 기체 용해도 기록 adapter

2026-10-19 공개본 AquaSolDB v2.1에는 물·염수에서의 기체 용해도 편집자료가 있으며, CO₂ 행은 7,194개다. 이 중 순수 물(`salt=none`), CO₂ partial-pressure 기준, 측정값, 무표식, 0.1 MPa 이하를 모두 만족하는 41행과 8개 원 출처가 있어 저압 순수물 조건에 대한 문헌 탐색 후보군을 만든다. 이 필터는 편의상 선택한 구조 감사 조건일 뿐, Henry 상수·물성값·보정 관측군 또는 적용 온도범위를 자격화하지 않는다. CO₂ 전체 행은 0.00395–200 MPa와 263.15–723.15 K를 포함하므로 하나의 희석 Henry 관계로 묶을 수 없다.

편집본의 CC BY 4.0은 편집자의 선별·정리와 schema를 대상으로 한다. 개별 수치 측정은 편집자가 이용허락하지 않으며 각 `source_id`가 가리키는 원 논문을 인용하고 해당 원자료 권리·조건을 따로 검토해야 한다. 프로젝트는 제공자 ZIP을 `data/raw/aquasoldb-gas-solubility-v2-1/`에서만 보관하고 public wheel·sdist·source review ZIP에서 제외한다. `iter_aquasoldb_co2_solubility`는 정확한 v2.1 SHA-256과 CSV schema를 확인해 사용자가 요청한 CO₂ 행을 호출자 메모리로 읽는다. 원자료를 추출하거나 보정·Henry 변환·기체 fugacity 추정·용해도 단위변환을 하지 않는다. 반환 계약은 `point_id`, 원 `source_id`, 상태·표식·압력 기준·매질·이온 몰랄도와 용해도 단위를 보존하고, 원 논문 인용·rights review 필요성을 함께 표시한다.

`select_aquasoldb_co2_records`는 명시된 조건으로 typed record를 필터링하며 상한 초과 결과를 조용히 자르지 않는다. 이후 `compare_aquasoldb_to_fixed_fugacity_model`은 source-specific 검토를 마친 한 관측 행과 독립 공급 Henry 계수·CO₂ fugacity를 비교하는 선택적 adapter다. 이는 AquaSolDB 행으로 계수를 역산하거나 모델을 보정하지 않는다. CO₂ 분압 기준, 정확한 온도 및 solvent-composition digest, Henry 정의와 기록 독립성을 확인하고 mol/kg-water→mol/L-solution 변환에 필요한 물 질량농도 및 비교 불확도를 호출자가 제공해야 한다. 검토 누락, total-pressure 행, 조건 불일치는 결과를 `needs_data`로 남긴다. 단일 점 비교만으로 다른 조건에서의 모델 적합성이나 부식 속도를 입증하지 않는다.

비점별 공개 감사 결과는 `validation/aquasoldb_co2_archive_audit.json`에만 기록한다. 해당 요약은 제공자 편집본의 저작자·버전 DOI·변환하지 않은 분석 범위를 귀속 표시하며, 출처 문헌 문자열과 관측 행·ID를 싣지 않는다. 컴파일러는 판독 자료의 일부만 점검했다고 밝히므로 출처 문헌의 원 값과 충돌하면 이 archive를 정답으로 취급하지 않는다.

```powershell
.venv\Scripts\python.exe scripts\fetch_data.py --ids heterogeneous-wet-co2-corrosion
.venv\Scripts\python.exe scripts\inspect_wet_co2_data.py
.venv\Scripts\python.exe scripts\inspect_wet_co2_literature_evidence.py
.venv\Scripts\python.exe scripts\inspect_wet_co2_hainan_evidence.py
.venv\Scripts\python.exe scripts\inspect_wet_co2_egua_preview.py
.venv\Scripts\python.exe -m pytest tests\test_wet_co2_data.py -q
```

집계 감사는 `validation/heterogeneous_wet_co2_dataset.json`과
`validation/wet_co2_literature_crosswalk.json`,
`validation/wet_co2_hainan_secondary_crosswalk.json`과
`validation/wet_co2_egua_publisher_preview.json`에 있다.


## 용접금속·모재 실험값 예제

Liu 외(2021)의 CT110 실험 보충자료 S1/S2(DOI `10.1371/journal.pone.0244237.s017`, `.s018`)는 CC BY 4.0을 표시하며, 온도 3점과 CO₂ 분압 3점에서 용접금속/모재 중량감소 부식속도를 제공한다. 출처·원본 체크섬·조건·변환과 제한을 보존한 6쌍의 attributed fixture는 `validation/ct110_weld_corrosion_rates.json`에 있다. 실험 coupon ID, 반복수와 불확실성은 제공되지 않아 단일 연구의 설명 예제로만 사용한다. 공개 모델 API `corrosion.material_rate_contrast`는 호출자 조건에서 두 속도의 비와 차이를 계산하며 습식 CO₂ 기구 모델, 보편적인 용접부 배수 또는 독립 보정을 만들지 않는다. 원본 XLSX는 `data/raw/experimental-coiled-tubing-weld-corrosion/`에 보관하고 공개 배포에서 제외한다.
