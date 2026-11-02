# 확장 요청: SCC 응력확대계수 이력 공급자

## 목적

`degradation.scc_crack_velocity_history`는 caller가 제공한 유한 `K_I(t)`를 받지만, 균열형상·하중·잔류응력으로부터 응력확대계수를 계산하지 않는다. 이 요청은 사용자가 권한을 가진 기존 FEM/파괴역학 모듈에서 digest-bound Mode-I 응력확대계수 이력을 받아 SCC da/dt API에 전달하는 중립 교환 경계를 제안한다.

## 제공 모듈에 필요한 입력 및 계보

1. 자산·위치·physical scope·시편·clock·재료/야금 상태·환경·하중 case ID를 보존한다.
2. 균열 위치·방향·형상 파라미터, 구조 형상/mesh revision, 하중 이력과 잔류응력 basis, 계산된 `K_I` 이력을 서로 구분한다.
3. `K_I`는 Pa·sqrt(m)로 명시하고, 모드 조합·부호·단위 변환·면내 좌표 convention을 결과에 남긴다. Mode II/III를 `K_I`에 합치지 않는다.
4. 결과에는 provider/model/version, solver settings digest, geometry/input digest, source/evidence, exact time knots, convergence/status와 적용범위를 포함한다. Missing, nonconverged, unsupported output은 유효한 숫자 이력으로 보이게 바꾸지 않는다.
5. 출력 clock과 `RunContext`의 asset/location/time basis를 정확히 대조한다. 재표본화가 필요하면 caller가 검토한 mapping을 별도 lineage로 명시하고 자동으로 보간하지 않는다.

## 소비 경계

- SCC growth API에 넘기기 전에 material condition, metallurgy, environment, loading-law identity가 caller curve와 정확히 일치해야 한다.
- 현재 `da/dt(K_I)` 구현은 supplied `K_I(t)`만 사용한다. 균열 성장량에 따라 형상이나 `K_I`를 업데이트하지 않으므로, 기하 피드백·증분 재해석이 필요하면 별도의 versioned outer-coupling 계약과 명시 budget/commit 규칙을 추가한다.
- SCC `da/dt`는 Paris 피로 `da/dN`가 아니다. 주기/빈도/환경 변화를 암묵적으로 환산하지 않는다.
- 계산된 확장량은 한 입력 이력에 대한 결정론 결과다. 사건확률·기간 최초고장확률·허용성은 별도 calibration/evidence를 통해 caller가 제공한다.

## 기대 산출물

- provider 결과를 SCC API 입력으로 옮기는 typed adapter, JSON Schema와 source catalog lineage
- 유닛·clock·시편·geometry/model revision·solver status 불일치 시 fail-closed 사례
- synthetic contract 예시와, 별도로 승인된 경우 독립 계산 결과/실험 기준과 비교하는 검증 기록
- 적용 범위, extrapolation 금지, nonconvergence 및 geometry feedback 제한을 설명하는 매뉴얼

이 요청서는 어떤 외부 저장소도 변경됐다고 주장하지 않는다. 각 provider의 코드·자료 이용권한과 실제 solver 결과 자격화는 소유 프로젝트에서 별도로 검토한다.
