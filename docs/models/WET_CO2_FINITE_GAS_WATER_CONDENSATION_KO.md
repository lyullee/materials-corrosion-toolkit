# 유한 기상 수증기 재고와 벽 액막의 응축·증발 이력

## 목적

`integration.wet_co2_finite_gas_water_condensation_history`는 유한한 기상 수증기 재고와 고정 벽면 patch의 액막 재고 사이에서 일어나는 구간별 전달을 계산한다. 앞선 `integration.wet_co2_gas_film_condensation_transfer_history`가 각 구간의 bulk fugacity를 caller가 외부에서 제공하는 방식이라면, 이 모델은 기상 수증기 몰수에서 해당 구간의 수증기 분압과 fugacity를 매번 계산하고 transfer에 따른 기체 고갈·증가를 반영한다.

## 계산식

각 구간에서 수증기 성분은 이상기체 부분압력 `p_w = n_w R T / V`와 caller fugacity coefficient `phi_w`를 따른다. 벽의 포화 fugacity `f_w,sat`와 비교하여 `dn_w/dt = -A k_g (phi_w p_w - f_w,sat)`를 적용한다. 온도·체적·전달계수·벽 포화 fugacity가 interval 내 상수이면 이 선형 상미분방정식의 해를 지수함수로 직접 계산한다.

가스에서 액막으로 이동한 몰수는 액상 면적재고에 물 몰질량으로 환산해 더한다. 액막 증발 요청이 가진 액상 재고를 넘으면 상수 입력에 대한 정확한 dryout 시각을 계산하고 액막 재고를 0으로 제한한다. 기체 inventory 변화와 액막 inventory 변환값의 합을 닫힘 잔차로 남긴다.

## 주요 입력

- 초기 기상 수증기 몰수와 초기 벽 물 면적재고
- 연속된 exact interval마다의 `T`, `V`, `phi_w`, 벽 포화 fugacity, 기상막 전달계수, 전달면적 및 액상 밀도
- 전달계수, 벽 상태, 밀도 자료 각각의 provider/source ID, 버전, digest와 Evidence
- 이상기체 성분분압, fugacity 환산, 전달법칙, 고정 patch 및 상수 interval 상태의 검토 플래그

모든 시간 절점은 elapsed time 0부터 정확히 연속해야 한다. 구간 입력이 빠지거나 review가 부족하면 계산 결과를 성공으로 처리하지 않는다.

## 가정과 사용 범위

이 모델은 기체 혼합물 전체가 아니라 물 증기 성분의 유한 재고만 계산한다. 기타 기체 조성이나 전체 압력, CO₂ 전달, 액상 탄산 평형은 풀지 않는다. caller가 제공한 fugacity coefficient로 부분압력과 fugacity를 잇고, 전달계수 및 벽 포화 fugacity는 각 구간에서 일정하다고 둔다. 시간 간격 내 전달은 지수해로 적분한다.

열용량, 잠열, 벽 열전도 및 온도 피드백은 고려하지 않는다. 염수·MEG의 물 활동도는 caller 포화 fugacity 입력을 대신하지 않으며, 방울 생성·배수·액막 측방 이동, 가스 bulk 흐름, 스케일·부식 반응, acceptance도 계산하지 않는다. 따라서 결과 두께는 물리적으로 검증된 부식률·젖음 판단·수명 지표가 아니다.

## 데이터와 권리

내장 실험값이나 전달계수 상관식은 없다. 모든 계수와 벽 포화 상태는 caller가 자료 출처, 물질·조성·상태 범위, 라이선스 및 적용 가능성을 확인한 값이어야 한다. Evidence와 digest는 재현 가능한 provenance를 제공하며, 제3자 자료의 배포 권한이나 물성 적합성을 대신 판정하지 않는다.
