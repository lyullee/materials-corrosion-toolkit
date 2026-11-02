# 기상막 수분 응축·증발 및 벽면 액막 재고 이력

## 목적

`integration.wet_co2_gas_film_condensation_transfer_history`는 고정된 벽면 patch의 단위면적당 물 재고를 시간 구간별로 적분한다. 각 구간의 기상 수증기 fugacity, 벽 온도에서의 물 포화 fugacity, 기상막 몰 전달계수, 액상 밀도는 호출자가 제공한다. 모델은 전달계수에 fugacity 구동력을 곱해 몰 flux를 계산하고 물 몰질량으로 질량 flux를 변환한다.

기상 fugacity가 벽 포화 fugacity보다 크면 물이 벽면에 더해지고, 반대면 액막에서 증발한다. 증발 요청이 보유 재고를 초과하면 액막을 0으로 제한하고 요청 초과분을 별도 기록한다. 각 interval 종료 재고에서 등가 균일 액막 두께를 계산한다.

## API 입력

- `WetCo2GasFilmCondensationHistoryRequest`: asset/location/physical-scope/condition/벽 patch ID, 최초 물의 면적 재고, 정확히 맞닿은 시간 구간과 사용성 review.
- `WetCo2GasFilmCondensationInterval`: 시간, bulk 및 벽 포화 fugacity, 기상막 전달계수, 액상 밀도, provider 구성/결과 digest, source Evidence.
- Evidence는 전달계수 provider, 벽 포화 fugacity provider, 밀도 근거를 식별해야 한다. 밀도 record hash는 Evidence hash와 일치해야 한다.
- 검토 플래그가 빠져 있으면 입력 오류로 가정하지 않고 `needs_data`를 반환한다. 단위·시간·유한수·이력 연속성 오류는 contract 단계에서 거부한다.

## 식과 수지

구간별 몰 flux는 `N_w = k_g (f_bulk,w - f_wall,w,sat)`로 계산한다. 질량 재고 증분 후보는 `Δm = N_w M_w Δt`이며, `M_w = 0.01801528 kg/mol`을 사용한다. 최종 재고는 `max(0, m_start + Δm)`이다. 공급되는 기체는 구간 내에서 고갈되지 않는 저장조로 다룬다. inventory balance residual과 요청/허용 증발량을 interval ledger에 보존한다.

## 적용 경계

이 계산은 벽면 응축 가능성만 다루는 기상막 전달 및 물 재고 장부다. 상관식, 유속, Reynolds/Schmidt 수에서 전달계수를 유도하지 않는다. 포화 fugacity와 gas fugacity는 같은 기준으로 비교 가능하다는 호출자 확인이 필요하다. 기본 water 포화는 순수 물 기준이며 염수·MEG의 물 활동도를 대체하지 않는다.

벽 열전도, 잠열 수지, wall temperature 피드백, 방울 핵생성·합체, 배수·전단 제거, 측방 액막 이동, 물질 전달과 탄산 평형의 동시결합은 계산하지 않는다. 따라서 액막 두께 또는 재고는 유효한 부식률·젖음상태·손상·누설·수명·합격 기준이 아니다. 이를 결합하는 더 큰 모델은 각 공급자와 에너지/질량수지 및 검증 자료를 별도로 연결해야 한다.

## 공개 데이터와 사용조건

계산 입력에는 사용자가 권리와 적용성을 검토한 자료를 연결한다. 내장 수치 데이터, 실험 보정계수, 특정 가스 조성의 대표 전달계수는 포함하지 않는다. source record와 Evidence는 구현 근거 및 caller 입력 계보를 구분하며, API 정의만으로 제3자 입력자료의 재배포 권한을 보증하지 않는다.
