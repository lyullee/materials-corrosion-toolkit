# CC0 마그네슘 합금 DEIS 자료 가져오기

`az-we43-az31-molybdate-eis`는 [Zenodo record 10482561](https://doi.org/10.5281/zenodo.10482561)의 로컬 전용 EIS 자료다. 원자료 저장소는 `data/raw/` 아래이며 `.gitignore`에서 제외된다. Zenodo 기록은 데이터 파일에 CC0-1.0을 표시한다. 분석 결과를 공개할 때도 출처 DOI와 과학적 조건·한계를 남긴다.

## 확인된 파일 구조

고정된 `Dataset_CorSci.zip`에는 DEIS, SEM/광학 이미지, XPS 파일을 포함한 16개 항목이 있다. 이 importer는 두 개의 DEIS text member만 읽고 이미지 및 XPS 자료를 처리하지 않는다. 각 DEIS 표는 UTF-8 계열의 tab 구분 숫자 행렬로 확인됐다. 현재 고정 버전의 각 행렬은 54행 × 8,640열이며 공란·비수치·비유한 cell은 없다. 원래 archive/member SHA-256, 표 크기와 순서는 호출 측에 드러낸다.

## 해석 경계

matrix 파일에는 header나 row/column label이 없다. 고정된 depositor metadata의 설명은 각 spectrum의 두 열이 real/imaginary 성분 순서라고 선언한다. 원 행렬의 8,640열은 이 설명에 따라 인접 열 쌍 4,320개로 나눌 수 있다. 기본 manifest는 이 해석을 자동 적용하지 않는다. `create_zenodo_deis_adjacent_pair_view()`는 지정된 metadata/archive digest와 caller의 `zero_based_adjacent_pairing_reviewed=True`를 모두 요구한다. 선택형 iterator는 0부터 시작하는 행 인덱스를 그대로 보존하고 각 행을 `(column[2*i], column[2*i+1])` 순서의 `(real, imaginary)` 쌍으로 묶는다. 이는 행이 주파수인지 시간인지, 각 pair가 특정 시각/조건인지, 실제 단위가 무엇인지 정하지 않는다. pair index를 timestamp나 spectrum acquisition order로 해석하지 않는다.

`summarize_zenodo_deis_depositor_conditions()`는 고정 metadata file SHA-256을 확인한 뒤 depositor가 기록한 조건을 별도 요약 계약으로 반환한다: AZ31/WE43, Hank's solution, 37.0 ± 0.1 °C, 작동 전극 면적 0.6 cm², 최종 전해액 60 mL, 600 mM sodium molybdate 주입액, 150 mM 최종 농도에 도달하도록 한 50분 주입, 무첨가 기준 10분과 억제제 주입 후 12시간 노출. 이 요약은 provider-reported metadata이며 개별 행렬 열/행에 붙이지 않는다. 시작·종료 농도에서 연속 농도 이력을 보간하거나 주입률을 역산하지 않는다.

이 도구는 주파수/시간에 대한 적합, 회로모델 fitting, 부식률 환산, alloy ranking, 용접/설계 acceptance 및 service qualification을 하지 않는다.

## Python 사용

`src/matintegrity/zenodo_deis_import.py`의 `inspect_zenodo_deis_archive()`는 archive pin과 member inventory를 확인하고 수치 데이터는 반환하지 않는 manifest를 만든다. `iter_zenodo_deis_rows()`는 선택한 표를 한 행씩 yield한다. 인접 열 pair view는 base reader와 별개이며 pinned depositor metadata와 명시적 caller review가 있어야 한다. 각 호출은 archive/member digest 및 shape를 확인한다. 데이터를 다시 저장하거나 공용 fixture에 복사하지 않으며, 호출 측은 행·열 순서와 digest를 후속 처리에 전달해야 한다.

실행 예제는 `examples/zenodo_magnesium_deis_local.py`다. 원 archive가 없으면 먼저 프로젝트 data-fetch 절차로 해당 ID를 가져와야 한다. 파일 다운로드 실패 또는 dataset revision 변경 시 parser 상수를 검토한 뒤 새 버전을 별도 등록한다. 기존 pin을 조용히 교체하지 않는다.

## 출처 및 검증 범위

Zenodo 기록의 저작권 표시는 데이터 재사용 권한을 나타내며, 연구 결론의 재현성이나 API의 물리적 타당성을 보장하지 않는다. 이 importer는 archive/member 구조와 파싱 경계에 한정된 데이터 교환기다. 스펙트럼 값 기반 수치 분석, 원 논문과 metadata의 물리 축 연결, 실험 재현, 부식률 보정 및 위험성/수명 모델 검증은 수행하지 않았다.
