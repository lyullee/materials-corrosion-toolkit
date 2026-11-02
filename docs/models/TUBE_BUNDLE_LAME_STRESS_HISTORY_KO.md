# 열교환기 튜브 묶음의 Lamé 압력응력 이력

`integration.tube_bundle_lame_stress_history`는 식별된 각 튜브의 현재 내경과 최소 벽두께, caller가 제공한 내부·외부 압력의 정확한 시간 knot를 사용해 내면과 외면의 Lamé 응력 성분을 계산한다. `TubeCondition` 계약과 `mechanics.Cylinder`/`lame_cylinder`를 재사용한다.

## 입력과 계산

- `TubeCondition`의 `inner_diameter_m`, `minimum_wall_m`, `reference_wall_m`, `tube_id`, `plugged`를 명시된 물성/검사 근거와 함께 제공한다. 내반경은 내경의 절반, 외반경은 내반경과 현재 최소 벽두께의 합으로 정한다.
- 각 튜브별 `TubePressureKnot`은 `time_s`, `internal_pressure_Pa`, `external_pressure_Pa`를 담는다. 두 압력은 비음수 절대압 Pa이며 같은 caller-reviewed 기준을 사용해야 한다.
- 압력 knot는 해당 source ID, record ID, record SHA-256 및 그 SHA를 고정하는 `Evidence`를 포함한다. 형상 레코드도 별도 Evidence digest로 고정한다.
- 형상·압력 knot마다 자산, 위치, 열교환기, bundle ID가 일치해야 하고, pressure knot의 tube ID·time basis·pressure reference는 해당 튜브와 요청 scope에 일치해야 한다.
- 각 knot에서 기존 Lamé 계산기를 내면과 외면에 각각 호출한다. 결과에는 hoop, radial, axial 및 von Mises 응력, 압력·시간 knot, 튜브 형상/압력 계보와 결과 digest가 포함된다.
- 중간 시각의 보간·외삽은 하지 않는다. 압력 입력이 한 knot이면 그 한 시점만 계산한다.

모델 ID는 `integration.tube_bundle_lame_stress_history`, caller 압력·형상 근거 source ID는 `caller_reviewed_tube_bundle_pressure_stress_history`다. Lamé 계산의 기존 수학 근거 source ID도 보존한다.

## 계산 게이트와 보존 조건

모든 리뷰 게이트가 명시적으로 참이어야 계산한다. 튜브 ID는 한 요청에서 유일해야 하며, 압력 시간은 각 튜브에서 엄격히 증가해야 한다. 양의 최소 벽두께, 형상·압력 source digest와 Evidence 일치, 튜브/자산/위치/열교환기/묶음 식별, 절대압 단위·공통 기준, 균일 축대칭 벽과 선형 탄성 적용성, 축방향 단부 조건을 caller가 검토한다. plugged 튜브는 해당 압력 경로를 별도로 검토하지 않으면 결과를 내지 않는다.

요청의 계산 예산은 튜브별 압력 knot 수에 비례해 확인한다. 예산 초과나 수치 범위 실패 시 일부 튜브/구간 결과만 전체 완료처럼 표시하지 않고 실패 위치와 이미 계산한 prefix를 반환한다. 각 튜브, 압력 이력 및 결과의 digest를 보존한다.

## 적용 범위와 한계

이 계산은 일정한 원형 두꺼운 벽, 균질 등방성 선형 탄성, 축대칭 압력 경계로 제한된다. 튜브시트·배플 구속, 편심/타원화, 국부 부식·균열, 접촉, 열응력, 잔류응력, 진동, 압력용량, 코드 acceptance, 사용 수명 또는 고장확률을 계산하거나 추론하지 않는다. plugged 여부만으로 잔류 압력이나 하중 경계를 가정하지 않는다.

`von_mises_Pa`를 포함한 결과는 caller가 공급한 압력·형상 자료 아래의 응력 descriptor다. 재료 허용응력, 설계 계수, 두께 공차, 부식 allowance 또는 승인 기준은 caller/provider가 별도로 정하고 적용성을 입증해야 한다. 본 API는 그러한 한계와 비교해 합격·불합격을 판정하지 않는다.
