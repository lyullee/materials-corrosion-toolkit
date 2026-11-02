# 후속 세션 확장 요청: 외부 crevice flow/CFD provider 연결

현재 consumer 계약은 `integration.external_crevice_solver_receipt`, `ExternalCreviceSolverHistory`, `ExternalCreviceVelocityProvider`다. 이 요청은 외부 저장소를 변경했다는 뜻이 아니다.

후속 provider 모듈은 다음을 구현한다.

1. 실제 provider 결과 형식 parser와 provider/solver 버전 식별
2. 원본 파일 SHA-256, run ID, mesh revision, coordinate-system/units, face ID/order와 mouth-to-tip 방향의 명시 mapping
3. 각 matintegrity geometry knot에 대응하는 cell widths/apertures, face pressure 및 face velocity 기록
4. `ExternalCreviceSolverHistory` payload 생성 및 provider 원본 row/face ID에서 normalized 배열까지의 추적표
5. provider parser fixture와 실제 최소 consumer 호출 기록. 무차원 수, pressure/flow balance 또는 solver 독립 residual을 source/digest와 함께 저장
6. mesh/time mapping 실패, face 부호 반전, geometry revision 불일치, extrapolation 요청을 거부하는 회귀 검증

실제 데이터와 solver가 제공되지 않은 상태에서는 provider adapter를 추측으로 작성하거나 consumer 연동을 완료했다고 주장하지 않는다. 데이터/코드 사용조건은 원 공급자별로 확인하고 입력 재배포권과 source publication 권리를 구분한다.
