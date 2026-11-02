# 간극 공간 전류의 caller 기반 Faraday 손실 매핑

`integration.crevice_spatial_ohmic_partial_current_metal_loss`는 계산된 공간 ohmic 혼합전위 결과의 선택 반응 branch에서 셀별 양극 전류밀도를 적분하고, caller가 검토한 금속·반응 매핑을 통해 고정 셀 면적의 Faraday 질량손실과 균일 등가 후퇴량을 산출한다.

## 입력과 계산

- 상위 `integration.crevice_spatial_ohmic_mixed_potential`의 완료된 `AssessmentResult`, 입력 계보와 전체 결과 SHA-256이 필요하다.
- 각 선택 branch에는 caller가 반응 ID, 전자수, 반응 진행당 금속 몰수, 금속 몰질량·밀도, 전류효율, 셀별 반응면적과 digest-linked Evidence를 지정한다.
- 인접 준정상 knot 사이 전류밀도는 caller가 검토한 선형 재구성으로 간주한다. 각 셀에서 양수 전류밀도의 면적·시간 적분을 정확히 계산하고 Faraday 상수로 반응 진행량을 변환한다.
- 매 interval의 셀별 전하·몰수·질량·후퇴량 및 knot별 누적 등가후퇴량을 반환한다.

## 해석 경계

- 선택 branch의 양전류를 금속 용해로 해석하는 근거, 전자수, 화학량론, 효율, 실제 반응면적, 밀도와 몰질량은 caller가 제공하고 검토해야 한다.
- 이 API는 순수 금속 용해 branch의 gross anodic 등가량만 계산한다. 음극전류의 재도금 크레딧, branch 간 화학반응, 조성 선택용해, 수동화, 확산 제한과 부식 합격 판정은 추론하지 않는다.
- 결과는 각 고정 mesh 셀의 평균 균일 후퇴 환산값이다. pit·crevice 국부 형상 변화·간극 폐쇄·서비스 수명·확률·실험적 부식률 qualification을 나타내지 않는다.
- 상위 시공간 모델 knot는 독립 준정상 상태다. knot 사이 선형 보간은 적분 가정이며 미측정 동역학을 뜻하지 않는다.

## 후속 통합

Registry에 모델을 등록하고 입력 계약을 공개 schema로 export해야 한다. Source catalog에는 caller branch-to-metal mapping과 piecewise-linear positive-current Faraday method를 분리 기록한다. 계산·수치 및 독립 실험 검증은 별도 작업이다.
