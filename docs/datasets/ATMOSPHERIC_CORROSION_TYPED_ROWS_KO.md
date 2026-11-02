# 대기 부식 자료 typed-row API

## 출처와 권리 범위

- 공식 레코드: [Mendeley Data, DOI 10.17632/ysr7wy3y7z.1](https://data.mendeley.com/datasets/ysr7wy3y7z/1). 게시일은 2026-10-20이며 제공자는 탄소강의 1년 대기 노출 자료와 ERA5 기후 공변량을 기록한다.
- 프로젝트 카탈로그 권리 검토일은 2026-10-27이다. 카탈로그는 CC BY 4.0을 편집물 라이선스로 기록하고, 개별 문헌 및 프로그램에서 유래한 관측의 재배포에는 별도 출처별 검토가 필요하다고 제한한다.
- 이 API는 모든 underlying observation의 권리 상태를 `unresolved`로 유지한다. 호출자가 계산 사용·관측 사용·로컬 전용 이용을 명시적으로 승인해야 하며, 호출자의 선언은 공급자 권리를 새로 부여하지 않는다. 현재 레코드와 그 파생 행은 로컬 전용으로 다룬다.
- 데이터 파일이나 행 값은 코드/문서에 복제하지 않는다. 승인된 로컬 사본만 사용한다.

## 고정 입력과 API

기존 파서 `matintegrity.atmospheric_data.read_atmospheric_corrosion_observations`를 단일 파싱 원천으로 감싼다. 파일은 `ysr7wy3y7z-1.zip`, 290,946 bytes여야 한다. 카탈로그 MD5는 `a28c35bea466ca2e1b280d875fdbb168`, 파서가 요구하는 revision SHA-256은 `a1accd1ad324f7b2cc0cf9776bf60839c3f7368a8c65c7e6ea71a494e6a0ca35`다. 이름·크기·파서의 강제 SHA pin 중 하나라도 다르면 읽기를 거부한다.

새 모듈 `matintegrity.atmospheric_typed_rows`는 다음 인터페이스를 제공한다.

- `AtmosphericReadAuthorization`: 귀속표시, 계산 및 관측 사용 승인, 로컬 전용 승인을 요구한다.
- `iter_atmospheric_corrosion_typed_rows(path, authorization=..., partition=...)`: 기존 파서 결과에 source partition/row, 출력 순번, archive 지문, authorization 지문, row digest, `Evidence`를 덧붙인다. `partition`은 `programme`, `independent`, `both` 중 하나다.
- `AtmosphericArchiveAuditRequest`, `audit_atmospheric_corrosion_archive`: pointwise 값을 반환하지 않고 고정 입력과 선택된 partition의 행 수만 제공한다.
- `specifications()`: 중앙 등록에서 쓸 ModelSpec을 반환한다. ID는 `data.mendeley_atmospheric_corrosion_typed_rows`, source ID는 `mendeley_atmospheric_corrosion_typed_rows`다.

`both`일 때 `source_order`는 기존 파서 결과에서 programme partition 뒤 independent partition 순서다. 각 행의 `provider_partition` 및 `provider_source_row`는 provider 내 위치를 보존한다. 행 digest는 archive SHA, partition과 provider 행 번호, 기존 파서 typed record, 출력 순번, authorization digest, 권리 상태를 묶는다.

## 단위와 해석 경계

기존 파서의 변환된 값과 단위 이름을 그대로 보존한다.

- 제공자의 첫해 부식률: `reported_first_year_rate_um_year`는 µm/year. `first_year_loss_m`는 1년 누적량을 m로 나타내고, `equivalent_first_year_rate_m_s`는 parser가 정의한 연간값의 초당 등가율이다. 이 둘은 별도 장기 관측이나 장기 성장법칙이 아니다.
- 위치: 위도/경도는 degree. 지역 이름과 source/programme 식별자는 원 파서 문자열을 유지한다.
- 환경 공변량: 염화물·이산화황 침적은 mg/m²/day, 강우는 m, 평균 기온 및 습윤시간 기온은 K, 상대습도는 0–1 fraction, RH 80% 기준 습윤시간은 h/year다. 공변량의 출처는 제공자 harmonisation으로 표시되며 개별 시험편 동시측정값으로 취급하지 않는다.
- `provider_tier`, `provider_rate_source`, 제공자의 염화물 0 가정, 문헌 DOI·메모는 해당 partition 필드일 때만 존재한다. 결측은 관측값으로 채우지 않는다.

이 reader는 제공된 첫해 평균 손실과 공변량을 원래 역할·출처 구분과 함께 전달한다. 국부 최대 침투, 장기 부식률, 구조 용량, 잔여수명, 코드 적합성, 실패확률 또는 통계적 독립성을 계산하지 않는다. Programme/문헌 반복과 기후 공변량은 별개의 자료 역할이다. 이 문서/API를 통해 raw 자료나 pointwise 파생값을 외부로 배포하지 않는다.
