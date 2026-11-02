# 수소 피로·균열 provider 교환

이 경로는 권한 있는 외부 시험·해석 공급자의 결과를 재현 가능한 입력 범위와 qualification evidence에 결속한다. 라이브러리가 수소 환경의 성장률, 인성 저하, 균열 진전, 수명 또는 합격 기준을 새로 계산하는 경로가 아니다.

## 수소 피로

`degradation.hydrogen_fatigue_provider_evidence`는 재료 상태, 환경, 온도, 하중·주파수·응력비 조건과 공급자 결과를 고정한다. 수소 조건은 absolute partial pressure와 fugacity 중 하나의 명시적 basis를 사용하며 둘을 자동 변환하지 않는다. 지원영역 사이를 보간하거나 성장곡선을 적분해 수명을 만들지 않는다.

Calibration과 holdout은 물리 시편 및 source group 기준으로 분리한다. 제공자 결과가 적용범위 안에 있고 qualification record가 완전하다는 사실은 서비스 수명이나 현장 타당성을 보증하지 않는다.

## 수소 균열

`degradation.hydrogen_cracking_provider_evidence`는 외부 toughness와 crack-driving result의 endpoint를 K, J 또는 CTOD 중 공급자가 선언한 형태 그대로 유지한다. 서로 다른 endpoint를 내부 상관식으로 변환하거나 파괴 허용성, 성장률, 임계시간 또는 고장확률을 계산하지 않는다.

Geometry, crack, loading, material condition, environment, analysis revision과 payload digest가 일치해야 한다. Qualification/holdout evidence의 범위와 독립성도 별도로 확인한다.

## 다른 모듈과 연결

후속 API는 provider 결과의 identity와 단위를 보존한 명시적 adapter를 사용해야 한다. FTA나 위험성 평가에 연결하려면 별도의 사건 정의, 기간, conditioning, 불확실성 및 calibration evidence가 필요하다. Provider result를 곧바로 기초사건 확률로 해석하지 않는다.
