# 파괴인성 온도 자료 typed-row API

## 자료 출처와 재사용 범위

- 공급자 레코드: [Mendeley Data, DOI 10.17632/2vkgrbsy8j.1](https://data.mendeley.com/datasets/2vkgrbsy8j/1)
- 카탈로그 권리 검토일: 2026-10-26. 공급자 레코드의 CC BY 4.0 표기는 편집물(compilation)에 대한 라이선스로 기록되어 있다.
- 레코드 설명은 Table A2를 training, Table A3를 test 자료로 설명한다. Reader는 기존 parser의 정확한 partition 값(`training`/`test`)과 source sheet 이름을 그대로 보존한다. 문서상의 “test” 분할을 “testing” 문자열로 정규화하지 않는다.
- 카탈로그에서 편집물에 수록된 개별 관측의 권리는 미해결로 분류되어 있다. 따라서 이 API는 데이터 재배포나 공개를 허가한다고 해석하지 않는다. 권한 있는 호출자가 명시적으로 승인한 환경에서만 로컬 자료를 읽으며, 출력물 공유 여부는 별도 권리 확인이 끝날 때까지 제한해야 한다.
- 코드에는 원자료 행 값이나 workbook 내용이 포함되지 않는다. 파일 이름·크기·SHA-256은 승인된 로컬 사본을 고정하기 위한 식별 정보다.

## API

모듈 `matintegrity.fracture_toughness_typed_rows`는 다음 인터페이스를 제공한다.

- `FractureToughnessReadAuthorization`: 호출자 귀속표시, 계산 사용 승인, 로컬 전용 승인, 파서의 단위 해석 검토 확인을 요구한다.
- `iter_fracture_toughness_observation_rows(path, authorization=..., ...)`: 기존 `read_fracture_toughness_temperature` 파서 출력을 입력 순서대로 typed record로 제공한다. 각 행에는 출처 partition/sheet/row, 원본 순번, 보고값과 파서 정규화 값, 단위 기준, archive/member digest, authorization digest, 행 digest, `Evidence`가 들어간다.
- `audit_fracture_toughness_archive(request)`: 값이나 로컬 경로를 반환하지 않고 고정 파일의 메타데이터 및 partition별 행 수만 산출한다.
- `specifications()`: 중앙 registry 연동에 사용할 ModelSpec을 반환한다. 모델 ID는 `data.mendeley_fracture_toughness_temperature_typed_rows`다.

원본 archive는 `2vkgrbsy8j-1.zip` (2,666,905 bytes, SHA-256 `d1007e9b3a3802594f169a15e72a94353a674cb72daf2faef93f9ae9fabdf66f`)로 고정한다. workbook member SHA-256은 `647de2626f39a83ccc35f2a00248e033724d52052cfbb8bd4d8ff0439993b0d2`여야 한다. 어떤 pin이든 다르면 읽기를 거부한다.

### 행 필드 의미와 단위

API는 기존 파서가 반환하는 값을 그대로 감싸며 원자료의 공학적 적합성이나 대표성을 판단하지 않는다.

- 온도: `reported_temperature`는 워크북 표기 `K`와 함께 보존한다. `temperature_K`는 파서의 기본 검토 단위 해석(논문 기준 기본 degC→K) 또는 호출자 지정 `temperature_unit_override`에 따른 값이며, `temperature_unit_basis`가 적용 기준을 기록한다.
- 항복강도: `yield_strength_MPa` 및 Pa 환산 필드를 함께 보존한다.
- 시험편 치수: `reported_W`, `reported_B`, `reported_a`의 원 단위 표기는 카탈로그상 확정되지 않았으므로 `reported_dimension_unit_label`은 미지정이다. `W_m`, `B_m`, `a_m`는 parser의 논문 검토 기본 해석 또는 `dimension_unit_override`에 따른 파생 필드이며 그 근거를 `dimension_unit_basis`로 보존한다.
- 파괴인성: 보고된 `KJc` 수치와 MPa√m/Pa√m 표기 필드를 모두 보존한다. 이 데이터 변환은 타당성, 기준온도 보정 적합성 또는 허용값을 인증하지 않는다.
- `source_partition`, `source_sheet`, `provider_source_row`, `source_order`, `reported_record_id`, `observation_id`는 원 자료의 분할 및 행 식별 정보를 유지한다. 결측값은 null로 표현하며 새 관측값을 만들지 않는다.

## 통합·보안 경계

기존 parser를 단일 원천으로 재사용하므로 단위 옵션과 grouping 옵션도 기존 함수의 규약을 따른다. 각 row digest는 파서 출력, 원본 순서, archive/member digest, 옵션, 미해결 권리 상태를 포함한다. `Evidence`에는 Mendeley DOI 및 호출자 귀속표시가 연결된다. authorization digest는 명시적 승인 조건의 지문이며 공급자가 개별 문헌의 데이터 권리를 승인했다는 뜻이 아니다.

이 API는 파괴인성 하한, 유효성, 물리적 독립성, 문헌별 원자료 식별, 재료 적격성 또는 수용 판정을 추론하지 않는다. `physical_specimen_id`와 `underlying_literature_id`는 확인되지 않았으므로 비어 있다. FTA나 다른 위험 분석에 연결할 경우에도 이 자료만으로 확률·실패율을 만들면 안 된다.

공개 배포 전에 공급자 라이선스 범위와 underlying observation 권리를 다시 검토해야 한다. 현 상태의 사용 경계는 local-only이며, 컴파일된 행 값·파서 출력·그 파생물을 공개 저장소나 검증 산출물로 복사하지 않는다.
