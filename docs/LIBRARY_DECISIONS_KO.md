# 기법과 라이브러리 선택

수소 트랩의 Arrhenius·전이상태 빈도와 축약 표면반응의 Arrhenius capacity는 Python `math`와 정확한 SI 상수로 직접 계산한다. 이는 유체 물성 계산이 아니므로 CoolProp을 호출하지 않는다. 표면반응 계산기는 호출자가 제공한 fugacity를 사용하고, partial pressure를 fugacity로 근사할 때는 별도 검토 플래그를 요구한다. SciPy는 수송 선형계, 별도 DOP853 조합 검증과 한 개 log-multiplier의 경계 있는 `least_squares` 역추정에 사용한다. 역추정의 국소 Jacobian·조건부 불확실성을 전역 식별성으로 해석하지 않는다. Eyring 원 논문과 IUPAC fugacity 정의는 공개 서지 근거이고 소스 코드·표·실험계수의 재배포 근거가 아니다.

검토 기준일은 2026년 10월 26일이다. 새 기법은 발표 연도만으로 채택하지 않는다. 적용 범위, 검열·결측 처리, 독립 검증, 유지보수, API와 라이선스를 함께 비교한다.

2026년 10월 27일에는 Sandia HELPR의 공식 `v2.1.0` tag와 commit
`ae12d20b6608123af41dd9d5f70db6b6547fece5`를 검토했다. HELPR는 BSD-3-Clause Python
패키지이며 수소 혼합가스 배관의 균열성장, SIF, FAD, 잔류응력과 확률 연구를 이미 제공하므로
동일 범위를 단순 재구현하지 않는다. 현재는 선택 의존성도 추가하지 않고 HELPR가 저장한
life-criteria CSV를 버전 고정 중립 계약으로 수신한다. 이는 의존성 충돌을 피하고 상대 계산의
정체성을 보존하지만 HELPR 입력 설정이나 물리모델을 검증해 주지는 않는다. 공식 출력의 다섯
열에는 자산·부위·설정 digest·리비전이 없으므로 수신자가 이를 명시해야 한다. HELPR에 포함된
규격 유래 표·곡선·계수는 MatIntegrity로 복사하지 않는다.
별도 제외 환경에서 공식 대표 입력을 실제 실행해 CSV 수신까지 확인했다. 공급자가 파괴저항에
도달하지 않아 `a/t=0.8`을 사용한 경고와 Python 폐기예정 경고를 서로 다른 코드로 보존한다.
이 통합 검사는 HELPR를 핵심 의존성으로 만들거나 그 물리모델을 독립 검증하는 근거가 아니다.

갈바닉 분극은 측정된 signed-current 보간과 전체 절점의 구간별 전류 보존을 사용한다. NumPy와 독립 구간 대수로 모든 고립근·영전류 구간을 조사하므로 단일 초기값의 비선형 root solver가 다른 근을 놓치는 문제를 피할 수 있다. smooth spline·log-absolute 보간은 부호·활성/수동 분기·추가 극값을 바꿀 수 있어 기본 경로로 채택하지 않았다. 물리적으로 검증한 함수/공간 모델은 추후 공급자로 추가하고, 임의 평활화나 새로운 라이브러리 도입을 실제 검증으로 간주하지 않는다.

