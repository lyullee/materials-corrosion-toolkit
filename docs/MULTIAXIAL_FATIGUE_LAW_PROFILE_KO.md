# 다축 피로 caller-law 적용범위 profile

`MultiaxialFatigueLawProfile`와 `bind_caller_multiaxial_material_law()`는 기존 memoryless 및 stateful multiaxial damage callback이 실제 입력 적용범위를 벗어나 사용할 때 이를 차단하는 caller 공급 contract다. 이 API는 피로 법칙 또는 보정값을 제공하지 않는다.

## 고정되는 계보와 범위

profile은 law/provider/revision, callback configuration SHA, calibration ID/SHA, material condition ID, stress/strain 측정 정의와 SI 단위, tensor 성분 순서 `[xx, yy, zz, xy, yz, zx]`, tensor/engineering shear convention을 담는다. 각 성분별 stress/strain 하한·상한, cycle duration, block cycle 개수, allocated repetition 수, 허용 time reconstruction 목록을 caller가 선언한다. calibration digest는 동일 provider ID/SHA의 Evidence에 연결한다. 사용권은 별도 Evidence와 license/rights 식별자로 보존하며, tensor 의미·재료 적용성·calibration transfer·계산 사용 review도 각각 필요하다.

binding 때 요청 metadata와 전체 cycle population을 검사한다. callback 실행 중에도 매 재구성 tensor 표본을 6개 stress/strain 성분별 범위와 material/shear identity에 대조한다. 범위 밖 sample이나 provider identity 변동은 예외로 거절해 damage 계산이 해당 law로 이어지지 않게 한다. 결과는 profile 전체 내용과 `law_profile_sha256`, 원 provider configuration digest를 lineage에 포함한다. 범위 밖 extrapolation은 지원하지 않는다.

```python
from matintegrity.multiaxial_damage_provider import (
    bind_caller_multiaxial_material_law,
    evaluate_caller_multiaxial_damage,
)

profiled = bind_caller_multiaxial_material_law(request, provider, law_profile)
result = evaluate_caller_multiaxial_damage(request, profiled)
```

stateful callback도 같은 binder를 사용하며 underlying provider signature/state law는 기존 API 계약을 따른다. 공개 Pydantic schema는 `docs/schemas/MultiaxialFatigueLawProfile.json`이다. 합성 wrapper 연결은 `examples/multiaxial_damage_provider.py`에서 볼 수 있다.

## 적용 제한

componentwise box는 caller의 보수적 지원영역 선언이며 상호상관, 다축 등가변수 적용범위, 온도·환경 의존성, 법칙 불확실성 또는 재료 간 transfer를 자동 처리하지 않는다. duration/count 범위는 cycle population 경계이지 수명이나 합격 기준이 아니다. provider callback은 전적으로 caller 재료법칙이며 검토 flags와 Evidence는 물리 qualification이 아니다. 공개 profile/계수의 재배포 권리는 별도로 검토한다.
