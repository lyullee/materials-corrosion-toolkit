# 공개 배포 기록 · 0.1.0a1

2026-11-03(한국시간), Materials Corrosion Toolkit의 첫 연구용 알파 버전을 세 서비스에 공개했다.

| 서비스 | 공개 주소 |
|---|---|
| GitHub 소스 | https://github.com/lyullee/materials-corrosion-toolkit |
| 고정 릴리스 | https://github.com/lyullee/materials-corrosion-toolkit/releases/tag/v0.1.0a1 |
| PyPI | https://pypi.org/project/materials-corrosion-toolkit/0.1.0a1/ |
| Zenodo 버전 DOI | https://doi.org/10.5281/zenodo.23899598 |
| 전체 버전 DOI | https://doi.org/10.5281/zenodo.23899597 |

배포 이름은 `materials-corrosion-toolkit`, Python import와 CLI는 `matintegrity`다.

```sh
python -m pip install "materials-corrosion-toolkit[science,thermo]==0.1.0a1"
```

## 고정 소스와 실제 배포 파일

태그 `v0.1.0a1`은 커밋 `e2a8888996a3e4fc21ac6764d49d4878c08f17a8`을 가리킨다. 이후 main의 문서 수정은 이 태그와 배포 파일을 변경하지 않는다. 초기 태그 README의 핵심 계산군 표에는 머리글 뒤 빈 줄로 인한 표시 문제가 있었으며 main에서는 문서와 생성기를 수정했다. 모델 코드 변경은 없다.

GitHub Actions [실행 41546707530](https://github.com/lyullee/materials-corrosion-toolkit/actions/runs/41546707530)이 Python 3.12/Linux에서 배포용 검사를 거쳐 wheel과 sdist를 만들고 PyPI 신뢰 게시자로 공개했다. 같은 파일을 GitHub 릴리스와 Zenodo에 첨부했다. PyPI 공개 메타데이터의 SHA-256과 다운로드한 배포 파일 해시가 2/2 일치했다.

| 파일 | SHA-256 |
|---|---|
| `materials_corrosion_toolkit-0.1.0a1-py3-none-any.whl` | `ebe93c986aa73395e4cd447c52c1d81348c523947e37ca59db79c016aa09e4c8` |
| `materials_corrosion_toolkit-0.1.0a1.tar.gz` | `b8c18c228b025de99946f707fbfb052e39215d3613c59444cbf3b8911f65f54b` |
| `materials-corrosion-toolkit-0.1.0a1-source.zip` | `1f4d95584047eb53924bcbca8949cdbd839d635fc1595000daeabd11674d27f7` |

## 이번 배포에서 새로 확인한 범위

- 문서 계약: 757/757 API 상세 페이지, 문서 링크 6,914개, README 계산 예제 통과.
- 배포 선택 시험: 79/79개 통과. 이는 과거 대표 계산식 확인 시험 79개와 별개의 시험 묶음이다. 서로 합산하지 않는다.
- 공개 스키마 일치·출처 경계·권리 메타데이터 구조 검사 통과.
- wheel/sdist 빌드, Twine 메타데이터 검사, 원자료·인증정보 패턴·압축파일 구성 검사 통과.
- SciPy·CoolProp 등 선택 패키지가 없는 별도 기본 설치 환경에서 smoke 검사 통과.
- Zenodo: 소스 ZIP, wheel, sdist, SHA256SUMS.txt, publication-receipt.json 총 5개 파일 공개. ZIP 안 파일이 많아 웹 미리보기는 제한되지만 다운로드 파일은 제공된다.

이 결과는 전체 엄격한 품질 gate 통과나 독립 실험 검증 완료를 의미하지 않는다. 미해결 정적 지적·예제 포함 검사·외부 근거 의존 항목은 [공개 상태](RELEASE_STATUS_KO.md)에 남긴다. 과거 검사와 이번 배포 검사의 숫자를 합쳐 모델 검증 완료율로 만들지 않는다.

## 문서와 권리 처리

README에 63개 핵심 계산군과 757개 전체 API의 목적·주요 입출력을 노출했다. 개별 페이지에는 전체 최상위 입력·기본값·제약·출력 단위·스키마·구현·근거·예제를 연결했다. 개발 이력에는 196개 날짜별 기록과 연구 재개 절차를 포함한다.

외부 원문 파일·원 관측자료·장치 파일·로컬 로그·인증정보는 배포 대상에서 제외했다. 독립 작성 설명을 사용하고 로컬 대조 검사에서 연속 24단어 동일 구간 후보가 검출되지 않았으나 짧은 문구까지 전부 다르다는 보증이나 법적 무위험 확인은 아니다. MIT는 자체 코드에 적용되며 외부 데이터·의존성·규격의 권리는 별도다.

기계 판독 기록은 [publication_receipt.json](../validation/publication_receipt.json), 변경 이력은 [CHANGELOG](../CHANGELOG.md), 재현 절차는 [연구 재개 설명서](RESEARCH_CONTINUATION_KO.md)를 따른다.
