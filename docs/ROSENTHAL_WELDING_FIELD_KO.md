# 3D 이동 점열원 용접 온도장

`welding.rosenthal_3d_point_source_temperature`는 균질한 semi-infinite solid 표면을 일정 속도로 이동하는 이상 점열원의 준정상 온도 상승을 계산한다. 구현식은 이동 좌표계에서

\[
T-T_0 = \frac{Q_{abs}}{2\pi kR}
\exp\!\left[-\frac{v(x+R)}{2\alpha}\right],\qquad
R=\sqrt{x^2+y^2+z^2},\quad \alpha=\frac{k}{\rho c_p}.
\]

여기서 `x`는 열원 이동 방향의 상대좌표, `y`는 횡방향 위치, `z`는 표면에서 내부로 향하는 깊이, `Q_abs`는 흡수 전력이다. 각 물성은 SI 단위로 입력한다. 좌표는 열원 위치에서의 순간 이동좌표다. 여러 점을 한 번에 평가할 수 있으며, 센서점의 열이력을 구성하려면 각 시간에 대응하는 이동좌표를 caller가 계산해 함께 제공한다. 이동 좌표와 시간은 모델이 자동 생성하지 않는다.

## 입력과 검토

`absorbed_power_W`, `travel_speed_m_s`, `thermal_conductivity_W_m_K`, `density_kg_m3`, `specific_heat_J_kg_K`, 초기온도와 세 좌표 배열을 지정한다. 좌표 배열 길이는 같아야 하며 이상 점열원 위치 `R=0`은 특이점이라 허용하지 않는다. 선택 입력 `time_s`는 좌표 배열과 같은 길이의 strictly increasing 시간이어야 한다. `threshold_temperatures_K`를 지정하면 각 온도 기준의 가열/냉각 통과 시각을 인접 표본 사이 선형 보간으로 계산한다. 모든 통과 bracket을 반환하므로 사용자가 heating과 cooling 교차를 구분할 수 있다. 표본 해상도 검토가 필요하며 특정 두 임계온도 사이 시간을 t8/5 또는 자격 냉각시간으로 해석하지 않는다. 아래 다섯 검토 필드가 모두 `True`여야 계산한다.

- 반무한체 근사와 형상 적용성
- 일정 물성 근사
- 상변태·잠열 무시
- 대류·복사와 용융풀 유동 무시
- 점열원·준정상 이동좌표 근사

검토가 빠지면 `needs_data`를 반환한다. 물성 지원 범위를 벗어났거나 결과가 수치 표현 범위를 벗어나면 완료 계산으로 처리하지 않는다.

## 범위와 제한

이는 고전 이동 점열원 해의 독립 구현이다. 상세 유도와 분포 열원 모델의 가정 비교는 공개된 Tsai–Eagar 논문을 참고할 수 있다: [MIT 공개 논문 PDF](https://eagar.mit.edu/publications/Eagar032.pdf). 해당 논문의 문장·표·그림은 코드나 문서에 복제하지 않았다.

이 계산은 유한 용접 길이, 시작/종료 과도, 판 모서리, 온도 의존 물성, 잠열, 용융풀 대류, 표면 손실을 다루지 않는다. `temperature_K`는 실험 보정 온도장이나 용융 경계가 아니다. t8/5 냉각시간, 경도, 조직, 예열 선정, 잔류응력, 균열 위험, WPS 자격 또는 코드 수용성으로 자동 변환하지 않는다. 다중 패스 이력과 수치/실험 검증은 후속 과제다.

## API

입력 계약은 `RosenthalPointSource3D`이며 registry 모델 ID는 `welding.rosenthal_3d_point_source_temperature`다. sampled model history에서 냉각구간까지 함께 평가하려면 `RosenthalCoolingIntervalLink`와 `welding.rosenthal_cooling_interval`을 사용한다. 연결 API는 고정점의 횡방향/깊이 좌표와 `x_relative(t)=x_relative(t0)-v(t-t0)` 일치 여부를 확인하고, 지정된 단조 냉각 branch만 기존 piecewise-linear cooling interval 추출기에 전달한다. 결과에 Rosenthal 요청 digest와 별도 cooling-interval 입력 digest, 전체 sampled 온도 기록 digest, 선택 branch digest 및 crossing bracket을 보존한다. 위치와 시각 표본을 생성하거나 t8/5 자격을 부여하지 않는다. 두 contract의 전체 정의는 `scripts/export_schemas.py`로 내보낸 JSON Schema에서 확인한다.

합성 입력 구성과 registry 호출 예시는 `examples/rosenthal_cooling_interval.py`에 있다. 예제 수치는 API 연결을 보여주기 위한 임의 입력이며 재료 물성 보정이나 검증 자료가 아니다.
