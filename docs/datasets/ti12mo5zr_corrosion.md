# Ti-12Mo-5Zr 수용액 부식 자료

## 출처·재사용 권리

- Zenodo 최신 버전: [DOI 10.5281/zenodo.14981665](https://doi.org/10.5281/zenodo.14981665) (v2)
- 제공자가 기재한 선행 개념 기록 DOI: [10.5281/zenodo.13903531](https://doi.org/10.5281/zenodo.13903531). 이전 기록의 v1은 최신 버전 링크를 가리킵니다.
- 공식 v2 API는 `license=cc-zero`를 반환하고 Zenodo 페이지는 CC0-1.0을 표시합니다.
- 데이터는 `data/raw/zenodo-ti12mo5zr-aqueous-corrosion/zenodo_APSUC_2024.zip` 로컬 전용 캐시에만 보관합니다. ZIP 및 측정 행은 패키지나 추적 문서에 넣지 않습니다.
- 공식 게시자 값: 54,257,020 bytes, MD5 `900a6e1fd9aa550299d01ce892e24d22`. 로컬 archive SHA-256 `caf53855e78ff7162c361ba73435892759926f2d60513f5d42220239ce21f537`.

CC0는 지정된 데이터 기록에 대한 제공자 권리 선언으로 기록했습니다. 학술 인용과 투명한 provenance를 위해 원 자료를 인용하고, 제3자 권리가 별도일 수 있는 출판물·그림·기기 소프트웨어는 포함하거나 재배포하지 마십시오.

## 제공자가 설명한 실험 범위

공개 기록은 Ti-12Mo와 Ti-12Mo-5Zr 합금의 OCP, EIS, AESEC 시험을 PBS+0.1 M 과산화수소 용액에서 수행했다고 설명합니다. 온도는 37°C이며, 기준전극은 포화 KCl Ag/AgCl, 상대전극은 Pt로 기재되어 있습니다. 기록은 EIS를 OCP ±10 mV, 1,000 Hz부터 0.01 Hz까지의 스캔 및 0.785 cm² 면적으로 설명합니다. AESEC는 1 mL/min 유량과 1 cm² 면적에서 OCP 1,200초 → -1 V 정전위 1,200초 → OCP 2,700초의 순서로 설명합니다.

OCP 파일 설명에는 합금별 5,100초 모니터링의 세 반복이 기재되어 있습니다. 내부 워크북 헤더의 시간, 전위, 주파수, 임피던스, 위상, 원소 용출률 열에는 단위가 표시됩니다. reader는 제공자 헤더 문자열과 자료 행을 원형 그대로 내보냅니다. 이 구현은 노출 단계 간 시간 좌표 조정, 전위 기준 변환, 임피던스 면적 정규화, 용출률 재계산, 피팅, corrosion rate 산정 또는 합금 순위화를 하지 않습니다.

## Reader 범위와 계약

`matintegrity.ti12mo5zr_corrosion_data.iter_local_rows`는 OCP 모니터링, OCP 이후 EIS 스펙트럼, AESEC 전위 및 원소 용출률 워크북에서 아래 표에 든 멤버를 개별적으로 스트리밍합니다. `.xls` 파일은 메모리에서만 열고 ZIP을 디스크에 압축 해제하지 않습니다.

| 자료 종류 | 파일 수 | 고정된 시트 행 × 열 | 용도 경계 |
| --- | ---: | ---: | --- |
| OCP | 6 | 10,201 × 3 | 공급자 time, potential 열을 그대로 제공 |
| EIS | 6 | 75 × 5 | frequency/time/impedance/phase 열을 그대로 제공; `Time [s]`를 노출 경과시간으로 재해석하지 않음 |
| AESEC 전위 | 2 | 5,062 × 2 | 단계 경계 계산 없이 전위 이력 원행을 제공 |
| AESEC 용출률 | 2 | 6,604 × 3 또는 6,122 × 4 | 원소별 용출률 원행을 제공; 단위 환산/재계산 없음 |

지원 계약은 `matintegrity.zenodo_ti12mo5zr_workbook_request.v1`, `matintegrity.zenodo_ti12mo5zr_workbook_provenance.v1`, `matintegrity.zenodo_ti12mo5zr_raw_row.v1`입니다. 입력에 로컬 원본 경로, 허용 목록의 내부 멤버와 계산 사용/로컬 처리 승인이 필요합니다. 모든 결과 행은 레코드 DOI, CC0 라이선스, 아카이브와 멤버 SHA-256, 원본 행 인덱스, 헤더, 결측값을 포함합니다.

OCP/EIS/AESEC intensity, DTA, XPS, ICP-AES·이미지 데이터를 이 API가 자동 파싱하지 않습니다. 특히 intensity의 정량 단위·검량 관계는 헤더만으로 판단할 수 없어 제외했습니다. EIS의 스캔 내 시간은 헤더로 존재하지만, 제공자 프로토콜의 침지 시간과 연결되는 의미를 추정하지 않습니다. 반복 ID는 파일 경로에서 유지하며 반복 간 독립성이나 시편 제조 provenance를 새로 추론하지 않습니다.

## 안전 경계

이 코드는 인터넷 접근·압축 해제·외부 프로그램 호출을 하지 않습니다. archive 바이트 수와 SHA-256, 허용 멤버의 크기와 SHA-256, 시트·행·열 수, 열 제목을 확인하고 불일치 시 중단합니다. `xlrd`가 설치된 선택형 `science` 의존 환경이 필요합니다. Python 예제는 문서용이며 여기서는 실행하지 않았습니다.

위자료는 실험 데이터 접근용이지 재료 적격성, 설계 허용치, 수명 또는 위험 확률을 제공하지 않습니다. downstream 위험성 모델은 독립적인 물리 가정·검증·불확도·적용범위를 선언해야 합니다.

## 승인된 파생 API

원행 reader와 분리된 `corrosion.ti12mo5zr_aesec_signed_equivalent_penetration`는 Ti/Mo/Zr AESEC 원소 질량유속(`ng·s^-1·cm^-2`)을 caller 증거가 연결된 밀도로 부호 있는 면적 평균 등가침투 속도(`m/s`)와 exact time-knot 누적량(`m`)으로 변환합니다. 소스 양의 부호가 바깥쪽 용출을 뜻하는지, 모든 분석 원소가 전환에 포함됐는지, 시간축 적분과 구간 선형 보간 및 균일 면적 가정이 적절한지 caller가 승인해야 합니다. 음의 누적 성분은 별도로 유지되며 국부 손상·Faraday 전환·수명·위험도는 산출하지 않습니다. 자세한 계약은 [AESEC mass balance API](../models/ti12mo5zr_aesec_mass_balance.md)를 참조하십시오.

`corrosion.ti12mo5zr_uniform_equivalent_remaining_thickness`는 그 computed AssessmentResult의 입력·전체 결과·내부 mass-balance digest를 확인하고, caller 기준두께 측정 Evidence에서 양의 누적 등가침투만 차감해 exact 관측 시점의 균일 잔여두께를 보고합니다. 음의 순침투는 감사 ledger에 남지만 기준두께 복원에 사용하지 않습니다. 두 API 모두 비국부 면적 평균 파생량이며 실제 국부 벽두께나 잔여수명·위험도를 의미하지 않습니다. [잔여두께 API](../models/ti12mo5zr_remaining_thickness.md).

`corrosion.ti12mo5zr_eis_complex_impedance`는 6개 allowlisted EIS 파일 중 한 개의 74개 source row만 받습니다. `|Z|`와 보고 phase를 `Z'`·`Z''`로 바꿀 때는 caller phase convention Evidence와 부호 선택이 필수입니다. 주파수·scan time·원행 순서를 보존하고 scan time을 침지시간으로 해석하지 않습니다. 면적 정규화와 회로 fitting도 수행하지 않습니다. [EIS 변환 API](../models/TI12MO5ZR_EIS_COMPLEX_KO.md).

