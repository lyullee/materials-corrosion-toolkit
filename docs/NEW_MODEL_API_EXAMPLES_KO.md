# 독립 모델 API 예제

`examples/scale_and_gasket_calibration.py`는 registry를 거치지 않고 계산 함수를 직접 호출하는 최소 예제다. 입력 계약과 계산 함수가 공개 Python API 경계이며, 다른 프로젝트는 Pydantic 모델을 만들고 결과 `Calculation`을 받아 자신의 데이터 파이프라인·대시보드·위험성 분석기로 연결할 수 있다. 입력값, 기준, 적용 검토와 근거는 호출 측에서 제공한다.

예제 안의 모든 값은 코드 사용법을 보이는 가상 입력이다. 측정 데이터, 물성치, 실제 가스켓 보정값, 연구 결론이나 설계 권고가 아니다. 실행하려면 프로젝트의 기본 과학 의존성에 더해 가스켓 적합 경로용 NumPy와 SciPy가 필요하다. 이 파일은 작성했으나 아직 실행하지 않았다.

## scale 이동 경계 모델

`PlanarScaleDiffusionReactionHistory`에 scale 시작 두께, 고체 몰부피, 순서가 맞는 시간 구간별 확산도·계면 전달계수·부호 있는 reservoir 농도차와 온도를 넣는다. 계산 함수 `planar_scale_diffusion_reaction_history()`는 구간별 끝 두께, 이동 몰 수/면적, 종료 원인을 반환한다. 용해로 두께가 0에 닿으면 그 시각에서 멈추고 이후 기판 노출 구간을 추정하지 않는다.

## gasket 누설 표면 적합

`GasketLeakageMapFit`에 접촉압력과 차압 축의 knot, 개별 flux 관측, 사전 정의한 calibration/holdout partition, 각 행의 양의 residual scale을 제공한다. `fit_gasket_leakage_map()`은 calibration 행으로 비음수 bilinear knot surface를 맞추고 holdout의 예측 잔차를 별도로 낸다. calibration 설계행렬이 모든 계수를 식별하지 못하면 map 대신 `needs_data`를 반환한다. 관측값의 단위·면적 기준·시편 독립성, 데이터 재사용권, 실제 joint로의 전이 가능성은 호출 측 책임이다.

## 공개 데이터로 바꿔 끼울 때

측정값을 넣기 전, 출처별 이용허락과 재배포 조건을 확인한다. 허용되지 않는 원자료는 저장소에 복사하지 말고 출처 메타데이터와 로컬 전용 입력으로 연결한다. 공개 가능한 데이터도 원본을 보존하고 해시, 변환 이력, 단위, 물리 시편 ID와 source group을 함께 기록한다. 이 예제의 `synthetic` Evidence를 실측 출처로 재사용하지 않는다.

이 모델들은 다른 모듈에서 직접 import해 호출하거나 registry의 model ID로 찾을 수 있다. 상위 계산에서 반복 호출할 때는 동일한 입력 계약과 각 응답의 status를 그대로 전달하고, `computed`를 규정 적합 또는 물리적 검증으로 해석하지 않는다. 등록·schema·catalog 경계는 프로젝트 generator에서 생성한다.

검증용 수치 실행, 테스트, 공급자 데이터 적합, 물리 검증과 패키지 빌드는 수행되지 않았다. 해당 단계는 별도 병렬 한강 검증 묶음에서 다룬다.
