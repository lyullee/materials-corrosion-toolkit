# 연속 임계면 FS 계수에서 수명 구간으로의 변환

`fatigue.continuous_plane_fs_life_bound`는 `fatigue.critical_plane_continuous_bound`가 반환한 인증된 Fatemi–Socie 계수 bracket을 입력받아, caller 보정 strain-life 관계로부터 수명 하한과 상한을 구한다. 입력 bound 결과와 보정계수는 전체 payload digest로 고정한다.

계수 구간은 `[F_sampled, F_upper]`이다. caller가 보정된 FS 수명 관계에서 계수가 증가할수록 수명이 감소한다는 단조성을 검토하면 수명 구간은 `[N(F_upper), N(F_sampled)]`가 된다. 두 끝의 수명 방정식이 caller의 cycle support 안에서 모두 풀려야 구간 결과를 반환한다. 어느 한 끝이 support 밖이면 `out_of_scope`와 끝점 진단을 반환한다.

이 API는 기존 연속면 Lipschitz factor bound를 수명 구간으로 전달하는 composition layer다. `continuous_plane_factor_to_life_monotonicity_reviewed`는 별도 caller review다. 결과는 전달된 닫힌 cycle의 선언 factor 정의와 제공된 계수에만 조건부다. 시간표본 사이의 실제 파형, cycle extraction, calibration uncertainty, material transfer, 임계면 법칙의 독립 검증 및 물리 모델오차는 포함하지 않는다. 상한 gap이 큰 경우 반환 수명구간도 넓을 수 있다.

배선 예제는 [continuous_plane_fs_life_bound.py](../examples/continuous_plane_fs_life_bound.py)다. 예제 factor bound는 synthetic wiring 데이터이며 재료 수명 결과나 검증을 주장하지 않는다.
