# 다상 스케일 두께 이력의 층상 수송 연결

`LayeredScaleHistoryStackTransport`는 caller가 별도로 계산한 단일상 스케일 두께 이력들을 한 시점에서 층별 수송 입력으로 연결한다. 하나의 `layer_bindings` 항목은 고유 `layer_id`와 해당 상의 `chemistry.caller_surface_scale_kinetics` 계산 결과를 가진다. 모든 수송 층은 정확히 하나의 상 이력에 대응해야 하며, 각 이력에 `selected_time_s`와 일치하는 출력 절점이 하나 있어야 한다.

요청은 상별 결과와 입력 digest, 상 식별자, 요청한 층 식별자와 선택 시각을 출력 계보에 남긴다. 서로 다른 시간의 이력을 보간하거나 누락 층을 0으로 간주하지 않는다. 선택 절점의 두께만 caller가 정한 층상 수송 특성과 결합하고, 기존 `layered_scale_diffusion_limit()`의 정상상태 확산 제한 계산을 다시 사용한다.

계산 전에는 공통 물리 범위·기판 상태·용액 상태·asset/location/time basis, 상-층 순서 매핑, 공통 시각 및 계산 사용 승인을 확인한다. 각 상별 반응속도 상수와 열역학 자료는 기존 상 이력 입력이 제공한 값을 그대로 사용한다.

## 적용 범위

- 층상 수송 저항에 서로 다른 caller 계산 상의 thickness histories를 같은 시간 절점에서 묶는 composition adapter다.
- 각 층의 effective diffusivity, partition coefficient, 상 순서, covered area fraction과 경계 농도는 caller가 공급한다.
- 이 API 자체는 상의 생성·소멸, 경쟁 석출, 공침, 계면 혼합, 층 재배열, 이동 경계 또는 부식속도를 계산하지 않는다.
- 시간 절점 사이의 거동을 보간하거나 예측하지 않는다. 확산 한계는 기존 모델의 caller 지정 가정에 한정된다.

예제성 수치 계산이나 테스트는 수행하지 않았다. 실제 사용 전에는 상별 kinetic calibration, 상-층 대응, 수송 물성, 별도 benchmark를 독립 자료로 검증해야 한다.
