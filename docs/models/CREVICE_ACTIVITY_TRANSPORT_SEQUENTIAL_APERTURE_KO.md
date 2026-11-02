# 활동도 반응수송과 간극 변화를 구간별로 연결하기

`integration.crevice_activity_transport_sequential_aperture_campaign`은 활동도 보정 반응수송 계산과 caller가 제공한 고체상 반응 extent-rate를 시간 구간마다 순차 연결한다. 각 구간의 시작에는 직전 구간에서 전달된 용액 조성·고체상 재고·균일 간극을 사용하고, 해당 구간을 새 transport 계산으로 다시 푼 다음 고체상 재고 및 다음 구간 간극을 갱신한다.

## 입력과 사용

입력 contract는 `CreviceActivityTransportSequentialApertureCampaign`이다. 전체 기간에 대한 다음 자료를 caller가 제공한다.

- exact time knot와 activity-corrected reactive transport 요청
- 시간 구간별·고체상별·cell별 명시적 반응속도
- 최초 균일 slit aperture, cell 길이, 횡방향 폭, 표면 coverage 및 침전 면 수
- phase별 몰부피와 digest가 일치하는 Evidence
- 종/반응 mapping, geometry, rate 단위와 구간별 geometry update에 대한 review flags

Evaluator `evaluate_crevice_activity_transport_sequential_aperture()`가 segment마다 새 하위 요청을 생성한다. 각 하위 solver 실행은 계산된 segment 시작 시각을 원점으로 옮긴 `[0, duration]` clock을 쓴다. 농도·활동도·온도·경계·속도·반응계수 값은 원래 global clock의 해당 두 절점에서 가져오며, segment 결과에는 원래 절대 시간과 local offset을 모두 기록한다. 각 계산과 하위 입력의 digest가 segment별로 보존된다.

```python
from matintegrity.crevice_activity_transport_sequential_aperture import (
    CreviceActivityTransportSequentialApertureCampaign,
    evaluate_crevice_activity_transport_sequential_aperture,
)

request = CreviceActivityTransportSequentialApertureCampaign(
    # validated transport/kinetic contracts, geometry, Evidence and review flags
)
result = evaluate_crevice_activity_transport_sequential_aperture(request)
```

실제 호출에서는 contract 필드를 빠짐없이 채워야 한다. JSON Schema는 `docs/schemas/CreviceActivityTransportSequentialApertureCampaign.json`에 배포한다.

## 계산 순서

1. 현재 uniform aperture를 `width × aperture`의 단면적으로 변환한다.
2. 해당 시간 구간의 반응수송 요청을 만들고, 시작 농도를 이전 구간의 phase-corrected 농도로 교체한다.
3. `solve_crevice_activity_corrected_reactive_transport()`로 그 구간을 새로 계산한다.
4. 그 구간에 지정된 명시적 cellwise solid extent-rate를 적용하고 phase inventory 및 equivalent aperture를 갱신한다.
5. cell별로 같은 aperture를 유지하는지, 변화량이 caller가 설정한 구간 한계를 넘지 않는지 검사한다. 다음 구간에는 갱신된 aperture와 액상/고체상 재고를 넘긴다.

각 segment는 입력/수송/phase handoff/result의 digest를 기록한다. 어느 하위 계산이 실패하거나 geometry 조건을 벗어나면 이전 완료 segment prefix와 실패 위치를 반환한다.

## 적용 범위와 제한

- 구간마다 한 번씩 계산하는 **순차 operator split**이다. 구간 내부에서 transport–kinetics–geometry를 반복 수렴시키지 않으며, fixed-point 수렴을 주장하지 않는다.
- 고체상 속도는 caller가 제공한 구간별 일정 rate다. saturation callback으로 kinetics를 재계산하지 않는다.
- 현재 활동도 수송 요청은 하나의 scalar cross-section만 허용한다. 따라서 최초 간극은 균일해야 하며, phase 결과도 모든 cell의 aperture가 허용 오차 안에서 균일해야 한다. cell별 간극 편차는 평균화하지 않고 거부한다.
- 구간 간 aperture 변화가 설정 한도를 넘으면 자동 substep을 만들지 않고 실패를 반환한다. caller는 더 짧은 time knots로 다시 요청해야 한다.
- 영점 농도는 기존 request contract의 양수 조건 때문에 일부 species에서 다음 segment 입력으로 사용할 수 없을 수 있다. 이런 상태는 contract 오류로 안전하게 거부된다.
- morphology, porosity, adhesion, 자동 speciation/phase discovery, 고체 kinetics 추정, qualified corrosion law, service life, risk probability를 계산하지 않는다.

이 모듈은 fixed-geometry activity transport 계산을 구간 경계에서 연결하는 코드 경로다. 비균일 moving geometry나 구간 내 nonlinear coupling을 원하면 transport solver와 geometry state contract에 시간·공간 단면적 field를 직접 추가하고, 모든 상/용액 수지를 보존하는 확장 작업이 필요하다.
