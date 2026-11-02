# Wet CO₂ scale–전기화학 동시 이력 계산

`integration.wet_co2_scale_corrosion_simultaneous_history`는 caller가 제공한 wet-CO₂ 용액 경계와 Butler–Volmer 반응, metal-to-scale 변환 자료를 사용해 단일 패치의 scale 두께 및 벽 두께를 시간에 따라 함께 적분한다. API는 기존 `integration.wet_co2_scale_corrosion_moving_geometry_history`의 interval 끝점 연산자 분할과 달리, ODE solver가 각 내부 시간 지점에서 현재 scale 두께를 반응물 film 두께로 되돌려 전달하고 제한 혼합전위를 다시 계산한다.

## 계산

각 caller interval 안에서 경계 조성, 온도, 전기화학 파라미터, 외부 net scale flux는 상수로 둔다. 현재 scale 두께 `s(t)`로 기존 Fick film transport cap을 갱신하고 caller 반응곡선 지원 범위에서 zero-current 혼합전위를 계산한다. 반응별 anodic partial current는 Faraday 관계 및 caller atom/extent 계수로 metal flux로 바뀐다. metal-to-scale yield와 외부 scale flux로 scale inventory를 갱신하며, alloy density와 molar mass로 uniform wall recession을 산출한다. SciPy BDF가 다음 상태를 함께 푼다.

- scale thickness / scale molar inventory
- remaining wall thickness
- reaction별 cumulative metal loss
- cumulative caller external scale flux

반응계수·metal-to-scale 환산·재료 상태·외부 scale flux 및 scale molar volume은 caller가 데이터, Evidence, revision, digest와 검토 상태를 제공해야 한다. Caller source별 라이선스나 계산 사용권도 독립적으로 확인해야 한다.

## 적용 경계

- 이 계산은 기존 branch-scaled Butler–Volmer/steady planar-film closure를 내부 시각마다 재풀이해 기하와 유효 전달 용량을 동시 갱신한다. 이는 full spatial diffusion-reaction-electrode PDE가 아니다.
- 한 interval에서는 열, 기체-액체 CO₂ 전달, 용액 조성, 온도, 외부 scale flux 및 반응 파라미터가 변하지 않는다고 둔다.
- scale은 붙어 있고 균일한 층, 벽 손실은 면적 평균 균일 침식으로 모델링한다. crack, 박리, 기공, lateral flow, 표면 거칠기 및 국부 침투는 계산하지 않는다.
- scale이 caller 지원 최소 두께에 도달하거나 벽 두께가 고갈되면 해당 interval을 중지하고 완료 prefix를 보존한다. 임의로 bare-metal branch로 전환하지 않는다.
- 계산된 잔차는 이산 질량·기하 수지 진단이다. 독립 실험 검증, 코드 허용성, corrosion rate qualification, 잔여수명, 위험확률 및 FTA event 확률을 뜻하지 않는다.

상세 수식 및 계약은 공개 API docstring과 생성된 JSON schema를 따른다. 본 구현은 generic scale-protection law나 자동 chemistry discovery를 제공하지 않는다.
