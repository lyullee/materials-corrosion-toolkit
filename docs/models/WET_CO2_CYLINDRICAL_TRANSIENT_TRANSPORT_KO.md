# Wet-CO₂ 원통 액막의 유한재고 과도 수송

## 목적

integration.wet_co2_cylindrical_transient_transport는 caller가 제공한 원통 형상 절점에 맞춰 종 농도장을
유한체적 inventory로 적분하는 제한적 과도 모델이다. 기존의 절점별 정상 cylindrical transport·혼합전위
계산과 달리, 이 경로는 초기 셀별 수용액 농도, 외측 경계 농도, 방사 확산계수, 벽 반응 진행률을 시간 구간에
걸쳐 적분하고 종·원소·전하 장부를 닫는다.

Python API:

- 요청: matintegrity.wet_co2_cylindrical_transient_transport.WetCo2CylindricalTransientTransport
- 종 및 반응 계약: WetCo2TransientSpecies, WetCo2TransientWallReaction
- 경계·시간 계약: WetCo2TransientTransportKnot, WetCo2TransientSpeciesBoundary
- 계산: evaluate_wet_co2_cylindrical_transient_transport(request)
- Model ID: integration.wet_co2_cylindrical_transient_transport

## 보존 계산

길이 1 m를 기준으로 방사 셀 k의 부피는 π(r²_outer−r²_inner)이다. 인접 셀 중심 사이의 cylindrical
확산 conductance는 해당 환형 거리의 logarithmic resistance와 piecewise-constant caller diffusivity로
계산한다. 셀 농도 미분은 안쪽 반응 플럭스, 인접 셀 전도, 바깥 bulk 농도 경계 flux의 합을 셀 부피로
나눈다. BDF 적분은 각 절점 쌍의 시간 구간에 수행한다.

경계 농도·확산계수·반응 extent·film 두께·geometry는 구간 왼쪽 절점 값으로 유지한다. 다음 geometry
절점에 도착하면 이전/새 방사 셀 사이의 공통 환형 영역에서 종 몰수를 겹침 적분하여 보수적으로 재격자화한다.
새롭게 포함되는 안쪽 영역의 농도는 caller의 boundary record에 있는 새 bulk 농도를 사용하며, 바깥쪽에서
추가된 영역도 새 bulk 농도로 채운다. domain에서 제외된 안쪽·바깥쪽 종 inventory는 각각 유출 장부로 남긴다.
이 계단형 시간 기준과 sweep fill 조건은 연속 moving-mesh 물리법칙을 뜻하지 않는다.

각 벽 반응은 signed 몰 진행률, 수용액 종 화학양론, 전자수와 alloy 원소 방출량/extent를 caller가 제출한다.
반응별로 수용액의 원소 변화가 alloy 원소 방출량과 일치하고, 수용액 전하 변화가 명시적 전자수와 일치해야
요청을 생성할 수 있다. 음극 방향으로 진행하는 금속 침착 반응은 monotone recession 범위 밖이므로 받지 않는다.
수용액 종 농도·반응·외측 경계·moving-boundary 재격자화 장부를 독립 보존한다.

## 유한 벽 재고와 fail-closed 검사

caller의 초기·최종 관 형상, alloy 밀도, 원소별 질량분율과 원자량으로 축방향 길이당 벽 원소 inventory를
구한다. 반응 진행률을 현재 원통 젖은 둘레에 곱해 누적한 원소 방출은 형상 history가 나타내는 벽 inventory
감소량과 각 knot에서 비교한다. 초기보다 큰 방출, 형상 기반 감소와 reaction ledger의 불일치, 음의 셀 농도,
종 몰수 잔차, 수용액 전하 잔차, reaction/electron 전하 잔차가 허용오차를 넘으면 해당 구간을 실패 처리하고
앞서 완료된 history prefix를 보존한다.

허용오차는 caller가 상대 기준과 몰수/전하별 절대 기준으로 지정한다. inventory, 원소, charge check는
수치 오차 gate이지 화학모델 적합성을 인증하지 않는다.

## 입력 근거·출처

- geometry: digest로 결합한 WetCo2CylindricalScaleGeometryHistory 요청
- 초기 셀 농도: 종별 배열 digest와 Evidence
- 수용액 종: caller 원소식과 전하수
- alloy: 밀도, 원소별 질량분율·원자량을 담은 caller digest와 Evidence
- 각 knot: 모든 종의 bulk 농도·방사 셀 diffusivity, finite wall reaction extent schedule, film 두께를 digest한
  boundary record와 Evidence
- 각 반응: caller가 제시한 calibration digest, licensed Evidence, 종 화학양론 및 외부 금속 원소 전달

새 관측자료나 경험계수는 포함하지 않는다. 계산은 원통 환형 유한체적 확산, species inventory 적분과 명시적
보존 장부의 독립 구현이다. method source ID는
independent_moving_cylinder_finite_volume_inventory_balance다. 입력 source IDs는
caller_signed_cylindrical_wall_reaction_extent_schedule 및
caller_wet_co2_initial_cylindrical_pipe_geometry다. 데이터 재사용 권한은 개별 입력 provider 조건을 따라
호출자가 확인해야 한다.

## 제한과 물리 경계

- 보존 좌표는 관 축방향 길이 1 m다. 유량 대류, 축방향 구배, 액막 유동·난류, 압력손실은 모델링하지 않는다.
- geometry knot 사이 값은 선형 보간하지 않고 왼쪽 값을 유지한다. 반응·경계 history도 piecewise constant다.
- 종 확산은 액상 annulus에서만 계산한다. 고체 scale 내부 확산, 다공도, 조성별 층 순서, cracking/spallation,
  탄산염 종분화, 활동도, homogeneous reaction 및 precipitation는 계산하지 않는다.
- 벽 경계 반응 위치는 현재 bore의 wetted circumference로 처리한다. scale 바깥면과 금속/scale 계면 사이의
  별도 전달저항은 포함하지 않는다. 즉, 이 계산을 porous/protective-scale 모델로 해석하지 않는다.
- 반응률은 caller가 고정한 signed extent 이력이며 Butler–Volmer나 Nernst 식으로 풀지 않는다. 벽 재고 검사는
  제공된 alloy 조성이 벽 전체를 대표한다는 조건부 비교다.
- 움직이는 경계에서 새로 포함되는 셀은 caller가 기록한 새 bulk 농도로 채운다. 실제 경계 sweep 유동·혼합을
  해석한 것이 아니다.
- 시간 수렴, 코드 검증, 실험 비교, 부식수명, 확률, 수용기준, material qualification을 주장하지 않는다.

## 구현·검증 기록

현재 구현은 typed caller 계약, annular finite-volume transient state, conservative exact-knot remap 및 species/
element/charge/wall inventory closure 경로까지 작성한 상태다. 수치 테스트와 package build는 실행하지 않았다.
