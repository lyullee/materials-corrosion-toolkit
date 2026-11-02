# 혼합 crevice 수용액 반응 kinetic network

`CreviceAqueousKineticNetwork`는 하나의 well-mixed, constant-volume 액상에서 caller가 제공한 유한 aqueous reaction network와 벌크 교환을 시간 적분한다. API는 반응물/생성물의 정수 화학량론으로 signed stoichiometric vector를 만들고, 각 시간 구간에 고정된 전·역 rate coefficient를 적용한다.

각 반응의 진행률은 `r = k_f * product(C_i ** nu_i) - k_r * product(C_j ** nu_j)`이다. `k_f`, `k_r`의 단위는 각 반응 차수에 따라 달라지므로 입력은 별도로 단위를 기록하고 caller가 단위 일관성을 확인해야 한다. 순교환 항은 `Q/V * (C_bulk - C)`이며 volume, interval temperature, bulk concentration, flow, 두 rate history는 시간 구간별 상수다. 구간마다 temperature에 맞는 보정 계수를 caller가 제공한다. 코드가 Arrhenius 계수나 활동도 계수를 생성하지 않는다.

반응 입력의 원소 조성과 전하를 이용해 모든 반응의 보존을 계약 생성 시 확인한다. 적분은 SciPy의 implicit BDF 또는 Radau를 사용한다. concentration, 교환 몰 inventory/volume, reaction extent/volume를 증강 상태로 같이 적분해 수지 잔차와 구간별 교환/반응량을 반환한다. 설정한 function-evaluation budget을 넘거나 솔버가 실패하면 실패 구간은 결과에 커밋하지 않고 이전의 완성 구간만 남긴다. 음의 농도는 clipping하지 않고 계산을 중단한다.

입력 조건은 명시적 species set, 동일한 액상/체적, 정확히 이어지는 구간, 원소/전하 보존식, rate 계수 단위와 온도 지원성 및 계산 권한이다. 원자료나 모델 parameter의 출처와 재사용 권리도 Evidence로 연결한다. 공개 합성 예제는 `examples/crevice_aqueous_kinetic_network.py`에 있다.

이 계산은 활동도·산염기/복합체 평형, 상 발견, 침전·용해, 종별 확산/전기이동, 전극 전위, 벽면 반응, 단면 변화, 부식률 및 수명 평가를 수행하지 않는다. 일정 체적 완전혼합 반응조라는 가정도 실제 crevice에서 자동 성립하지 않는다. 이 API가 returned status `computed`인 것은 선언된 ODE를 계산했다는 뜻이지, kinetic parameters나 crevice 물리의 검증/자격화를 뜻하지 않는다.

계산 실행·테스트·물리 검증은 하지 않았다. 한강 증분 검증 묶음에 별도 계산 비교를 추가하기 전에 schema와 catalog 연결이 필요하다.
