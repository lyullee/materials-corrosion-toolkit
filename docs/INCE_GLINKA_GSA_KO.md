# 다축 피로 generalized strain-amplitude 지표

`InceGlinkaGSACalculation`과 `ince_glinka_gsa_parameter()`는 caller가 제공한 한 개의 닫힌 응력/탄성변형률/소성변형률 텐서 이력과 유한한 평면 후보에서 generalized strain-amplitude (GSA) 지표를 산출한다. 코드가 평가하는 평면별 산식은 다음과 같다.

평면 수×표본 수는 `maximum_plane_sample_evaluations` budget 안에 있어야 한다. 너무 큰 조합은 요청 계약에서 거부해 한 호출의 계산량을 제한한다.

`GSA = (|tau|max/tau_f') * gamma_e,a + gamma_p,a + (sigma_n,max/sigma_f') * epsilon_n,e,a + epsilon_n,p,a`

각 범위 진폭은 입력된 같은 한 사이클 표본의 최대값과 최소값 차이를 2로 나눈 값이다. 전단 변형률은 텐서 전단 성분을 engineering shear로 바꾸어 투영한다. 전단 최대값은 평면 방향 선택 부호의 영향을 없애기 위해 절대값 최대를 사용한다. 인장 정상응력 최대는 부호를 보존하며, 압축 정상응력은 탄성 정상항을 낮출 수 있다. 평면 목록의 GSA 값이 가장 큰 항목을 유한 탐색의 controlling plane으로 기록한다.

산식은 Ince–Glinka 계열의 generalized strain-amplitude 기준과 관련 공개 논문에 근거한다: Zheng-Yong Yu, Shun-Peng Zhu, Qiang Liu, Yunhan Liu, “Multiaxial Fatigue Damage Parameter and Life Prediction without Any Additional Material Constants,” *Materials* 10(8), 923 (2017), [DOI: 10.3390/ma10080923](https://doi.org/10.3390/ma10080923). 해당 논문은 CC BY 4.0으로 배포된다. 이 저장소 구현은 수식과 입력 계약을 별도로 코드화했으며 논문 문장, 표, 실험 관측값은 포함하지 않는다. 출처 인용과 코드/데이터 권리는 별도로 관리한다.

응력 및 두 변형률 분해 이력의 첫·마지막 텐서는 각 caller 허용 오차 안에서 닫혀야 한다. 정상 및 전단은 대칭 텐서의 `[xx, yy, zz, xy, yz, zx]` 순서로 입력한다. 탄성/소성 분해와 재료 강도 계수 `tau_f'`, `sigma_f'`는 caller가 별도 자료와 단위 근거로 제공해야 한다. Evidence, 제공자 revision/configuration digest, 적용성 검토, 사용권 검토, 계산 허가와 plane-grid 지원 검토를 요구한다.

결과는 `parameter`이며 수명 예측이나 damage increment가 아니다. rainflow/주기분해, 여러 주기의 합산, 임의 평면 생성, 연속 방향 최대 탐색, 미표본 이력 보정, 곡선 적합·수명 연결, 재료 간 전이는 하지 않는다. finite plane 최대는 후보 평면의 최대일 뿐 정확한 critical-plane optimum이 아니다. 원 논문은 두 합금과 평가 조건에서 GSA를 검토하면서 저주기 영역에 상대적으로 적합하고 고주기 영역에서 정확도가 낮을 수 있다고 보고했다. 다축 수명 관계식은 전단 지배 조건에서 지나치게 긴 수명을 내는 문제가 보고되어 별도 구현/사용 전에 해당 적용영역을 점검해야 한다. 이는 다른 재료·환경·온도·제작 상태의 검증을 대신하지 않는다.

API 구성과 가상 입력은 `examples/ince_glinka_gsa.py`에 있다. 입력 숫자는 합성 예제일 뿐 측정값이나 권고 물성치가 아니다. 구현과 문서는 작성됐지만 아직 테스트, 계산 실행, 공개 데이터 비교 또는 실험 qualification을 수행하지 않았다.
