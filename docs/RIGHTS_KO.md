# 공개 배포 자료 관리

프로젝트 코드와 설명은 독립적으로 작성한다. 공개 자료에서 과학적 관계와 사실을 확인하더라도 해당 설명 문장·도표·편집된 표·소스코드를 복제하지 않는다. 단순한 문장 변경이 권리 문제를 해결한다는 전제로 개발하지 않는다. [WIPO의 저작권 안내](https://www.wipo.int/en/web/copyright/faq-copyright)는 아이디어와 표현의 구분을 설명한다. 개별 자료의 이용조건과 다른 권리는 별도로 확인해야 한다.

Zenodo `10.5281/zenodo.18668632`의 316L SECCM-SEM/EBSD 자료는 CC BY 4.0을 선언한다. 원 ZIP은
로컬 제외 경로에만 두고 저자·제목·DOI·라이선스와 프로젝트의 구조 감사 변환을 고지한다. 제공자
GitHub 분석 저장소는 고정 commit에서 MIT를 선언하지만 코드·노트북을 복제하거나 실행하지 않는다.
독립 reader는 raw header와 수치를 직접 검증하며 provider descriptor·label·영상표를 재배포하지 않는다.
dataset license는 map point의 물리 독립성이나 label·pit truth·검출성능을 보증하지 않는다.

Zenodo `10.5281/zenodo.21420213`의 FABEST LCF v2 자료는 CC BY 4.0을 선언한다. 작성자·제목·DOI·
라이선스 링크와 archive 구조 감사라는 변환을 고지한다. 원 ZIP·보고서·제출 template·점별 CSV는
공개 Python 배포물에 복제하지 않고 로컬 제외 경로에 둔다. 제공자 파일을 실행하거나 설명 문장을
코드 주석으로 옮기지 않는다. 공개 라이선스와 별개로 experiment folder가 물리 시편 독립성을
증명하지 않으며, Case 4-5 target 폴더에 outcome CSV가 없으므로 blind 결과를 추정·생성하지 않는다.

Zenodo `10.5281/zenodo.18731788`의 공식 API는 판재 균열 영상 ZIP에 CC BY 4.0을 선언한다.
재사용 시 저자·제목·DOI·라이선스 링크와 프로젝트 변환을 표시한다. 원 영상은 공개 Python
배포물에 복제하지 않고 선택적 취득 대상으로만 둔다. Dataset-level 이용허락은 image-level label을
균열 치수·POD·규격 합격 또는 현장 VT truth로 해석할 기술적 권한을 주지 않는다.

Zenodo `10.5281/zenodo.10618962` API metadata는 X-weld image archive를 open access와
Apache-2.0으로 표시한다. 다만 record에는 upstream image provenance나 촬영조건 설명이 없으므로
license tag를 미식별 제3자 영상의 권리 보증으로 확대하지 않는다. 파일은 기본 비활성 선택 취득이며
공개 배포물에 복제하지 않는다. GDXray의 연구·교육 한정 및 재배포·상업 이용 금지 조건과 명시적
license 파일이 없는 RIAWELC는 공개 자동 취득 대상에서 제외한다.

ML-NDT 저장소는 고정 commit에서 LGPL-3.0을 표시한다. 코드와 augmented PAUT data를 이 프로젝트의
MIT 배포물에 복제·재라이선스하지 않고 commit·tree 집계·독립 설명과 사용자가 별도로 보유한 clone의
파일 정합성을 읽는 독립 인터페이스만 기록한다. Reader는 제공자 코드를 실행하거나 원자료를 내려받지
않는다. Strathclyde PAUT
record는 CC BY 4.0을 명시하지만 원 ZIP checksum과 성공한 취득 증거가 없으므로 metadata-only다.
TYUST-PAUT의 신청 승인 방식과 Bristol 자료의 non-commercial 조건은 공개·상업 겸용 기본 취득
정책과 구분한다.

Mendeley Data `10.17632/sggn77wv29.1`은 공식 record에서 CC BY 4.0을 선언한다. 현재는 서지·license와
독립 요약만 catalog에 기록하고, 제공자 simulation 파일·FORTRAN code·그림·설명 문장을 MIT 배포물에
복제하지 않는다. 파일 목록·checksum·좌표와 시간 단위가 확인되기 전 자동 취득 대상으로 승격하지 않는다.

Mendeley Data `10.17632/c2h2jf5c54.1`은 CC BY 4.0을 선언한다. README와 네 ILI XLSX를 제공자
체크섬으로 로컬 취득했으며, 공개 패키지에는 원파일·점별 행을 포함하지 않는다. 독립 코드에는 출처,
license, 고정 해시와 집계 감사만 남긴다. 이 권리는 원자료가 raw MFL, 굴착 truth 또는 자격화된
feature tracking임을 뜻하지 않으며, 별도 MIT 저장소의 코드·가공 표·모델은 복제하지 않는다.

HyMatBase record `j1e8n-2bz97`은 Sandia 4130X 수소 파괴·피로 workbook을 공개 다운로드하고
provider MD5를 표시하지만 Rights 항목은 비어 있다. 공개 접근을 재배포 허락으로 해석하지 않는다.
원 XLSX와 271개 점별 행은 `data/raw/`에만 두며 source/wheel/review ZIP에서 제외한다. 공개물에는
서지·record URL·해시·독립 reader·집계 감사와 압력 충돌만 기록한다. 관련 논문·규격의 문장·도표·
합격기준·곡선식도 복제하지 않는다.

## 배포 경계

이 디렉터리만 공개 저장소 및 배포물의 루트로 사용한다. 상위 폴더와 로컬 데이터 캐시는 포함하지 않는다. 원본 자료의 전체 문서·사진·표·규격 전문은 패키지에 자동 포함하지 않는다. 배포 검사기는 허용된 코드·문서·예제·카탈로그·검증 기록만 묶고 파일 목록을 검사한다.

## 외부 자료

BAM의 “Simulation and laboratory eddy current testing data - modelling compound defects via perturbation
theory” `10.5281/zenodo.14186333`은 Zenodo record에서 CC BY 4.0으로 표시된다. 공개 저장소에는
작성자·제목·DOI·라이선스·고정 체크섬·집계 감사와 독립 작성 계약만 둔다. 원 7z, CSV, DICONDE와
상용 Faraday solver는 source archive·wheel에 포함하지 않는다. 제공자 문장·도표·점별 자료를 복제하지
않고 filename/comment를 독립 결함 치수나 물리 시편 truth로 승격하지 않는다.

라이브러리는 의존성으로 설치하고 원래 라이선스를 유지한다. CC BY 4.0 데이터는 작성자·제목·DOI·라이선스와 변환 내용을 기록한다. 원자료를 일부 재배포하려면 해당 파일의 조건을 먼저 확인하고 독립된 고지를 붙인다. 데이터가 공개적으로 내려받아진다는 사실만으로 아무 조건 없이 재배포할 수 있다고 판단하지 않는다.

NIST는 SRD, 직원 작성 자료, 외부 기여 자료에 서로 다른 조건이 있을 수 있다. [공식 이용조건](https://www.nist.gov/open/license)을 확인하며 CORR-DATA 원본과 변환 관측의 재배포는 별도 검토 전까지 보류한다. 다운로드·스크래핑을 금지한 공급자는 자동 취득 목록에서 제외한다.

Harvard Dataverse의 습식 CO₂ 편집 자료는 데이터셋 수준에서 CC0 1.0을 표시하지만, 제공자 설명상 현장·시뮬레이션·문헌 실험을 혼합했다. 연계 preprint `10.21203/rs.3.rs-8896642/v1`은 CC BY 4.0이며 열 단위와 네 데이터 유형의 집계 수량을 확인하는 인용 근거로만 사용한다. Mendeley Data의 `10.17632/4nydhxjymw.1`도 CC BY 4.0이며, 고정 workbook의 헤더·단위표·243개 수치행을 편집본 처음 243행의 정확한 출처 대조에 사용한다. 이 라이선스는 NORSOK M-506 규격, 제3자 구현 코드·표·문서 또는 그 동작을 재현하는 공개 surrogate의 권리를 부여한다고 해석하지 않는다. 논문 문장·표·그림과 규격 내용을 복제하지 않는다. 잔여 184개 원행에 문헌 식별자나 데이터 유형 연결이 없으므로 데이터셋 선언, 논문 이용조건과 기초 문헌 관측의 권리를 분리한다. 공개 배포에는 두 원 workbook/CSV와 점별 파생값을 넣지 않고 인용·해시·집계 감사와 독립 로더·대조·변환 계약만 포함한다.

잔여 행의 후보 대조에 사용한 `10.1016/j.psep.2018.07.006` accepted manuscript는 기관 저장소가
CC BY-NC-ND 4.0으로 표시한다. PDF와 부록 표의 점별 전사본은 로컬 `data/evidence/`에만 두고
공개 패키지·source archive·review ZIP에서 제외한다. 공개 코드에는 호출자 보유 값을 비교하는
독립 계약만, 검증 기록에는 행 수와 일치·불일치 집계만 둔다. 출판물 접근·라이선스를 기초 문헌
관측의 재배포 허가로 취급하지 않으며, 수치 불일치를 수정본이나 파생 표로 공개하지 않는다.

동부 하이난 60행 원 논문의 다섯 행을 재수록한 PipeChina 공식 API 응답과 Egua-2 논문의
출판사 미리보기는 로컬 `data/evidence/`에만 둔다. 어느 쪽도 점별 관측 재배포 권리를 확인하지
못했다. 전자는 재수록된 다섯 행의 집계 대조에만 사용하고, 후자는 대상 논문 본문과 표가 실제
미리보기에 없다는 접근성 감사에만 사용한다. API JSON, PDF, 표 전사와 렌더링 이미지는 공개
배포물에 포함하지 않는다.

## 근거 기록

CEIT/WATEREYE의 방법 연구 `10.3390/app12020808`과 Zenodo 기록
`10.5281/zenodo.7400271`은 CC BY 4.0으로 표시된다. 공개 프로젝트에는 저자·DOI·라이선스,
고정 해시, 독립 작성한 왕복거리 계산·교정 계약과 원 관측을 복원하지 않는 집계만 둔다. 연구의
문장·그림·표·점별 결과와 로컬 근거 파일은 배포하지 않는다. 연구에 보고된 5950 m/s는 해당
S355J2G3 기준시편·실온 교정의 결과이며 이후 현장 JSON의 자동 기본값이나 일반 S355 물성표로
재배포하지 않는다.

COQTEL DOI `10.5281/zenodo.14193336`과 연계 논문 DOI `10.1016/j.dib.2025.111393`은 CC BY
4.0으로 표시된다. 공개 프로젝트에는 작성자·DOI·라이선스·고정 체크섬, 독립 reader와 집계 검사만
둔다. HDF5 두 파일, root 이미지, 전기화학 행, 파형과 제공자 MATLAB 예제는 source archive와
wheel에서 제외한다. CC BY 조건이 있더라도 전체 raw를 패키지에 복제할 필요가 없으며, 시편과
교란·참값 누락을 보존한 재취득 방식을 사용한다.

CEIT 해안 노출 균일부식 자료 DOI `10.5281/zenodo.13897090`은 Zenodo 메타데이터에서 CC BY
4.0으로 표시된다. 49.9 MB JSON 원관측과 파형은 공개 패키지에 복제하지 않고, 작성자·DOI·
라이선스·고정 체크섬, 독립 reader와 집계 감사만 둔다. 파일에 명시되지 않은 ToF·온도 단위와
초음파 경로·음속·교정식을 저작물이나 장치 동작에서 추정해 구현하지 않으며, 제공자 요약
134 µm/year를 재현된 계산값으로 표시하지 않는다.

수식·상수·계수·예제의 근거는 `data/catalogs/sources.json`과 각 계산기의 `source_ids`로 추적한다. 규격별 한계값·허용표·면제곡선은 정식 이용권이 있는 사용자 공급자 또는 별도 허용 근거를 확보한 플러그인으로 받는다. 출처 고지가 필요한 자료의 고지를 삭제하거나 다른 자료에서 나온 것으로 표시하지 않는다.

원천 권리, 고용관계에 따른 코드 소유권, 상표·특허·계약 및 관할별 판단까지 자동 검사로 확정할 수는 없다. 배포 검사는 확인한 조건과 포함 파일을 기록하며 법적 무결성을 인증하지 않는다.
