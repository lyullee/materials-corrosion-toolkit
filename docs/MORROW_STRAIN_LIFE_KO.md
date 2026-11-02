# 평균응력을 반영한 변형률-수명 모델

이 문서는 Morrow 탄성 항 조정과 SWT 최대응력-변형률 매개변수 모델의 입력·적용 경계를 설명한다.

`fatigue.morrow_strain_life`는 단축 일정진폭 조건에서 caller가 제공한 인장 양(+) 부호의 평균응력을 탄성 Basquin 항에 반영한다.

\[
\varepsilon_a = \frac{\sigma'_f-\sigma_m}{E}(2N_f)^b + \varepsilon'_f(2N_f)^c
\]

`N_f`는 cycle 수이며 `2N_f`는 reversal 수다. 유효 피로강도 계수 `sigma'_f - sigma_m`가 양수여야 한다. 모델은 로그 cycle 좌표에서 bracketed root를 풀고 caller가 선언한 calibration cycle 범위 밖으로 외삽하지 않는다. 기준식과 평균응력 보정은 재료별로 동일하게 유효하지 않을 수 있으므로 계수·부호와 재료 적용성 검토가 필수다. DOI 근거는 [Dowling의 평균응력 변형률-수명 논문](https://doi.org/10.1111/j.1460-2695.2009.01404.x)을 참고한다.

`fatigue.swt_strain_life`는 최대 법선응력과 변형률 진폭의 곱을 수명 매개변수로 사용한다.

\[
\sigma_{max}\varepsilon_a = \frac{(\sigma'_f)^2}{E}(2N_f)^{2b} + \sigma'_f\varepsilon'_f(2N_f)^{b+c}
\]

입력 최대응력은 모델이 재구성하지 않는다. 원 SWT 관계는 단축 조건을 대상으로 하며 최대응력이 양수가 아닐 때 계산하지 않는다. 계수와 재료 적용성은 호출자가 검토해야 한다. 근거 문헌은 [Smith, Watson, and Topper](https://doi.org/10.1179/1752270612Y.0000000008)를 참고한다.

예제 입력 숫자는 실행 경로 설명용 synthetic 값이며 재료 물성이나 권장 설계값이 아니다.

두 API는 변수 진폭 rainflow 집계, 응력 재구성, notch/국부 소성, 다축 임계면, 환경효과, 크리프 상호작용, 확률, 수용기준 또는 독립 실험 자격화를 수행하지 않는다. 입력계수는 해당 재료·상태·시험 범위와 연결된 호출자 자료여야 한다. synthetic API 입력은 `examples/model_inputs.json`에서 찾고, `ModelRegistry.run(model_id, payload, context)`로 실행한다.
