# Otto 수계 전해질 자료 reader

`matintegrity.otto_electrolyte_data.read_otto_electrolyte_archive()`는 TRI Energy & Materials Data의 `otto_aqueous.json`을 담은 제공자 ZIP에서 251개 provider record를 읽고 typed record로 반환한다. ZIP을 추출하지 않고 읽으며, archive snapshot SHA-256·JSON member SHA-256·정규화 record digest, 원 `GUID`, run ID, provider time series, composition feeder fields, reported electrochemical summary와 CC BY attribution을 보존한다. 확인한 archive는 `data/raw/matr-aqueous-electrolytes/otto_data.zip`에 있으며 `.gitignore` 대상이다.

## 데이터의 의미와 사용범위

제공자 페이지는 데이터셋 자체에 CC BY 4.0을 선언하며, JSON 및 pickle 파일을 제공한다. 논문은 251개 수계 리튬/나트륨 염 배합의 전도도·pH·백금 전극 전기화학 응답이라고 설명하고, fast assessment 측정은 정전류 hold 기반의 다단계 실험이다. 이 구조는 일반적인 부식 polarization scan과 다르다. reader는 시간에 따른 전위와 signed current-density trace 및 provider의 anode/cathode 안정성 요약값을 원형 그대로 다루며 `PolarizationCurve`, 부식률, tafel corrosion current, metal-loss, 재료 합격이나 수명으로 변환하지 않는다.

JSON 안에는 conductivity 및 temperature 숫자의 단위 표기가 없다. reader는 이 값을 provider-native 수치와 `not encoded in JSON; caller review required` 단위 상태로 보존하고 변환하지 않는다. 논문 방법 설명에 있는 전극·current step·reference·시간 해석은 protocol metadata로만 연결하며, 부식 시험 증거로 일반화하지 않는다. 모든 데이터 사용 결과에 CC BY attribution을 유지해야 한다. 이 데이터셋의 라이선스와 별도 연구 논문의 CC BY-NC-ND 라이선스를 혼동하지 않는다. 본 프로젝트는 논문 문장·표·그림을 복사하지 않는다.

## 재현 구조 감사

로컬 archive 고정 digest와 record/member integrity를 검사하고 합계·범위만 `validation/otto_electrolyte_archive_audit.json`에 기록하는 도구는 `scripts/inspect_otto_electrolyte_data.py`다. 개별 row·time-series 값은 보고서에 쓰지 않는다. 이 감사는 JSON 형식, 배열 정렬, ID 유일성, archive/checksum 상태만 다루며 실험 불확도나 electrochemistry 물리 자격화는 하지 않는다.

## 원자료와 방법 근거

- [TRI Energy & Materials Data: Aqueous electrolytes](https://data.matr.io/5/) — provider dataset page, CC BY 4.0 declaration, file links and schema description.
- [Dave et al. 2020 article DOI](https://doi.org/10.1016/j.xcrp.2020.100264) — experiment and measurement method reference. The article and the dataset have distinct license notices; do not reproduce article prose, figures or tables.

코드는 원자료의 저작 표현을 복사하지 않은 독립형 reader다. Provider ZIP에는 cryptographic publisher checksum이 없어 기록된 SHA-256은 이 로컬 취득 snapshot의 고정값이지 provider checksum으로 주장하지 않는다.
