# 유한표본 Dang Van 파라미터의 caller 수명곡선 연결

`fatigue.dang_van_finite_parameter_life`는 `fatigue.dang_van_finite_sample_limit_screen`의 digest가 확인된 결과에서 유한표본 Dang Van-style parameter를 가져와 caller 제공 parameter/life 곡선에 연결한다. limit screen 자체에 수명 법칙을 추가하는 것이 아니라, 그 finite-set parameter와 별도로 보유한 same-condition 실험 calibration 사이의 명시적 매핑이다.

## 입력 고정

- upstream `AssessmentResult`의 전체 SHA-256과 model ID/version/input/context digest를 확인한다. 지정된 유한표본 Dang Van screen variant와 Pa 출력 단위만 허용한다.
- curve에는 material condition ID, exact parameter-definition ID, source ID/SHA-256/Evidence, license/use-basis, 조건설명 digest가 포함된다.
- parameter 점은 양수 strict 증가, cycles-to-failure는 양수 strict 감소여야 한다.
- curve material condition은 upstream screen의 calibration material condition과 정확히 일치해야 한다. 재료, 열처리, 온도, 환경, 시편/시험 basis를 별도로 확인한다.

## 수명 매핑

screen의 `equivalent_screening_parameter_Pa`를 log(parameter)-log(cycles) 좌표에서 caller curve에 사상한다. 정확한 knot는 그대로 반환한다. 양 끝 지지구간 밖에서는 `out_of_scope`를 반환하고 외삽하지 않는다. 계산 결과에는 screen/result/input, curve와 condition digest를 남긴다.

## 경계와 해석

모델은 정해진 finite shear-system 집합과 finite time samples에서 계산된 Dang Van-style 파라미터만 소비한다. continuous plane optimum이나 시간표본 사이의 극값은 다시 찾지 않는다. 결과 curve는 사용자 교정자료의 경험적 life mapping이지 보편적인 Dang Van 수명식이 아니다. variable-amplitude Miner 합계, cycle counting, sequence effect, scatter, 확률, acceptance, qualified remaining life 또는 재료 qualification을 제공하지 않는다.

## 근거

기반 parameter와 applicability contract는 기존 [유한표본 Dang Van screen](DANG_VAN_FINITE_SAMPLE_SCREEN_KO.md)의 caller inputs와 finite-set 정의를 그대로 따른다. 본 adapter에 수치 자료를 포함하지 않으며, cycle-life calibration은 caller가 출처·권리·조건 Evidence를 제공해야 한다.
