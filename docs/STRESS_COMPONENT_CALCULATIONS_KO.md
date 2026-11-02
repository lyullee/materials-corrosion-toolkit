# 응력 성분과 단면 산술

## 평면 단면의 두께 방향 응력 선형화

`structural.planar_stress_linearization`은 `PlanarStressLinearization`을 받는다. 물리 범위·하중 경우·고정 좌표계·응력 성분 정의와 증가하는 위치(m), 부호 있는 성분 응력(Pa)을 정렬해 제공한다. `section_model`은 `constant_width_planar_piecewise_linear_component`로 명시한다. 전체 경로가 일정 폭의 평면 단면을 나타내고 표본 사이에서 응력 성분이 선형이라는 적용성은 호출자가 검토해야 한다. 입력과 사용 권한은 `CorrelationBasis`로 해시에 연결한다.

두께를 `t`, 중심으로부터 거리를 `z`라 할 때 다음 단면 적분을 보존하는 직선을 구성한다.

- 막 성분: `m = integral(stress dz) / t`
- 중심에 대한 모멘트: `M = integral(z * stress dz)`
- 굽힘 성분: `b(z) = 12 * M * z / t^3`
- 잔차: `r(z) = stress(z) - m - b(z)`

구간별 선형 함수를 해석적으로 적분한다. 계산 내부에서는 정규화 위치와 유리수 산술을 사용하며, 최종 출력이 표현되지 않거나 비영 성분·결과력이 언더플로로 사라지면 `out_of_scope`로 반환한다. 좌표를 평행 이동해도 응력 분해는 같고, 두께 배율은 단위 폭 힘에 1차, 모멘트에 2차로 반영된다.

막 응력, 양 끝의 부호 있는 굽힘 응력, 단위 폭 막 힘(N/m)·굽힘 모멘트(N), 각 표본의 선형 성분과 잔차, 최대 절대 잔차를 반환한다. 잔차 극값은 선언된 구간별 선형 이력에 대한 값이며 표본 사이의 미관측 극값을 보장하지 않는다.

성분 분해와 잔차의 일반적 의미는 [Ansys 공식 설명](https://ansyshelp.ansys.com/public/Views/Secured/corp/v251/en/wb_sim/ds_linearized_stresses.html)으로 독립 확인했다. 제품 고유 수치 절차·축대칭 보정·상용 코드를 복제한 구현은 아니다.

이 API는 고정 좌표계의 응력 성분을 처리한다. 등가응력 스칼라를 먼저 계산한 후 선형화하면 성분별 분해와 같지 않으므로 자동으로 대체하지 않는다. 경로 선택·좌표 회전·곡률 보정·비균일 폭·응력 범주 지정·허용값·피로 수명은 별도 과제다. 평면 결과를 곡면이나 축대칭 단면의 규격 해석으로 표시하지 않는다.

## 평균 전단응력

`structural.mean_shear_stress`는 `MeanShearStress`의 부호 있는 힘(N)을 양의 유효 전단면적(m²)으로 나눈다. 물리 범위와 힘의 양의 방향 정의를 보존하며, 결과는 `signed_mean_shear_stress_Pa`다. 유효 목두께·하중 분배·국부 전단 분포와 규격 전단 허용값은 생성하지 않는다. 비영 결과의 언더플로와 오버플로는 보류하고 실제 영 힘은 영 응력으로 계산한다.

## 사용자 계수의 셸 특성길이

`structural.declared_shell_characteristic_lengths`는 `DeclaredShellCharacteristicLengths`를 받는다. 명시된 반경 정의와 양의 반경·두께(m)에서 `sqrt(radius * thickness)`를 구하고 사용자가 지정한 비음의 길이 배율을 각각 적용한다. 중간 `radius * thickness`가 먼저 넘치지 않도록 제곱근을 분리한다. 기본 배율이나 규격 기준은 없다. 계산된 길이만으로 국부 응력 영역·불연속 간격·독립성·허용 여부를 판정하지 않는다.

## 연동과 검증 범위

세 API는 기본 레지스트리의 `run` 및 `run_json`에서 사용할 수 있다. 입력의 식별자·계수·관측을 변경하면 전체 입력 해시를 다시 검토해야 한다. 이번 계산은 응력 해석기의 결과나 관측 성분을 처리하는 산술이며 전체 구조 해석·규정 승인·독립 실험 검증을 대신하지 않는다.

자체 작성한 비대칭 삼각형 분포의 수지, 선형·일정 부호 응력, 좌표 이동·두께 배율, 잘못된 표본 순서와 길이, 결과력의 수치 범위, 부호 있는 전단응력, 특성길이의 중간 곱셈 오버플로 회피, 해시 변경 및 세 API의 Python/JSON 일치를 포함한 관련 21개 테스트와 정적 검사가 통과했다.

## 로그 기울기의 파단강도 계수

`creep.declared_log_slope_rupture_factor`는 `DeclaredLogSlopeRuptureFactor`를 받는다. 재료 상태·기울기 정의의 식별자, 음의 `negative_log_time_per_log_stress_slope`, 1보다 큰 `logarithm_base`, 양의 `upper_factor_cap`을 모두 명시한다. 기울기의 방향은 로그 시간 변화/로그 응력 변화다. 반대 방향으로 정의한 기울기를 자동으로 바꾸지 않는다.

`uncapped_factor = logarithm_base ** (1 / slope)`를 계산한 뒤 사용자 상한과의 최솟값을 `capped_factor`로 반환한다. 반환 수치가 같은 경우 `controlling_terms`에 두 항을 남긴다. 양의 원래 계수가 언더플로로 사라지면 0이나 상한으로 대체하지 않고 보류한다. 재료 기울기·규격 상한·파단 수명·허용응력은 제공하지 않는다.

## 온도 경향값의 강도 환산

`materials.temperature_trend_strength_scaling`은 `TemperatureTrendStrengthScaling`을 받는다. 재료 상태·물성 정의·경향 근거 식별자, 기준·평가 절대온도(K), 양의 기준 강도와 두 온도의 양의 경향 강도(Pa)를 제공한다. 같은 온도와 같은 경향 근거에 서로 다른 경향값을 주면 거부한다.

계산은 `reference_strength * trend_at_evaluation / trend_at_reference`다. `scaled_reference_strength_Pa`, `trend_ratio`, `trend_ratio_representable`과 물성·온도·근거 식별자를 반환한다. 유리수 산술로 전체 비율을 구성하므로 중간 비율이 넘치거나 언더플로여도 최종 강도가 표현 가능하면 이를 보존한다. 이 경우 비율은 `null`, 표현 가능 여부는 `false`다. 최종 양의 강도 자체가 표현되지 않으면 보류한다.

경향값을 만들거나 보간·외삽하지 않으며 최소 강도 보증·재료 선정·규격 허용값을 부여하지 않는다. 이미 공급된 후보 강도·배율에서 최솟값을 고르는 `materials.scaled_strength_minimum`과 입력 및 역할이 다르다.

추가한 두 강도 산술은 자체 작성한 거듭제곱 해·상한·동률·로그 밑·잘못된 기울기 및 수치 범위, 온도 경향 비율·동일 온도 일관성·중간 비율의 범위 이탈, 해시 변경과 Python/JSON 일치를 포함한 관련 20개 테스트 및 정적 검사를 통과했다. 물리적 파단 데이터 보정이나 독립 실험 검증 결과는 아니다.
