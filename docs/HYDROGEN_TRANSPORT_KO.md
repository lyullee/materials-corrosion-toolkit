# 유한 평판·원통의 수소 수송과 속도식 트랩

`transport.hydrogen_slab_kinetic`은 평판 내부의 격자 수소 이동과 고정 트랩의 포획·탈리를 함께 계산한다. `transport.hydrogen_finite_cylinder_kinetic`은 같은 원자 mol·트랩 관례를 유한 원통의 반경–축 2차원 축대칭 격자로 확장한다. 사용자가 초기 분포, 온도·격자 확산계수, 트랩별 속도 이력과 각 표면의 고정 농도, 선형 표면전달, 축약 가역 표면반응 또는 무유량 경계를 공급한다. `transport.hydrogen_dissociative_surface_rates`는 검토된 기체 구동량과 유효 Arrhenius 계수로 두 표면반응 capacity 이력을 만든다. 어떤 계산기도 재료 보정계수나 기체 수소 파괴 기준을 기본값으로 제공하지 않는다.

물리식의 공개 근거는 [Díaz 외, 2025](https://doi.org/10.1016/j.engfracmech.2025.111007)의 주파수 단위 포획·탈리 표현이다. 보존식·이산화·소거식·비선형 풀이와 합성 검사는 이 프로젝트에서 독립적으로 작성했다. 외부 코드·규격 표·실험 곡선은 포함하지 않는다.

## 물리량과 적용 범위

모든 수소 농도는 **수소 원자의 mol/m³**다. 격자 site 밀도 `N_L`과 트랩 site 밀도 `N_p`도 mol/m³이며 금속 원자 밀도나 H₂ 분자 농도와 구분한다. 셀 평균 격자 농도는 `C_L=N_L u`, 트랩 농도는 `C_p=N_p v_p`다. `u`, `v_p`는 0~1의 점유율이다. site 정의의 다중성은 site density에 한 번만 반영한다.

고정된 균일 site population에 대해 다음 보존식과 속도식을 사용한다.

```text
∂(C_L + Σ C_p)/∂t = -∂J/∂x
J = -D_L(t) ∂C_L/∂x
dv_p/dt = κ_p(t) u (1-v_p) - λ_p(t) v_p (1-u)
λ_p(t) = κ_p(t) exp[-E_p/(R T(t))]
```

`κ`, `λ`의 단위는 모두 s⁻¹이다. `κ u`를 농도에 비례하는 다른 관례의 속도상수와 혼동하지 않는다. 각 트랩은 다음 두 모드 중 하나를 명시한다.

| `rate_model` | 필요한 입력 | 계산 규칙과 검토 |
|---|---|---|
| `binding_energy_ratio` | `κ(t)`, 양의 결합에너지, 온도 | `λ/κ=exp[-E/(RT)]`; 에너지 기준과 상세평형 근사 검토 필요 |
| `independent_frequencies` | `κ(t)`, `λ(t)` | 두 이력을 그대로 선형 보간; 별도 근거와 `independent_rate_histories_reviewed` 필요 |

`E_p`는 격자 기준 양의 결합에너지다. 비율 모드는 해당 온도 범위에서 사용할 수 있는 유효 자유에너지 근사와 속도 prefactor 관례를 검토한 경우에만 적용한다. 독립 모드는 population에 결합에너지를 보존하더라도 속도 계산에 사용하지 않으며 온도 변화로 두 이력을 덮어쓰지 않는다. 따라서 서로 다른 유효 prefactor·엔트로피 효과를 외부에서 보정한 속도 이력을 전달할 수 있지만, 이 계약 자체가 그 물리량을 분해하거나 원자 규모 전이상태를 식별하지는 않는다. 비율 모드에서 `κ=0`이면 두 속도가 0이 되어 population이 동결된다. 독립 모드에서는 `κ=0`, `λ>0`인 방출 이력도 허용한다. 작은 탈리율이 부동소수점 범위를 벗어났다는 이유로 임의의 비가역 트랩으로 바꾸지 않는다.

이 식의 정지 조건은 `v/(1-v)=exp(E/RT) u/(1-u)`이므로 기존 `transport.hydrogen_trap_equilibrium`과 연결된다. 빠른 평형은 이 계산의 필수 가정이 아니며 실제 속도와 시간 해상도를 검토해야 한다. 트랩 밀도는 격자 site에 비해 희박하다는 모델 조건이 있고, 사용자가 검토한 전체 밀도비 상한을 명시한다. 이 상한이나 검토 bool은 실험 적합성 인증을 대체하지 않는다.

다음 범위는 별도 구현·검증이 필요하다.

- 구·비축대칭 3차원 형상, 면내/방위각 변화, 비균일 온도와 열확산
- 응력 구배·소성에 따른 생성/소멸 트랩·이동 전위·입계 네트워크
- 한 결함의 여러 H 점유와 상호작용, 수소화물 형성
- 전기화학 전류에서 경계조건으로의 역변환, 다중 흡착상태·오염·산화막·재결합을 포함한 상세 표면 미세반응
- 검출기·배경·시편 전달 지연을 포함한 실제 TDS 관측 모델
- 수소 균열 성장·취성·파괴 기준·기간 고장확률

## 입력과 교환 계약

`HydrogenSlab`은 재료 상태·격자 기준·경과시간 원점 ID, 평판 두께, 셀 수, 초기 셀 평균 격자 농도와 시간 knot를 갖는다. knot는 0에서 시작해 엄격히 증가하고 온도·확산계수·포획 빈도·표면 농도가 같은 knot를 사용한다. 각 이력은 knot 사이에서 선형 보간한다. 중복 시각으로 불연속을 감추지 않는다. 명확한 순간 변화는 상태를 보존한 새 구간 계산이나 검토된 유한 ramp로 구성해야 한다.

`HydrogenKineticTrap`은 기존 `HydrogenTrapPopulation`에 속도 모드, 포획 빈도 이력, 선택적인 독립 방출 빈도 이력, 초기 셀별 점유율과 별도 속도 근거를 더한다. 모든 속도 이력은 공통 시간 knot와 일치해야 한다. 비율 모드에 방출 이력을 함께 넣거나 독립 모드에서 이를 생략하면 입력을 거절한다. 선택한 모드에 해당하는 검토 플래그가 없으면 계산하지 않고 `needs_data`를 반환한다. 결과에는 `rate_model`과 속도 이력 digest가 남는다. 재료 상태와 격자 ID가 형상 계약과 다르면 입력을 거절한다. 점유율의 실험 지원 범위는 population별로 보존한다. 원자 규모 에너지의 존재만으로 포획 빈도를 결정하지 않는다. 외부 공급자 확장은 [원자 규모 수송 요청서](extension_requests/ATOMISTIC_TRANSPORT_KO.md)를 따른다.

### 열활성화 속도 공급자

`transport.hydrogen_trap_thermal_rates`는 검토된 온도 knot에서 capture와 release 빈도를 따로 생성한다. 각 방향은 다음 중 하나를 독립적으로 선택할 수 있다.

```text
Arrhenius:         k(T) = A exp[-Ea/(R T)]
transition state:  k(T) = κ (k_B T/h) exp[ΔS‡/R] exp[-ΔH‡/(R T)]
```

Arrhenius는 절대 prefactor(s⁻¹)와 활성화에너지(J/mol)를 받는다. 전이상태 모드는 활성화 엔탈피(J/mol), 활성화 엔트로피(J/(mol·K)), 0보다 크고 1 이하인 transmission coefficient를 받는다. `k_B`와 `h`는 정확한 SI 정의값을 사용한다. 전이상태 식의 공개 서지는 [Eyring, 1935](https://doi.org/10.1063/1.1749604)이며 문장·표·그림·계수나 외부 코드를 포함하지 않고 식을 독립 구현했다.

입력은 trap·재료 상태·격자·에너지 기준·경과시간 원점 ID, 적용 가능한 온도 구간, 두 parameterization의 근거와 세 검토 플래그를 보존한다. 범위 밖 온도는 외삽하지 않는다. 지수가 부동소수점 양의 범위를 벗어나면 0·무한대·비가역 트랩으로 자르지 않고 `out_of_scope`를 반환한다. 결과의 `independent_rate_contract_fields`는 population과 초기 점유율을 추가해 `HydrogenKineticTrap` JSON에 합성할 수 있다.

`effective_rate_ratio_energy_J_mol=-RT ln(λ/κ)`는 두 입력 속도의 비를 확인하는 진단값이다. 서로 다른 prefactor·엔트로피를 포함하므로 이를 측정된 결합에너지로 이름 바꾸지 않는다. 공급자는 knot에서 식을 평가하고 수송기는 이력 knot 사이를 선형 보간한다. 비선형 온도 ramp에서 식을 연속 재평가한 것과 같지 않으므로 사용자가 knot 세분화 민감도를 확인해야 한다. 다중 경로 선택, 역반응 상세평형 강제, 모수 적합·불확실성·실험 자격은 별도 과제다.

`LatticeBoundary`는 경계 ID·근거와 다음 네 종류 중 하나를 갖는다.

| 종류 | 입력 | 의미 |
|---|---|---|
| `prescribed_lattice_concentration` | 시간별 격자 H 농도 | 계면 안쪽 농도를 외부 공급자가 지정 |
| `linear_surface_transfer` | 시간별 평형 격자 H 농도와 양의 전달계수(m/s) | 표면저항과 반 셀 확산저항을 직렬 결합 |
| `dissociative_surface_reaction` | 시간별 흡수·방출 한계 atom-molar flux | 축약 가역 표면반응과 반 셀 확산저항을 직렬 결합 |
| `no_flux` | 농도 이력 없음 | 표면을 통한 유출입 0 |

선형 표면전달의 유효 속도는 `1/(1/k_surface + d_half/D)`다. `k_surface`와 평형농도는 각각 근거를 갖춘 외부 입력이며, 압력·전류·진공 조건에서 자동 생성하지 않는다. 이는 비선형 흡착·해리·재결합 반응이나 검출기 응답을 대신하지 않는다. 닫힌 끝과 탈착 sink는 서로 다른 경계다. 시편 표면의 총 농도와 이동 가능한 격자 농도도 구분한다.

### 기체 구동 축약 표면반응 공급자

`transport.hydrogen_dissociative_surface_rates`는 다음 한 상태 축약식을 사용한다.

```text
J_in = J_abs(T,f) (1-theta_surface) - J_des(T) theta_surface
J_abs = A_abs exp[-E_abs/(RT)] sqrt(f_H2/f_ref)
J_des = A_des exp[-E_des/(RT)]
```

`theta_surface`는 흡착 피복률이 아니라 수송 모델의 바로 안쪽 격자 표면 점유율이다. `J_abs`는 빈 격자 표면에서의 안쪽 한계 flux, `J_des`는 단위 점유율에서의 바깥쪽 한계 flux이며 둘 다 mol-H-atoms/(m²·s)다. 따라서 `J_abs/(J_abs+J_des)`는 이 축약식의 zero-net 표면 점유율일 뿐 bulk 용해도·측정 평형농도·Langmuir 피복률이 아니다. 계산기는 이 식을 인접 반 셀 Fick 저항과 대수적으로 결합하므로 표면 flux와 셀 재고가 같은 보존식에 들어간다.

기체 입력은 사용자가 공급한 H₂ fugacity이거나, 별도 `ideal_gas_approximation_reviewed=True`를 선언한 H₂ partial pressure다. total/gauge pressure, 혼합가스 압력이나 CoolProp 결과를 자동으로 fugacity라고 바꾸지 않는다. Fugacity의 물리량 정의는 [IUPAC Gold Book](https://doi.org/10.1351/goldbook.F02543)을 서지 참조하고 문장·표·계수는 복제하지 않았다. 온도·기체 구동량 지원 범위를 벗어나거나 양의 capacity가 부동소수점으로 표현되지 않으면 외삽·clipping 없이 중지한다. `boundary_contract_fields`는 ID를 붙여 평판 또는 원통의 `LatticeBoundary`에 직접 합성할 수 있다.

공급자는 선언한 knot에서 Arrhenius와 fugacity 식을 평가하고 수송기는 생성된 두 capacity 이력을 knot 사이에서 선형 보간한다. 비선형 온도·fugacity 이력에서 연속적으로 원식을 다시 평가한 것과 같지 않으므로 knot 세분화 민감도를 확인한다.

## 수치 해법과 보존 검사

평판을 동일 폭의 셀로 나누고 셀 평균을 계산한다. 내부 flux에는 인접 셀 중심 사이 거리를, 지정 표면에는 반 셀 거리를 사용한다. 각 내부 flux가 인접 두 셀에서 반대 부호로 들어가므로 전 영역 합에서 상쇄된다.

시간 적분은 backward Euler다. 한 단계에서 `a=Δt κ`, `b=Δt λ`라 두면 트랩의 새 상태를 다음처럼 소거한다.

```text
v_new = (v_old + a u_new) / [1 + b + (a-b)u_new]
```

이 관계를 전체 수소 보존식에 넣고 격자 점유율에 대해 Newton 반복한다. 도함수를 직접 계산하고 [SciPy `solve_banded`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.solve_banded.html)로 삼중대각 계를 푼다. 갱신은 0~1의 영역 안에서 line search를 수행한다. 계산 후 음의 농도를 잘라 질량을 바꾸는 보정은 하지 않는다.

초기 단계는 확산·포획/탈리의 시작 시간척도도 고려한다. 먼 출력 시각만으로 초기의 빠른 반응을 지나치지 않으며 시간 좌표의 해상도는 현재 단계의 시각에서 평가한다. 한 큰 단계와 두 반 단계의 점유율·경계 통과량 차이를 비교해 이후 시간을 조정한다. 통과량을 별도로 비교하는 이유는 정상 농도 분포에서도 D나 경계 이력이 변하면 통과 유량 적분에 오차가 생길 수 있기 때문이다. 승인한 두 반 단계의 상태와 같은 단계 flux를 누적한다. 외삽으로 두 해를 합쳐 점유율·질량 보존을 잃는 방식은 사용하지 않는다.

왼쪽과 오른쪽 출력 flux는 **각 표면에서 재료 안쪽으로 들어갈 때 양수**다. 따라서 전체 면적당 재고와 누적 교환의 관계는 다음과 같다.

```text
inventory(t) = ∫[C_L + Σ C_p] dx
inventory(t)-inventory(0) = left_exchange(t) + right_exchange(t)
```

출력의 질량 잔차를 사용자가 지정한 수치 예산과 대조한다. 상대 잔차의 척도는 초기 재고, 출력 knot의 최대 재고, 최종 양쪽 누적 교환 절댓값 합 중 최대값이다. 순 통과량이 재고보다 매우 큰 문제에서는 mol/m² 단위의 절대 잔차도 함께 검토한다. 이 잔차가 작다는 사실은 공간·시간 해상도나 물리 파라미터의 정확성을 증명하지 않는다. `relative_tolerance`, `absolute_occupancy_tolerance`는 국소 step-doubling 제어다. 전 시간구간 오차 상한으로 표시하지 않는다. 절대 허용오차의 단위는 농도가 아닌 점유율이다.

`cell_count`, `maximum_step_s`를 각각 줄이거나 늘려 관심 출력의 수렴을 확인한다. 기본적으로 모든 knot의 평균·재고·경계 flux와 최종 셀 분포를 돌려준다. `store_profiles=True`이면 모든 knot의 셀 분포도 보존하며 명시한 출력 크기 상한을 적용한다. 내부 시간 예산·수치 범위·점유율 지원 범위를 넘으면 `out_of_scope`를 돌려주고 완료된 전체 궤적으로 표시하지 않는다.

## Python 사용과 재현

```powershell
.\.venv\Scripts\python.exe examples/hydrogen_slab.py
.\.venv\Scripts\python.exe examples/hydrogen_independent_trap_rates.py
.\.venv\Scripts\python.exe examples/hydrogen_thermal_rates.py
.\.venv\Scripts\python.exe examples/hydrogen_thermal_rate_fit.py
.\.venv\Scripts\python.exe examples/hydrogen_detector_observation.py
.\.venv\Scripts\python.exe examples/hydrogen_surface_reaction.py
.\.venv\Scripts\python.exe examples/hydrogen_slab_flow_fit.py
.\.venv\Scripts\python.exe scripts/validate_hydrogen_slab.py
.\.venv\Scripts\python.exe scripts/validate_hydrogen_independent_rates.py
.\.venv\Scripts\python.exe scripts/validate_hydrogen_thermal_rates.py
.\.venv\Scripts\python.exe scripts/validate_hydrogen_thermal_rate_fit.py
.\.venv\Scripts\python.exe scripts/validate_hydrogen_detector_observation.py
.\.venv\Scripts\python.exe scripts/validate_hydrogen_surface_reaction.py
.\.venv\Scripts\python.exe scripts/validate_hydrogen_inverse.py
.\.venv\Scripts\python.exe examples/hydrogen_cylinder.py
.\.venv\Scripts\python.exe scripts/validate_hydrogen_cylinder.py
.\.venv\Scripts\python.exe scripts/validate_hydrogen_surface_transfer.py
.\.venv\Scripts\python.exe scripts/verify.py
```

`examples/hydrogen_slab.py`와 `examples/hydrogen_cylinder.py`는 외부 관측이 없는 합성 입력을 `ModelRegistry.run_json`으로 실행한다. Python에서는 `HydrogenSlab` 또는 `HydrogenFiniteCylinder`의 `model_validate_json`으로 JSON 배열과 중첩 근거를 엄격하게 읽거나, 실제 Pydantic 객체·tuple 근거를 갖춘 Python 계약을 직접 제공한다. `AssessmentResult`는 입력 스냅샷·단위·버전·근거·시간 원점 ID를 보존한다. 예제 계수를 재료 기본값으로 사용하지 않는다.

`validation/hydrogen_slab_math.json`은 소스 해시와 독립 해석식 대비 오차를 기록한다. 시간 최대 단계 0.04→0.02→0.01초에서 닫힌 반응의 점유율 오차는 약 1.95~1.98배씩 줄었다. 12→24셀의 Fourier 셀 평균 비교는 오차가 약 3.78배 줄었으며 고정 시간 간격의 오차도 포함한다. 이는 모든 문제에서의 수렴 차수 보증이 아니다. 별도 검사는 두 트랩·변온 이력의 독립 DOP853 ODE, 빠른 속도의 Oriani 한계, 먼 출력 시각과 빠른 초기 반응의 공존, 경계 반사, 비균일 폐쇄 재료의 질량 보존, 일정 분포의 가변 유량 적분, 범위·신원·예산 실패를 확인한다.

`validation/hydrogen_surface_transfer_math.json`은 평판 flux와 원통 곡면 총 flow가 위 직렬저항 항등식과 일치하고 누적 표면교환이 재고 변화와 맞는지 검사한다. 이 검사는 입력한 표면계수의 산술·보존 검증이며 실제 재료의 흡수·방출 계수 보정이 아니다.

`validation/hydrogen_surface_reaction_math.json`은 Arrhenius·제곱근 fugacity capacity를 독립식과 대조하고 같은 boundary 조각을 평판과 유한 원통에 넣는다. 초기 평판 flux, 원통 곡면적을 곱한 총 flow와 두 계산의 atom-mol 질량잔차를 확인한다. 이는 합성 산술·형상 조합·보존 검사이며 실제 표면 상태, fugacity 공급자나 실험 계수를 보정하지 않는다.

`validation/hydrogen_independent_rates_math.json`은 결합에너지를 의도적으로 매우 크게 두고 온도를 300→900 K로 바꾼 닫힌 평판·유한 원통에서, 독립적으로 입력한 동일 포획/방출 빈도가 해석적 균일 반응식과 일치하는지 확인한다. 따라서 독립 모드가 결합에너지·온도로 재계산되지 않는다는 계약과 질량보존을 검사한다. 이 합성 검사는 실제 재료 속도, prefactor, 엔트로피 또는 비가역성의 보정이 아니다.

`validation/hydrogen_thermal_rates_math.json`은 Arrhenius와 전이상태 식을 별도 계산과 대조하고, 생성한 JSON 속도 조각을 평판 수송에 연결해 piecewise-linear 속도 이력의 독립 DOP853 반응해와 비교한다. 파라미터는 모두 합성이며 실제 트랩 기구, 에너지 장벽, 엔트로피 또는 실험 곡선의 검증이 아니다.

`transport.hydrogen_thermal_rate_fit`은 검토된 양의 유효 속도 관측만 받아 calibration 행에서 로그 속도–역온도 관계를 가중 적합한다. 관측·source group·partition·trap/material/lattice/energy-reference ID를 보존하고 holdout은 적합에 쓰지 않으며 calibration 온도 범위 밖이면 검증으로 표시하지 않는다. 전이상태식은 rate만으로 transmission coefficient와 entropy를 분리할 수 없으므로 coefficient를 고정 입력으로 요구한다. `validation/hydrogen_thermal_rate_fit_math.json`은 독립 가중 직선 폐형식, holdout 제외와 기존 thermal-rate 공급자 조합을 검사한다. 보고 공분산은 선택한 단일 경로와 입력 log-rate 불확실성 또는 잔차에 조건부이며 실제 TDS/투과 역식별, model-form·source-group·transport 불확실성이나 독립 실험 검증이 아니다.

`transport.hydrogen_detector_observation`은 표면에서 바깥으로 나가는 signed 수소 원자 mol/s를 입력으로 받는다. 전기화학 모드는 전자수·전류효율·부호와 정확 SI Faraday 상수로 이상 전류를 만들고, TDS 모드는 검토된 시편 질량과 수소 원자 몰질량으로 질량기준 ppm/s를 만든다. 평판 어댑터는 검토된 실제 면적이 있어야 inward flux를 outward flow로 바꾸며, 원통 어댑터는 계산기가 이미 적분한 곡면/끝단 flow를 사용한다. `validation/hydrogen_detector_observation_math.json`은 두 항등식과 평판 어댑터를 독립 산술과 대조해 절대 오차 0을 기록한다. 이는 실제 detector calibration, 지연·배관·pumping·재결합·흡착·잡음, 역문제 또는 실험 검증이 아니다.

## 한 모수 평판 수송 역추정

`transport.hydrogen_slab_flow_multiplier_fit`은 이미 검토·보정된 평판 표면의 signed outward 수소 원자 mol/s에 대해 하나의 완전한 양수 파라미터 이력에 공통 배수를 적합한다. 선택할 수 있는 대상은 격자 확산계수, 한 트랩의 capture 또는 independent release 빈도, 한 표면의 선형 전달계수, 또는 축약 표면반응의 흡수·방출 capacity다. 모든 다른 초기 분포, 형상, trap, 경계, 면적과 검출기 변환은 고정하고 독립적으로 검토해야 한다. 관측 knot는 정방향 `HydrogenSlab`의 elapsed-time knot와 정확히 같아야 하며 임의 보간이나 명목 가열률로 시계를 만들지 않는다.

호출자는 고유 observation ID, source group과 사전 선언한 `calibration`/`holdout` partition을 제공한다. 경계 있는 `scipy.optimize.least_squares`는 log multiplier 한 개와 calibration 행만 사용한다. holdout 값은 목적함수, 초기값, bound 또는 고정 입력 선택에 쓰지 않고 적합 뒤 잔차만 계산한다. 결과는 fitted multiplier와 이력, 재사용 가능한 fitted slab 계약과 digest, 분할별 RMSE·정규화 잔차, 활성 bound, 정방향 질량잔차, 국소 calibration Jacobian과 선택 모델에 조건부인 표준불확실성을 보존한다. 민감도가 선언 하한보다 작거나 정방향 계산이 지원 범위를 벗어나면 유효 적합으로 반환하지 않는다.

`validation/hydrogen_slab_flow_inverse_math.json`은 확산계수 배수 2.0으로 같은 정방향 모델에서 만든 합성 flow를 복원하고 fitted 계약을 재실행한다. holdout 값만 바꿔도 fitted multiplier와 계약 digest가 변하지 않으며 최대 정방향 상대 질량잔차는 약 `5.1e-16`이다. 이는 코드 경로·parameter recovery·holdout 제외 검사다. 한 개 multiplier라도 고정 입력과 강하게 보상될 수 있으며, 국소 Jacobian/공분산은 전역 식별성이나 model-form·고정입력·검출기·clock·source-group 불확실성을 포함하지 않는다. 원 TDS·투과 전류·ppm 신호, 미확정 면적 또는 detector dynamics를 이 계약에 직접 넣지 않는다. 다중 모수 적합은 profile likelihood, 모수 상관과 별도 식별성 증거가 준비될 때까지 제공하지 않는다.

## 유한 원통 계약

`HydrogenFiniteCylinder`는 반지름·길이, 반경/축 셀 수와 radial-major·axial-minor 순서의 초기 셀 평균을 받는다. 원통 축은 대칭 무유량 면이며 `curved_surface_boundary`, `lower_end_boundary`, `upper_end_boundary`는 서로 다른 ID와 근거를 갖는다. 출력은 전체 원자 mol 재고, 세 표면별 안쪽 양의 mol/s와 누적 mol, 체적가중 평균, 반경·축 셀 중심 및 질량 잔차를 제공한다. 끝단을 무시하는 무한 원통 근사가 아니며 방위각 균일성은 호출자가 검토해야 한다.

공간 이산화는 환형 셀 체적, 반경 면의 `2πrΔz`, 끝단의 환형 면적과 표면 반 셀 거리를 사용한다. 국소 트랩 상태는 후진 Euler에서 제거하고 격자 농도는 sparse Newton 계로 푼다. 한 전체 단계와 두 반 단계의 상태·표면 교환 차이로 국소 시간 오차를 조절하되 반경·축 격자 오차의 상한으로 해석하지 않는다. `validation/hydrogen_finite_cylinder_math.json`은 무트랩 원통의 Bessel 급수 체적평균과 10→20 반경 셀 오차 감소, 축방향 선형 정상해, 끝단 유량 및 전체 질량보존을 기록한다.

## 실험 연결의 현재 상태

확보한 [탄화물 트랩 연구](https://pmc.ncbi.nlm.nih.gov/articles/PMC10808193/)는 열탈착에 유한 원통 시편을 사용하고 본문에서 질량 ppm을 보고한다. 이 형상을 투과막의 두께로 쓰지 않는다. 투과막 두께·노출 면적·전위 기준·충전 시작·흡수 효율은 별도 확인이 필요하다. 원시 내보내기와 본문의 선택 노출시간 표식도 원곡선까지 대조해야 한다. 출처에 명시된 정보와 아직 대응되지 않은 열을 구분해 `data/data_inventory.json`에 기록한다.

현재 결과는 독립적인 수학·소프트웨어 검증이다. 공개 본문의 지름·길이는 계약 형상에 넣을 수 있지만 실제 곡선별 시편 ID, 초기 분포, 세 표면의 fugacity·흡수/방출 capacity 또는 평형농도·전달계수, 측정 시계와 검출기 응답이 미확정이므로 아직 해당 실험을 계산기에 적합하지 않았다. 실제 곡선의 보정·시편별 보류·독립 기관 검증도 수행하지 않았다. 이력 연결과 원자료 경계는 [수치 내보내기 기록](HYDROGEN_EXPORTS_KO.md)을 따른다. 다음 확장은 실제 원신호와 수송–관측을 함께 쓰는 식별 가능한 역문제, 표면/속도 model-form·source-group 불확실성, 다중 표면상태와 실제 검출기 동특성·불확실성 모델이다.
