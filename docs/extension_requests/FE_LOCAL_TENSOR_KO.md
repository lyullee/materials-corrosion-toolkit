# 구조·FE·노치해석 국부 tensor 이력 공급 요청

## 목적

구조해석 저장소가 계산한 국부 응력·변형률 이력을 MatIntegrity 임계면 계산에 연결할 때
`matintegrity.local_tensor_history.v1` 계약을 출력한다. 이 요청서는 상대 저장소가 이미 이
기능을 제공한다는 뜻이 아니며, 특정 상용 solver 파일 형식이나 결과를 이 저장소에 포함하지 않는다.

## 필수 출력

- 자산·재료 상태·부위·하중 case·tensor source ID
- 공급자와 버전, solver와 버전, analysis ID·solution revision
- mesh ID, node/integration point/surface 구분, field-location ID, 공간 평균 방식
- 우수 좌표계 ID와 전역 좌표에서 표현한 오른손 직교 단위 기저 3개
- Cauchy stress 또는 다른 명시적 stress measure, infinitesimal strain 또는 다른 명시적 strain measure
- `[xx, yy, zz, xy, yz, zx]` 성분 순서와 strain shear가 tensor인지 engineering인지의 선언
- 고유 sample ID, 증가하는 초 단위 시계, 표본별 유효성, Pa 응력과 무차원 변형률
- 대표 주기 선언과 해석장 검토 상태
- 원 export의 SHA-256과 solver·재료·경계·mesh 설정을 묶은 configuration digest

engineering shear를 내보내는 공급자는 그 사실을 선언한다. MatIntegrity 어댑터가 비대각
strain을 2로 나눠 tensor shear로 바꾸며, normal strain은 바꾸지 않는다. 단위·measure·좌표계
또는 shear convention을 추정하지 않는다.

## 소비 측 중지 조건

`critical_plane_inputs_from_local_tensor_history`는 다음 경우 계산 입력을 만들지 않는다.

- 자산 또는 부위가 실행 context와 다름
- tensor field가 caller-qualified 상태가 아님
- 하나라도 무효·누락 표본이 있음
- Cauchy stress와 infinitesimal strain 조합이 아님
- 좌표계가 단위·직교·오른손 조건을 만족하지 않음
- 표본 ID·시계·tensor 행이 정렬되지 않음

현재 이 어댑터는 다른 stress/strain measure를 자동 변환하지 않는다. 대변형 해석, 회전된
configuration, shell/beam section output, extrapolated nodal average, submodel mapping은 별도
검토와 변환 계약이 필요하다.

## 인수 시험

1. 같은 export와 configuration은 같은 record digest를 만든다.
2. configuration revision, mesh 또는 field location이 달라지면 digest와 identity가 달라진다.
3. tensor shear와 engineering shear로 동등하게 표현한 이력이 변환 뒤 같은 계수를 만든다.
4. 전역 우수 회전으로 같은 물리 tensor와 후보 평면을 함께 변환하면 계수가 유지된다.
5. 결측 표본을 삭제하거나 보간해 조용히 닫힌 주기로 만들지 않는다.
6. mesh/time refinement와 실험 비교를 각각 별도 증거로 기록한다.

현재 저장소의 `validation/local_tensor_adapter_math.json`은 합성 정삼각형 전단 경로로 교환·
변환·계산 조합만 검사한다. 이는 solver 결과, mesh 수렴, 노치근 장, 피로수명 또는 실험
검증이 아니다. 실제 상대 저장소 연동은 고정 commit과 대표 export hash를 기록한 뒤 완료로 표시한다.
