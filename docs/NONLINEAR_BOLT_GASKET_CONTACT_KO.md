# 사용자 곡선 기반 비선형 볼트–가스켓 접촉

`fabrication.nonlinear_bolt_gasket_contact`는 caller가 제공하고 계산 사용 권한을 확인한 두 곡선을 이용해 단일 자유도 준정적 joint force balance를 푼다.

## 곡선 계약

- 가스켓은 압축량에 따른 접촉력 표다. 압축량과 힘이 모두 엄격 증가해야 하며 `(0 m, 0 N)`에서 시작한다.
- 볼트 곡선은 signed extension change에 대한 bolt force change 표다. 두 축이 엄격 증가하고 `(0 m, 0 N)` 원점을 포함해야 한다. 초기 bolt force는 사용자가 선언한 초기 압축에서 gasket curve가 주는 clamp force로 둔다.
- 두 곡선의 source ID와 SHA-256을 보존한다. material/temperature/geometry에서 곡선 사용의 적합성과 균일 접촉 가정을 caller가 검토한다. 입력 범위 밖 외삽은 하지 않는다.

폐쇄 접촉 상태에서 현재 gasket 압축량을 `c`, 초기값을 `c0`, bolt free-length 변화량을 `ΔL`, bolt 곡선의 force-change 함수를 `ΔFb`, gasket 함수를 `Fg`, 초기 clamp force를 `F0`, 외부 분리하중을 `Fext`라 하면 잔차는 다음과 같다.

`R(c) = F0 + ΔFb(c0 - c - ΔL) - Fg(c) - Fext`

곡선이 단조이므로 지원구간 내에서 닫힌 접촉 평형은 최대 하나다. 해는 bracket 내부 bisection으로 계산한다. 접촉력이 사라지면 bolt curve로 분리 변위를 구하고 gap을 별도로 반환한다. 지원구간이 부족하거나 equilibrium이 bracket되지 않으면 상태를 `out_of_scope`로 보존한다.

## 범위 한계

이 모델은 표 형태의 비선형 구성요소 응답을 조합하는 단일 자유도 정적 평형이다. 검토된 equivalent bolt/assembly compliance를 곡선에 담아 쓸 수 있지만, 프로그램이 그 곡선을 생성하거나 정당화하지 않는다. flange 표면의 공간 휨, gasket 접촉압 분포, 온도별 곡선 전이, history-dependent hysteresis, relaxation, leakage, dynamic response와 설계 합격은 포함하지 않는다. 내부 수치 해법은 구현되어 있지만 이번 코딩 단계에서 실행 검증이나 공학 자격화는 하지 않았다.

## 연결

Python 계약은 `matintegrity.gasket_contact.NonlinearBoltGasketJoint`, `BoltForceChangePoint`, `GasketCompressionPoint`다. 계산 함수는 `evaluate_nonlinear_bolt_gasket_joint(request)`이며 registry ID는 `fabrication.nonlinear_bolt_gasket_contact`다. 합성 입력은 `examples/model_inputs.json`에서 같은 ID로 찾을 수 있다.
