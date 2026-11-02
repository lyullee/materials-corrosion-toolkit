# Dang Van형 유한표본 다축 피로한계 스크리닝

## 목적과 공개 1차 근거

`matintegrity.multiaxial_dang_van_finite_screen`은 caller가 선언한 유한 shear system과 닫힌 응력 표본에서 Dang Van형 고주기 피로한계 파라미터를 계산하고, caller가 제공한 한계와 비교한다. 여기서 shear system 하나는 재료면 법선과 해당 면의 한 방향 shear 방향 쌍이다.

방법 근거는 K. Dang Van, B. Griveau, O. Message, “On a new multiaxial fatigue limit criterion: Theory and application,” *Biaxial and Multiaxial Fatigue*, EGF 3, 1989, pp. 479–496이다. [원 논문 서지 및 저자 제공 전문 링크](https://www.gruppofrattura.it/ocs/index.php/ICMFF/ICBMFF2/paper/view/11754)를 기록한다. 이 구현은 공개 원 방법의 criterion 구조를 명시적으로 이산 입력에 적용한 제한 버전이다. 원 논문 문장을 복제하지 않고 계산 계약과 경계를 새로 기술한다.

## 계산 정의

각 caller system에서 signed resolved shear history \(\tau_i=\mathbf m\cdot\boldsymbol\sigma_i\mathbf n\)을 계산한다. \(\mathbf n\)은 평면 법선, \(\mathbf m\)은 평면 내 단위 전단 방향이다. 응력 성분 순서는 `[xx, yy, zz, xy, yz, zx]`이며 shear 성분은 대칭 응력 텐서의 물리 성분이다.

시간 평균 전단응력은 공급된 시각과 선형 구간으로 구성한 이력의 trapezoidal 평균이다.

\[
\bar\tau=\frac{1}{t_{n-1}-t_0}\sum_{i=0}^{n-2}\frac{\tau_i+\tau_{i+1}}{2}(t_{i+1}-t_i)
\]

표본시각에서 \(\sigma_{H,i}=(\sigma_{xx,i}+\sigma_{yy,i}+\sigma_{zz,i})/3\)를 구하고, 각 system/sample 파라미터를 다음과 같이 계산한다.

\[
D_{j,i}=|\tau_{j,i}-\bar\tau_j|+a_{\mathrm{caller}}\,\sigma_{H,i}
\]

결과는 유한 caller system과 표본 집합의 \(\max_{j,i} D_{j,i}\)다. \(a_{\mathrm{caller}}\)와 `caller_limit_Pa`는 보정 자료와 사용 범위에 연결된 명시 입력이며, 코드가 추정하거나 생성하지 않는다.

## 입력 및 검토

- `SampledStressInvariantHistory`가 sample ID/순서, source ID/SHA, tensor basis, 유한 값과 정확한 endpoint closure를 보존한다.
- `sample_time_s`는 nested sample과 길이가 같고, 순서대로 유한하며 엄격히 증가해야 한다.
- 모든 shear system은 유일한 ID와 단위·직교 평면법선/평면내 shear 방향을 가진다.
- calibration Evidence의 source ID와 SHA는 명시한 calibration ID/값과 연결한다. 재료 condition은 history와 정확히 일치해야 한다.
- 후보 system 모집단, 시간가중 평균, 응력 부호/basis, 보정 재료범위 및 caller limit 사용목적을 별도로 검토해야 계산한다.
- 평가량은 `sample_count × shear_system_count`다. `maximum_shear_evaluations`를 넘으면 계산을 생략하고 `out_of_scope`를 반환한다.
- 산술 중 유한 입력이 비유한 traction·stress·criterion 값으로 바뀌면 `out_of_scope`를 반환한다.

## 해석과 한계

`caller_limit_not_exceeded`는 caller가 제시한 계수와 한계, 선택한 유한 system과 입력 표본에 대한 수치 비교만 뜻한다. 이 API는 연속 plane 방향 탐색을 수행하지 않고, 표본 사이 극값을 만들지 않으며, hidden cycles, residual microstress, shakedown 계산, life curve, cycle counting, 다중주기 damage accumulation, 불확실성, failure probability, 코드 acceptance 또는 material qualification을 제공하지 않는다.

후보 system 집합의 적절성은 재료의 실제 slip system이나 결정방향을 자동으로 나타내지 않는다. 비균일 시각에 대한 평균은 구간별 선형이력 가정에 의존하며, time grid refinement, 방향 집합 확장 및 독립 fatigue-limit 자료 비교는 별도로 수행해야 한다.

## 카탈로그 출처 문구 제안

`caller_finite_shear_hydrostatic_dang_van_limit_screen`: Dang Van의 published high-cycle 구조를 caller 제공 평면내 shear-system의 시간중심 전단응력과 순간 hydrostatic stress 결합으로 계산한다. 시간·system 집합·보정계수·한계는 명시 입력이며 연속 search와 재료 qualification은 포함하지 않는다.
