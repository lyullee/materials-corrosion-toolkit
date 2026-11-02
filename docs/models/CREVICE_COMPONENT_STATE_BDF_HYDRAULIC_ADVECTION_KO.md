# Crevice component-state BDF의 고정 형상 hydraulic advection

## 목적

`integration.crevice_component_state_bdf`의 선택 입력 `hydraulic_component_advection`은 별도 계산된 transient planar-slit inertance history를 component-state BDF의 stage RHS에 연결한다. stage aqueous equilibrium으로 얻은 종 농도와 부호가 있는 exact inertance flow를 사용해 upwind species face flux를 계산하고, caller 보존 component basis로 투영한다. face flux는 BDF component inventory 미분에 직접 들어간다.

## 입력 계약

- `bind_crevice_hydraulic_component_advection`에 BDF request, hydraulic request/result 및 결과 digest를 전달한다. hydraulic result는 committed 상태, 동일 request digest, exact clock와 ordered cell IDs를 만족해야 한다.
- inlet/outlet reservoir 종 농도는 모든 exact knot에 제공하고 Evidence가 시각·종 순서·양쪽 이력의 digest를 핀해야 한다. 전기중성, computation authorization 및 fixed-geometry applicability 검토가 필요하다.
- hydraulic cell geometry에서 계산한 solution volume은 BDF template volume과 일치해야 한다. aperture는 전체 구간에서 고정이어야 한다.
- caller가 최대 절대 유량과 계산 사용 review를 제공한다.

## 수지와 한계

유량은 각 hydraulic interval의 inertance 해를 BDF 평가 시각에서 계산한다. 부호가 바뀌면 상류 셀 또는 해당 경계 reservoir를 바꾼다. BDF state vector에는 좌·우 경계의 누적 성분, 원소, 전하 교환량이 분리되어 추가된다. commit 조건은 cell/component 및 element balance와 system-plus-reservoir closure를 포함한다.

이 모드는 고정 aperture/volume slit-flow와 보존 성분 advection만 다룬다. moving boundary, variable-volume 재격자화, Navier–Stokes, 압력-반응의 유동 되먹임, 반응·상 자동 선택은 계산하지 않는다. hydraulic history의 적용성과 경계 농도는 caller 책임이다. qualification을 주장하지 않는다. 수치 검증은 아직 수행하지 않았다.