수소에서는 전체 점유 관계와 SciPy의 log-expit·log-sum-exp·bracketed root로 국소 질량 평형을 풀고, 별도 평판·유한 원통 계산기는 고정-site 포획/방출 속도와 Fick 수송을 결합한다. 2026년의 [실시간 수소 이동 연구](https://doi.org/10.1038/s43246-026-01178-x)와 [포획·방출 통합 동역학 연구](https://doi.org/10.3390/jmmp10090360)를 검토 대상으로 삼았다. 농도·시간에 따라 변하는 이동을 하나의 일정 유효 D로 대체하지 않는다. fugacity 기반 표면 경계는 `J_abs(1-theta)-J_des theta`의 한 상태 축약식이며 상세 Langmuir microkinetics나 bulk solubility로 확장 해석하지 않는다. 새 동역학 연구가 있다는 이유만으로 실제 실험의 미식별 포획률·표면계수를 추정하지 않는다.

국소 평형의 수학 근거는 [Oriani의 원 연구](https://doi.org/10.1016/0001-6160(70)90078-7), 수소 재료의 관측 구분은 [1차 트랩 실험](https://doi.org/10.1038/s41467-024-45017-4)을 참조한다. 물성·결합에너지·site density는 사용자 근거가 있는 입력이며 문헌 권장 계수나 원 구현을 포함하지 않는다.

| 용도 | 선택 | 선택 이유와 범위 |
|---|---|---|
| 단위 | Pint | 차원을 검사하고 온도 오프셋을 다룬다. 압력 기준은 별도로 명시한다. |
| 관측 추세 | SciPy Theil-Sen 및 OLS 선택 | 이상치에 덜 민감한 기울기를 선택할 수 있다. 공정 변화·검사 편향을 자동 해결하지는 않는다. |
| 수명 적합 | SciPy 최적화와 검열 우도 | 미파단 관측을 버리지 않고 생존 우도에 반영한다. |
| 반복 하중 | rainflow | 기존 MIT 구현을 의존성으로 호출하고 사이클·반사이클 정보를 보존한다. |
| 물성 보간 | 선형 및 SciPy PCHIP | 성질과 데이터에 맞춰 선택한다. 외삽은 차단한다. |
| 열역학 | CoolProp 8의 SI API | 유체별 상태방정식을 재사용하고 버전·리비전을 남긴다. 압력감쇠 조합에서는 세 절대 상태의 `Z`·phase와 canonical digest를 보존하며 two-phase/미정 상태를 거절한다. |
| DICONDE | pydicom 3 선택 의존성 | 표준 container/tag와 비압축 pixel decode만 재사용하고, component 의미·보정·검출·판정은 독립 계약에서 명시한다. |
| Oxford EBSD `.cpr/.crc` | DefDAP 1.3 선택 의존성 (`ebsd` extra) | 검토된 형식 reader만 재사용한다. archive SHA·선택 member 쌍·배열 shape와 dtype를 검증하고 원 phase labels를 반환한다. grid-step 단위와 label identity는 추정하지 않으며 방향 메타데이터가 없는 파일에 대해 임시 입력본에만 identity placeholder를 적용한다. |
| 1D 과도 열전도 | NumPy 배열과 자체 삼중대각 풀이 | 보존식·경계 부호·온도 물성 범위를 프로젝트 계약에 맞게 통제한다. 다차원 PDE/FE 자격을 주장하지 않으며 외부 solver 코드를 복사하지 않는다. |
| 고급 피로·FE | pyLife 검토 후보 | Apache-2.0 라이브러리의 피로·응력·재료 적합 기능을 조사했다. 초기 핵심 의존성에는 넣지 않고 별도 공급자 비교 대상으로 둔다. |
| hit/miss POD | SciPy MLE·프로파일 우도 | score·정보행렬·완전 분리·한쪽 신뢰한계를 확인한다. 유한 표본 정확성은 합성 진단으로 별도 평가한다. |
| 변동 하중 균열 | SciPy 적응 적분·bracketed root | 입력한 비감소 형상표의 절점에서 나눠 적분하고 cycle 역산 잔차와 인성·보정 종료를 확인한다. |
| 사용자 FAD 경계 | NumPy 선형 보간과 엄격한 공급자 계약 | 규격별 곡선·cutoff·계수를 복제하지 않고 허용 근거와 판본이 있는 사용자 경계를 지원 범위 안에서만 평가한다. |
| 파괴인성 편집 workbook | openpyxl 읽기 전용·pandas 관측 표 | ZIP 안 xlsx의 두 provider partition과 source row를 보존한다. 수식·매크로를 실행하지 않는다. 온도는 workbook 충돌과 연계 논문의 °C 근거를 모두 기록하고, 단위가 없는 치수는 사용자 검토 override 전까지 SI로 추정하지 않는다. 핵심 계산기의 필수 의존성은 아니다. |
| 용접 표면 형상 | OLS·Theil–Sen·soft-L1 선택 | 쌍별 방법의 큰 표본 비용을 제한하고, 큰 자료에는 명시적 잔차 척도를 갖는 SciPy robust least squares 경로를 제공한다. |
| 충격 전이곡선 | SciPy bounded multistart·선형/soft-L1 잔차 | shelf 포함과 식별성을 따로 확인한다. robust loss의 척도는 사용자 선택이며 독립 검증이나 정확한 예측 구간을 대신하지 않는다. |
| 면적 최대 pit 깊이 | SciPy Gumbel MLE·재적합 AD 진단·파라미터 bootstrap | 확률지 직선만 적합하는 경로보다 표본 모형·추정·적합도·파라미터 불확실성을 명시한다. Gumbel 가족·공간 독립성과 동일 노출 조건이 필요하다. |
| WILLOW MATLAB v7.3 | h5py 참조 셀 순차 읽기 | 실제 파일은 HDF 기반이므로 일반 `scipy.io.loadmat` 경로를 사용하지 않는다. 파형 축과 부재한 시간축·비유한 실패를 보존한다. |
| 배관 유도초음파 구형 XLS | xlrd 2.x 읽기 전용 | XLSX 전용 openpyxl로 위장 변환하지 않고 OLE BIFF workbook의 sheet 이름·원 순서·주파수·4개 열을 직접 검사한다. xlrd는 선택적 science 의존성이며, xlwt는 테스트용 합성 fixture 작성에만 사용한다. sheet 순서가 9종이므로 위치가 아닌 이름으로 주파수를 식별한다. |
| 축 방향 감육 | NumPy 구간 적분·전체 절점 스캔·사용자 보정표 | 최소 두께 한 점으로 대체하지 않고 각 길이의 면적과 보정을 함께 계산한다. 규격 계수나 허용압력 추정 규칙은 포함하지 않는다. |
| 배관 편집 workbook | openpyxl 셀 스타일·pandas 관측 표 | 범례의 보완/추정 색상을 읽어 수치만 읽을 때 사라지는 기원을 보존한다. 수식은 실행하지 않는다. |
| 파열압 예측 비교 | Python `math`·`statistics`와 엄격한 Pydantic 계약 | 단순 압력비·로그오차는 외부 회귀 라이브러리 없이 재현하고, 모델식보다 시편·source group·분할·압력 기준·권리 검토를 먼저 강제한다. 신뢰구간이나 합격기준을 임의 생성하지 않는다. |
| 과도 열전달 자료 | pandas CSV·openpyxl 읽기 | 선택적 데이터 조사 경로에서 원 시계·열전대·처리 적합 관계를 보존한다. 핵심 열계산기의 런타임 의존성에는 넣지 않는다. |
| 대규모 비선형·공간 계산 | 교체 가능한 공급자 | 단순 경험식으로 자동 대체하지 않고 데이터·수치 검증을 갖춘 경로를 추가한다. |

파형 용접에서는 평균 전압과 평균 전류의 곱이 평균 순간 전력과 다를 수 있다. `welding.waveform_energy`는 표본별 전력의 시간 적분을 수행한다. COQTEL 입력은 HDF5의 축과 전기화학 시계 단위를 확인한 전용 로더를 사용한다. 신호 변화량은 별도 보정 없이 결함 깊이나 고장확률로 바꾸지 않는다.

참고한 공개 1차 문서:

크리프 보정은 현재 SciPy의 안정된 정규 꼬리 함수·제약 최적화·공간 hull을 사용한다. 검열을 버리고 파단점만 회귀하는 경로보다 종료 조건을 보존할 수 있다. 응력 정규화 Wilshire 계열이나 기구 기반 고급 모델은 신뢰할 수 있는 온도별 UTS·복수 온도·기구 자료가 있을 때 비교할 후속 경로다. 현재 CMSX-6 한 온도 자료에 열 효과 모수를 추가하지 않는다. 모수 불확실성·클러스터·독립 기관 검증이 확보되면 프로파일 우도·재표집·대안 모델 비교를 추가한다. 최신 외부 코드의 존재만으로 구현·자격이 끝났다고 표시하지 않는다.

- [NIST 로그정규 수명](https://www.itl.nist.gov/div898/handbook/apr/section1/apr164.htm)
- [NIST 가속 수명 우도 추정](https://www.itl.nist.gov/div898/handbook/apr/section4/apr422.htm)
- [SciPy minimize](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html)
- [SciPy log_ndtr](https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.log_ndtr.html), [erfcx](https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.erfcx.html)
- [BAM 원 자료 연구](https://doi.org/10.1016/j.dib.2025.112436), [고정 자료 v1](https://doi.org/10.5281/zenodo.14750432)

극값 진단의 `rng` API를 사용하므로 과학 확장의 SciPy 하한은 1.15다. [SciPy 1.15의 API 변경](https://docs.scipy.org/doc/scipy-1.15.0/reference/generated/scipy.stats.goodness_of_fit.html)을 확인했다. 현재 독립 설치 검증 환경은 1.18.1이며 모든 하한 버전 조합을 검증했다는 의미는 아니다. GEV·다른 꼬리 가족·공간 의존은 충분한 표본과 별도 비교를 갖춰 추가한다. 단순히 더 많은 파라미터가 있는 분포를 우선 선택하지 않는다.

- [NIST 검사 성능 신뢰한계](https://www.nist.gov/publications/estimating-instrument-performance-confidence-intervals-and-confidence-bounds)
- [POD 방법 저자의 프로파일 우도 설명](https://statistical-engineering.com/mh1823-workshop/)
- [AFRL POD4.5](https://github.com/AFRL-Material-State-Awareness/POD4.5): 고급 추정기 비교 후보. 소스 구현을 복사하거나 MIT로 재표시하지 않는다.
- [otpod 공식 문서](https://openturns.github.io/otpod/master/): 더 넓은 signal-response·대리모델 기반 POD의 비교 후보다. 현재 구현은 독립 작성한 fixed-threshold log(size)-linear normal-residual 경로로 한정하며 otpod를 의존하거나 코드를 재사용하지 않는다.

- [SciPy Theil-Sen](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.theilslopes.html)
- [SciPy 검열 데이터](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.CensoredData.html)
- [SciPy least_squares](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html)
- [NIST Gumbel 최대 분포](https://www.itl.nist.gov/div898/handbook/eda/section3/eda366g.htm)
- [SciPy 재적합 적합도](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.goodness_of_fit.html)
- [BSEE가 공개한 원 DNV 연구 보고서](https://www.bsee.gov/sites/bsee.gov/files/tap-technical-assessment-program/265ac.pdf): 면적 감소 관계를 확인했다. 계수·판정표·보고서 문장과 그림은 복제하지 않는다.
- [CoolProp 고수준 API](https://coolprop.org/coolprop/HighLevelAPI.html)
- [OriginLab Viewer](https://www.originlab.com/viewer/index.aspx): OPJU의 검토된 CSV 내보내기에만 사용한다. 이번 로컬 도구 버전은 10.4.0.25이며 Python 의존성·배포물에 포함하지 않는다. 해시·단위·기록 구조는 독립 로더로 다시 대조한다. 구체적인 절차와 한계는 `HYDROGEN_EXPORTS_KO.md`에 있다.
- [BIPM SI 정의 상수](https://www.bipm.org/en/measurement-units/): Faraday 상수는 정확한 기본전하와 Avogadro 상수의 곱으로 사용한다. 수소 관측 모듈의 전류·질량 변환은 대수식이므로 CoolProp 대상이 아니다. CoolProp을 검출기 보정이나 수소 표면 반응 공급자로 오용하지 않는다.
- [NumPy least squares](https://numpy.org/doc/stable/reference/generated/numpy.linalg.lstsq.html): 열활성화 속도 적합의 두 열 설계에 사용한다. 역온도를 중심화·척도화하고 rank와 singular value를 보존하며 공분산은 별도 독립 식으로 계산한다. 일반 비선형 최적화나 CoolProp은 이 선형화된 속도식에 불필요하다. 이 선택은 single-path 모형 적합일 뿐 실제 rate 관측의 물리적 타당성을 보증하지 않는다.
- [SciPy banded 선형계](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.solve_banded.html): 유한 평판의 독립 보존식에서 생기는 삼중대각 Newton 계에 사용한다. 점유율·경계 통과량을 포함한 시간 제어는 이 프로젝트에서 독립 작성했다. [NIST FiPy](https://pages.nist.gov/fipy/en/latest/)의 현재 유한체적 문서도 검토했으며 다차원·비균일 격자 확장의 비교 후보로 유지한다. 현재 1D 계는 기존 SciPy 의존성으로 풀며 FiPy 설치·실험 비교가 완료됐다고 표시하지 않는다. 독립 반응 비교에는 SciPy DOP853을 사용했다.
- [TWI 아크 측정](https://www.twi-global.com/technical-knowledge/job-knowledge/measurement-of-arc-welding-parameters-139)
- [pyLife 공식 문서](https://pylife.readthedocs.io/en/latest/)
- [SciPy Sobol 추정기](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.sobol_indices.html)와 [QMC 생성기/오차 설명](https://docs.scipy.org/doc/scipy/reference/stats.qmc.html)을 독립 입력 민감도의 계산 의존성으로 사용한다. 기존 SciPy 범위에서 paired-array 추정기를 호출하며 자체 코드로 단위·외부 응답 ID·실패·재현 확인과 scramble/표본 수 진단을 보존한다. [SALib](https://salib.readthedocs.io/en/latest/)의 Morris·FAST·Shapley 등 범위를 비교했으며 현재 설치·코드 복제·지원 완료 방법으로 표시하지 않는다. 의존 입력·관측 잡음·대안 추정기는 후속 과제다.
