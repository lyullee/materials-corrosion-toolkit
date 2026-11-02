# 외부 모듈 API 계약 검토

2026-11-01 로컬 어댑터 검토에서는 다음 네 계약 묶음을 확인했다. 전체 연동 시스템의 물리 모델을 검증 대상으로 확대하지 않고, 공개 입력·출력 계약과 전달 의미를 확인했다.

| 계약 묶음 | 확인 범위 |
|---|---|
| API581 고정 revision 요청 | 정확한 최소 요청 필드, 허용 enum, 임의 추가 필드 거부, 손상 값과 기간 고장확률 구분 |
| 영향평가 도구 고정 revision 요청 | 자산·시나리오·출처 일치, source term 명시, 예약 확장 필드 충돌 및 해시 변조 거부 |
| Monitoring 교환 | 평가 identity·문맥·단위·내용 해시의 보존, 변조 거부, `needs_data` 상태를 정상/경보로 바꾸지 않음 |
| Human reliability 교환 | 기회당 실패 의미, task/event/estimate 일치, recovery/timing 범위, 기간 최초고장 의미의 잘못된 대체 거부 |

API581 요청 검토 revision은 `7c8badb829f84b19c7b84d07fbc476601d9194eb`, 영향평가 요청은 `4106da0020196fcf61c8b6264ae0598e63a881a1`이다. 현재 원격 저장소 최신 상태를 다시 확인한 결과가 아니라, 프로젝트에 보존된 revision과 계약을 기준으로 한 로컬 테스트다. 상대 프로젝트 파일을 변경하거나 새 외부 계산을 실행하지 않았다.

관련 테스트 고유 28개가 최종 통과했다. 최초 실행에서는 요청서 인덱스 누락 1개가 실패했고, 실제 요청서 45개를 연결하도록 인덱스를 갱신한 뒤 관련 카탈로그 검사 3개를 재실행해 통과했다. 중복 재실행을 고유 테스트 수에 더하지 않았다.

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_api581_pinned_adapter.py tests/test_consequence_pinned_adapter.py tests/test_monitoring_exchange.py tests/test_human_reliability_exchange.py tests/test_github_integration_catalog.py
```

연동 요청서 파일과 인덱스는 `scripts/sync_extension_request_index.py`로 맞춘다. 이 도구는 수동 작성 설명을 보존하고 누락된 실제 요청서 파일을 별도 생성 목록에 추가한다. 요청서가 존재한다는 사실은 상대 프로젝트의 확장 구현이 끝났다는 의미가 아니다. PRISM 등 다른 저장소의 전체 연동 완료 여부는 각 revision 및 수신 계약 근거를 별도로 확인해야 한다.
