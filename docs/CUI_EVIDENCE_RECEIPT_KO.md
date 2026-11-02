# CUI 검사 증거 영수증 연동

`degradation.under_insulation` 모델은 검사 캠페인 보고서와 함께 `downstream_receipt`를 반환합니다. 이 작은 계약은 별도 위험성·자산관리 모듈이 CUI 캠페인의 식별자와 판정 요약을 전달받을 때 사용합니다.

## Python API

```python
from matintegrity.models.under_insulation_campaign import (
    CUIEvidenceReceipt,
    UnderInsulationCampaignAssessment,
    cui_evidence_receipt,
)
from matintegrity.models.under_insulation_campaign import under_insulation_campaign

assessment = UnderInsulationCampaignAssessment.model_validate(input_payload)
result = under_insulation_campaign(assessment)
receipt = CUIEvidenceReceipt.model_validate(result.values["downstream_receipt"])

print(result.status)
print(receipt.model_dump(mode="json"))
```

타 모듈은 `assessment_id`, `campaign_id`, 자산·위치·구역·회로 ID, 범위 설정 digest, 호출자 프로파일 revision, 캠페인 판정, 접근 구역 coverage, 관측 개수, 기준별 판정, 입력 digest 및 보고서 digest를 받을 수 있습니다. 영수증 digest는 위 값 전체에 대해 계산됩니다. 소비자는 계약 스키마를 검사하고 digest를 다시 계산하여 저장·전송 중 변경을 검출해야 합니다.

## 의미와 경계

- `accept`, `review`, `reject`는 제공된 호출자 프로파일의 기준을 적용한 결과입니다. 법규·표준 승인이나 독립적인 기술 적합성 판단을 뜻하지 않습니다.
- coverage와 관측은 입력에서 명시한 접근 영역만 나타냅니다. 접근하지 않은 면적의 부식 상태를 추정하지 않습니다.
- 영수증은 부식률, 잔여수명, POD, 위험도 또는 파손확률을 만들지 않습니다. 이런 계산을 수행하는 별도 모듈에는 해당 모듈이 요구하는 검토된 입력과 모델 가정을 전달해야 합니다.
- 영수증은 downstream 증거 요약이며 원 관측을 대체하지 않습니다. 감사·재분석을 위해 원 assessment, evidence 출처 및 digest를 함께 보관하십시오.
- 같은 입력과 보고서에 대해 영수증은 결정론적으로 생성됩니다. 입력이나 보고서가 달라지면 결합된 digest도 달라집니다.

## 커스텀 소비자 연동

독립 모듈은 공개 JSON Schema를 이용해 Python 이외 언어에서도 영수증 형식을 확인할 수 있습니다. `docs/schemas/CUIEvidenceReceipt.json`은 저장소에서 스키마 내보내기 스크립트로 생성됩니다. 위험 분석 계층은 이 영수증을 식별·추적 정보로 사용하고, 발생확률이나 결과값을 계산할 때는 별도 검증된 모델과 입력 계약을 명시적으로 호출해야 합니다.

이 인터페이스의 확장 요청은 모델 입력에 별도 위험 기능을 섞지 않고, 추가 필드의 소비자·단위·출처·digest 의미를 제안하는 방식으로 작성합니다.
