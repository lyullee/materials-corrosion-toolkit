# 가스켓 joint 축력·전도모멘트·접촉 면적 재조정

## 역할

`integration.gasket_joint_spatial_resultant_balance`는 같은 joint의 계산된 다중 볼트 knot와 정적 unilateral flange contact field를 연결해 축력 잔차, XY축 전도모멘트 잔차, 가스켓 접촉력 중심과 유한 접촉 절점 면적 비율을 계산한다. 플랜지 응답이나 접촉 solver를 다시 수행하지 않는다. 결과 ID, 입력 ID, 원자료 digest, geometry, external-moment evidence를 모두 보존한다.

## 입력 계보

- `fabrication.gasket_multi_bolt_sector_equilibrium`의 `AssessmentResult`, 전체 digest, 선택 step ID. 그 단계의 볼트별 `tensile_force_N`과 scalar `external_separating_force_N`를 사용한다.
- `fabrication.flange_contact_field` 또는 `fabrication.flange_nonlinear_contact_field`의 계산 완료 정적 `AssessmentResult`, 전체 digest. field node ID/순서, force, mean pressure, upstream gasket area를 읽는다.
- 정적 contact result에는 계산 시각 field가 없으므로 두 result digest, joint/scope, 선택 upstream step ID와 시간 knot를 결속하는 caller `contact_time_alignment` record/Evidence/license가 별도로 필요하다.
- 모든 볼트와 contact node의 기준점 상대 XY 좌표, reference center ID, 제공자/revision, geometry digest, Evidence 및 사용권리 ID.
- 선택 시각의 signed external moments `Mx`, `My`, 제공자/revision, joint/time/reference center로 계산한 record digest, Evidence 및 이용권리 ID.
- 두 결과가 동일 joint, physical scope, asset, location이며 정확히 같은 시간 knot를 가리킨다는 caller 검토.

외부 모멘트 digest는 제공자·revision·joint·scope·선택 knot/time·reference center와 signed moment 값을 결속한다. 외부 모멘트가 0이라면 caller가 그 0값과 기준을 Evidence로 선언한다. 이 값은 bolt 결과의 scalar separating force와 중복 계산하면 안 된다.

## 계산식

caller 좌표의 기준점에서 bolt `i`의 closing-force 크기를 `Bᵢ`, gasket node `j`의 compressive contact force 크기를 `Gⱼ`라 정의한다. positive coordinate system은 아래의 xy-force-resultant convention을 사용한다.

- 축력 잔차: `Rz = ΣBᵢ − ΣGⱼ − Psep`, 여기서 `Psep`는 선택 bolt step에 기록된 separating force다.
- signed XY moment convention: point `(x,y)`의 positive force magnitude `F`에 대해 `Mx = Σ yF`, `My = −Σ xF`.
- 모멘트 잔차: `RM = Mbolt − Mgasket − Mexternal`.
- 가스켓 접촉력 중심: `xcp = −My,gasket / ΣG`, `ycp = Mx,gasket / ΣG`; 압축 접촉력이 0이면 중심은 정의하지 않는다.
- finite-node 접촉 면적 비율: 양의 계산 접촉력을 가진 node의 caller gasket area 합 / 모든 선택 node area 합.

결과에는 잔차를 caller 힘·모멘트 허용오차와 비교한 boolean도 포함된다. 이 값은 caller criterion에 대한 정량 대조일 뿐 코드 합격이나 씰 qualification이 아니다.

## 해석 한계

contact node의 평균 압력·면적은 제공된 유한 이산화에 대한 값이다. 연속 압력장을 적분하거나 node 사이 응력·contact patch를 재구성하지 않는다. 좌표계·기준 중심·하중 작용점·외부 모멘트 표기법은 caller가 검토하고 Evidence로 고정해야 한다. bolt result 또는 contact field가 실제 실험/FE의 검증을 받았다고 추론하지 않는다. local bolt/flange stress, gasket damage, leak rate, seal acceptance, code compliance, life 및 failure probability는 계산하지 않는다.
