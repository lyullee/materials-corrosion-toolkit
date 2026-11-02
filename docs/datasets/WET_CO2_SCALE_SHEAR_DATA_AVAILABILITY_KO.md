# Wet-CO₂ 스케일 전단 탈락 공개자료 조사

- 조사일: 2026-11-01
- 대상: CO₂ 수용액 부식 생성물의 유동 중 부착, 파쇄, 탈락 또는 제거를 직접 관측해 전단 의존 법칙을 검토할 수 있는 공개 dataset
- 조사 범위: 공식 데이터 저장소와 제공자/출판사 메타데이터. 이 조사에서는 파일 다운로드·열람·파싱을 하지 않았다.

## 결론

현재 확인한 공개 레코드에서 **FeCO₃/Fe₃C scale adhesion 또는 corrosion-product detachment/removal을 정량적으로 관측한 재사용 가능한 파일 세트는 확인하지 못했다.** 2026년 FeCO₃/Fe₃C 유동 연구는 기술 주제와는 매우 가깝지만, 출판사 랜딩 페이지가 이 조사 환경에서 403을 반환했고 공개 검색 결과만으로는 별도 repository, 파일 manifest, 파일별 라이선스와 데이터 접근 상태를 확인할 수 없었다. 따라서 그 논문을 공개 dataset으로 등록하지 않았다.

가장 가까운 공개 자료인 Mendeley의 NORSOK M-506 simulation grid는 **이미 `norsok-m506-simulation-grid`로 양쪽 데이터 카탈로그에 등록**되어 있다. 이 자료는 유속·전단응력·pH·부식률 입력/출력의 소프트웨어 비교에는 쓸 수 있지만, 실측 제품막의 접착·탈락 자료가 아니다. 카탈로그의 제한사항에 이 차이를 추가했다. 새 dataset 레코드는 만들지 않았다.

## 후보별 조사 결과

### 1. NORSOK M-506 기반 CO₂ 부식 simulation grid — 공개, 간접 비교용

- 공식 제공자: [Mendeley Data, v1](https://data.mendeley.com/datasets/4nydhxjymw/1), DOI [10.17632/4nydhxjymw.1](https://doi.org/10.17632/4nydhxjymw.1)
- 레코드 메타데이터는 CC BY 4.0을 표시하고 페이지에 “Download All” 접근 버튼을 제공한다. 파일 URL에 본문을 요청하지 않는 HTTP `HEAD`를 보내 302 redirect 뒤 object store에서 `200 OK`, XLSX content type, `Content-Length: 19,583`과 attachment filename을 확인했다. 파일 바이트는 내려받거나 읽지 않았다. 응답 ETag는 MD5 형태이지만 SHA-256이 아니므로 기존 카탈로그의 SHA-256 값과 동일성 검증에 사용할 수 없다.
- 제공자 설명에 따르면 243개 비중복 행은 NORSOK M-506 계산과 Monte Carlo 절차에서 생성되며 유체 온도·압력·CO₂ 분압·유속·억제제 효율과 shear stress·pH·부식률을 포함한다. 이는 독립 시험이나 현장 관측이 아니다.
- 범위 판정: 유속/전단 변수와 부식 출력의 배선 및 예시 모델과의 대조에만 적합하다. 제공자 설명은 스케일 접착력, 임계 제거응력, 제품 손실량, detachment kinetics 또는 scale morphology의 측정을 제시하지 않는다. 따라서 Wet-CO₂ stage v5의 phase별 탈락법칙을 보정하거나 검증하는 자료로 사용하지 않는다.
- 재사용 경계: CC BY 4.0의 출처표시 및 변경사항 고지를 지키고, 해당 데이터 라이선스를 NORSOK 표준·표·원문 또는 독립 구현물의 재배포 허가로 확대 해석하지 않는다. 상세 출처·체크섬은 [dataset catalog](../../data/catalogs/datasets.json)의 `norsok-m506-simulation-grid` 레코드를 본다.

### 2. FeCO₃/Fe₃C layer의 넓은 유속 범위 연구 — 기술적 직접성 높음, 공개 데이터 확보 미확인

- 논문: Zhang et al., “Effects of wide-range flow velocity variation on formation and protective properties of FeCO₃/Fe₃C films on X65 steel in CO₂ environment,” *Corrosion Science* 265 (2026), 113832, DOI [10.1016/j.corsci.2026.113832](https://doi.org/10.1016/j.corsci.2026.113832).
- 출판사 검색 메타데이터는 submerged-jet 유동, X65 강의 FeCO₃/Fe₃C scale, 전기화학/저항/표면 관찰과 CFD 결합을 설명한다. 이는 생성과 층 구조가 유동과 함께 변하는 현상을 다룬다는 점에서 직접 관련성이 높다.
- Elsevier 랜딩 페이지는 403으로 열리지 않았다. 공개 검색과 현재 찾은 repository metadata에서는 이 논문에 연결된 dataset DOI나 공개 파일 manifest를 확인하지 못했다. 따라서 실제 data-availability 문구, supplement 파일, 파일 라이선스 및 바이너리 접근성을 확인했다고 주장하지 않는다.
- 조치: 논문 기록만 참고 후보로 남기고 공개 dataset으로 catalog하지 않는다. 후속으로 저자/기관 repository 또는 출판사 supplement를 공식 확인하기 전에는 수치 추출·전단 탈락 law 보정에 쓰지 않는다.

### 3. Ohio University ICMT wet-gas flow-loop 시설 — 시험 인프라 메타데이터, 공개 시험자료 아님

- 공식 시설 페이지: [Wet Gas Corrosion Flow Loops](https://www.icmt.ohio.edu/facilities/wetgasloop.asp).
- 페이지는 CO₂ wet-gas loop의 설비와 운전 가능 범위를 설명하지만, 이번 검토에서 특정 실험 원자료, 파일 목록, dataset DOI나 자료 재사용 라이선스를 찾지 못했다.
- 따라서 이를 공개 dataset으로 등록하지 않는다. 설비 capability 정보만으로 실측 이력이나 실험 수치를 유추하지 않는다.

## 적용 권고

1. 기존 NORSOK simulation grid는 deterministic/model-generated 비교군으로 분리한다. 실험 검증 또는 제품막 탈락 법칙의 calibration set으로 취급하지 않는다.
2. 직접 전단 제거 경로를 검증하려면 상 조성·시편/전극·온도·수용액·유속 또는 wall shear field·노출시간·막 전후 상태/질량·반복·불확도가 연결된 실측 데이터가 필요하다.
3. 새 공개 파일을 발견하면 파일 단위 license/provenance와 provider checksum을 먼저 확인하고, raw file은 프로젝트의 기존 비공개 raw-data 정책을 따른다.

## 출처

- <https://data.mendeley.com/datasets/4nydhxjymw/1>
- <https://doi.org/10.1016/j.corsci.2026.113832>
- <https://www.sciencedirect.com/science/article/pii/S0010938X26002416>
- <https://www.icmt.ohio.edu/facilities/wetgasloop.asp>
