# Thermal-spray 공개자료 검토

기준일은 2026년 10월 28일이다. 이 문서는 후속 독립 검증 후보를 기록하며, 후보를 이미 확보했거나
자격화된 자료로 표시하지 않는다.

## 우선 후보

Zenodo record `10.5281/zenodo.14034890`, *Microstructure and mechanical performance of cold spray Cr
coatings*를 우선 후보로 검토했다. Zenodo API의 고정 record metadata는 open access와 CC BY 4.0을
선언한다. 제공자는 `Data.zip` 하나를 게시했고 크기는 약 1.9 GB, provider MD5는
`f24f61ad9d6fb33d301c2102b31b934b`다. 설명상 archive에는 두 coating의 porosity 분석 SEM image,
interface roughness/thickness variation image, hardness, residual-stress XRD, in-situ DIC와 분석 notebook이
함께 있다.

## 현재 판단

자료 주제는 `fabrication.thermal_spray_cross_section_summary`와
`fabrication.thermal_spray_thickness_uncertainty`의 후속 검증에 적합할 가능성이 높다. 그러나 현재는
archive 내부 member manifest, image calibration, 실제 physical specimen/field 반복구조, 두 coating의
calibration/holdout 분할, pointwise reference thickness 및 uncertainty를 확인하지 않았다. 따라서 이
record를 모델의 검증 완료 근거나 내장 parameter로 사용하지 않는다.

1. 누리온 또는 별도 저장공간에서 provider URL로 archive를 한 번만 취득한다.
2. provider MD5와 프로젝트 SHA-256을 모두 검증하고, extraction 전에 path·중복·암호화·총 비압축
   크기를 감사한다.
3. 원 image와 upstream notebook을 실행하거나 공개 배포물에 포함하지 않는다.
4. scale calibration, field/specimen identity와 원 측정의 독립성을 확인한 뒤, 자체 reader가 만든
   최소한의 aggregate audit만 공개한다.
5. 같은 field에서 산출한 porosity와 thickness를 독립 holdout으로 중복 계수하지 않는다.

권리 선언은 dataset reuse의 근거이지 관련 논문 문장·그림·upstream code를 복제할 권한의 대체물이
아니다. 구현과 문서는 독립적으로 작성하고 출처·라이선스·제외 범위를 별도 장부에 유지한다.
