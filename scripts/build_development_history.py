"""Preserve the existing dated engineering ledger and explain its evidence boundaries."""

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = (ROOT / "docs/STATUS_KO.md").read_text(encoding="utf8")
    blocks = re.split(r"(?=^## \d{4}-\d{2}-\d{2})", source, flags=re.MULTILINE)
    unique = {}
    for index, block in enumerate(blocks):
        match = re.match(r"## (\d{4}-\d{2}-\d{2})", block)
        if not match:
            continue
        digest = hashlib.sha256(block.strip().encode()).hexdigest()
        if digest not in unique:
            unique[digest] = (match[1], index, block.strip())
    intro = """# 開発 이력 · 개발·검증 과정의 상세 기록

## 기록의 성격

이 문서는 저장소의 기존 날짜별 개발 기록을 보존하고, 재현 가능한 코드·스키마·시험·영수증에 연결한다. 첫 공개 Git commit는 그 이전 로컬 개발의 누적 snapshot이다. 이전 작업 전체가 독립 commit나 완전한 채팅 기록으로 공개된다는 뜻은 아니다. 날짜별 항목은 당시 기록이며 현재 상태는 README와 RELEASE_STATUS_KO.md를 먼저 확인한다.

반복된 완전히 같은 기록은 본문 SHA-256으로 한 번만 수록한다. 같은 날짜라도 내용이 다른 기록은 유지한다. 원자료와 로컬 실행 로그는 배포에서 제외하므로 공개 기록에는 코드·시험 ID·상태·해시·범위를 중심으로 남긴다. 과거의 시험 수가 현재 모델 수나 검증 완료율을 뜻하지는 않는다.

## 1. 개발 목표와 설계 원칙

재료 거동·부식·구조 건전성·제작·용접·검사 기능을 독립 Python 단위 모듈로 구성하고, 사용자가 파라미터·자료·판정 기준·외부 provider를 공급하도록 설계했다. 열역학이 필요한 부분에는 선택적 CoolProp 연동을 둔다. 후속 위험성 평가·FTA·다른 저장소 연동은 명시적인 단위·식별자·시간·결과 의미·해시를 통해 연결한다.

재료 추천값이나 규격 표를 임의로 내장하지 않고, 물리 모델·입력 계약·자료 근거·판정 규칙·결과 소비를 구분했다. 계산 성공이 인증·실험 검증·현장 예측 정확도와 같아지는 것을 막는 것이 핵심 설계 원칙이다.

## 2. 공통 코드 구조가 정해진 이유

- `Contract`: 엄격한 Pydantic 입력 타입. 누락·잘못된 자료형·경계·중첩 일관성을 검사한다.
- `RunContext`: 평가 설비·위치·시간 기준을 계산 입력과 묶는다.
- `ModelSpec`/`ModelRegistry`: 문자열 ID로 단위 API를 찾고, 목적·스키마·단위·가정·provider·버전을 드러낸다.
- `Calculation`/`AssessmentResult`: 값과 상태를 분리하고 입력·출력·근거·해시·실행 환경을 함께 전달한다.
- `Evidence` 및 source/dataset catalogs: 합성·선언·실측·공개자료·예측의 출처 의미와 권리 상태를 구분한다.
- 선택 provider: Python callable과 자료 공급자의 identity/revision·설정/관측 해시를 분리해 외부 코드의 숨은 실행을 줄인다.

## 3. 구현 범위와 분모를 정리한 과정

넓은 기술 범위의 backlog 101행, 이전 입력 감사 116개, 검토 기록의 고유 API 수, 현재 registry 757개가 서로 다른 집합임을 구분했다. 현재의 핵심 물리 묶음은 고정 63개이며 그 안의 개별 실행 감사 대상은 232개 API로 저장했다. 757개에는 자료 읽기·계약·교환·기록·workflow가 포함된다. 따라서 이를 모두 독립적인 검증 완료 물리 솔버로 부르지 않는다.

고정 목록은 `tests/data/core_physics_full_run_targets.json`, 대표 수식 시험 연결은 `core_physics_formula_cases.json`, 입력 계약·연결·극단값의 세부 매핑은 다른 `tests/data` 파일에 있다. 이후에는 진행률을 각 고정 분모에 대해 따로 보고한다.

## 4. 자료와 권리 검토의 원칙

공개 공정·부식·피로·크리프·검사 자료를 dataset catalog에서 분류하고 버전·bytes·공급자 checksum·로컬 SHA-256·출처·라이선스·제약을 기록했다. 공개 편집본의 라이선스가 기초 논문·관측자료의 권리까지 자동 허가하는 것으로 판단하지 않았다. 원자료·파생 관측·장치 신호·상용 공급자 결과는 공개 소스와 분리했다.

한 시편의 여러 시간점·공간점·노치·증강 이미지·여러 하중 단계가 독립 시편으로 집계되지 않도록 경계를 추가했다. 보정과 holdout의 시편·source group을 분리하고, 실제 측정과 재구성된 nominal 응력을 다른 근거로 기록했다. 관련 결정은 `THIRD_PARTY_NOTICES.md`와 데이터별 설명서에 남아 있다.

## 5. 검증을 나누어 수행한 과정

1. 입력 계약: 누락·자료형·단위 의미·범위·필드 관계·검토조건 차단을 검사했다.
2. 계산식: 손계산 가능한 수치·폐형식 해·독립 적분 등과 비교했다.
3. 극단값: 표현 범위·제로 한계·경계·외삽 금지·보류 상태를 확인했다.
4. 연결: 선행 결과·문맥·단위·해시 전달과 실제 물리 체인 연결을 구분했다.
5. 회귀: 수정 전후 기존 기준값과 계약을 재실행했다.
6. 전수 실행: 고정된 개별 API를 public JSON registry 경로로 실행했다.
7. 물리 검토: 수지·좌표 불변량·정수압·박육 극한·응력/온도 스케일·열역학 항등식과 적용 한계를 확인했다.
8. 공개 전 검사: 설치 wheel과 소스 배포본, 선택 의존성 부재, 제한 자료·경로·키 패턴·테스트 fixture 포함 여부를 검사했다.

이 단계들은 서로 대체되지 않는다. 수렴·피팅·실행 성공만으로 모든 물리 분기나 현장 정확도가 검증되었다고 기록하지 않는다.

## 6. 전수 검사에서 드러난 수정 유형

최근 전수 실행·정적 검사·깨끗한 설치에서 다음 유형을 수정했다. 정확한 함수와 재발 방지 사례는 관련 시험·영수증으로 추적한다.

- legacy 피로 evaluator의 dict 반환과 표준 `Calculation` adapter 불일치.
- SciPy에 없는 함수 사용, 입력·중첩 strict tuple 계약 불일치, 종단 배열 및 고체 재고 인덱스 오류.
- CoolProp 포화 상태와 단상 퓨가시티 평가 경로, provider Evidence 직렬화 및 결과 분류 enum 불일치.
- 원통 반응·스케일 적분의 wrapper/공간 요청 혼용, 성분 ID 대신 위치 배열 사용, 맨 표면 반경 경계 조건.
- 기체↔액체 내부 전달을 외부 유입으로 다시 세는 원소 수지 중복.
- 활동도 반복 예산이 부족한 합성 fixture, 보정 영역 밖 누설 예제, 불균형 접촉 예제와 평면 선택 오류.
- 평면응력 중간 제곱 overflow 및 Basquin 양수 수명의 overflow/underflow.
- 틈 형상 피드백의 공급자 인자 누락과 동적 수리 RHS의 외부 누적 변수 선언 누락.
- 온도 슬라이스의 잘못된 변수, 응축막 구간 밀도 할당 순서, 스케일 성분 인덱스 누락.
- 기본 설치에서 선택 SciPy를 먼저 불러오던 import, 소스 아카이브의 로컬 계산 로그 포함, JSON 이스케이프 경로 검사의 공백, tests/data JSON 누락.

## 7. 첫 공개 시점의 사실과 미해결 항목

대표 수학·물리 검토 63개 군, 공개 스키마 757개, 주 JSON 예제 400개 및 고정 전수 실행 232개를 구분해 기록한다. 정상 전수 계산은 230개이며 2개는 외부 근거가 필요하다. 주 예제 파일 완전성 검사 1건과 전체 정적 지적 885건은 남겨 두었다. 새 공개 문서가 추가되어도 이 과거 검사 결과를 현재의 전체 재검증으로 재명명하지 않는다.

공개 준비에서 README를 목적·입출력 중심의 63개 핵심군 표와 전체 API 표로 재구성하고, 모든 API의 별도 입력·출력·스키마·구현 설명서를 생성했다. 첫 공개 이름은 `materials-corrosion-toolkit`, Python namespace는 `matintegrity`, 버전은 `0.1.0a1`이다. 기존 엄격한 전체 품질 workflow는 유지하며 알파 배포 검사와 구분한다.

## 8. 이어서 읽을 기록

- `docs/RESEARCH_CONTINUATION_KO.md`: 환경·자료·검증·모델 추가·병렬 계산 재개 순서.
- `docs/CORE_EXECUTION_VERIFICATION_KO.md`: 232개 개별 정상 실행과 보류 사유.
- `docs/PHYSICAL_REVIEW_KO.md`: 63개 군별 물리 관계와 적용 한계.
- `docs/PREPUBLISH_CHECKS_KO.md`: 공개 전 실제 설치·패키지 경계 검사.
- `validation/`: 공개 상태·해시·매핑·환경 영수증. 원자료·로컬 상세 로그와 다르다.
- `docs/extension_requests/`: 관련 시스템에 요청할 계약·입출력·검사 조건.

## 날짜별 기존 개발 기록

아래는 기존 `STATUS_KO.md`에서 날짜가 있는 서로 다른 항목을 내용 그대로 보존한 기록이다. 동일 날짜 안의 순서는 원 기록의 순서를 따른다. 오래된 상태와 최신 상태가 다를 수 있으므로 현재 공개 상태 표를 우선한다.

"""
    # Keep source-ledger text and ordering evidence, without inventing commits.
    ordered = sorted(unique.values(), key=lambda row: (row[0], row[1]))
    text = intro + "\n\n".join(block.replace("## ", "### ", 1) for _, _, block in ordered) + "\n"
    text = text.replace("# 開発 이력", "# 개발 이력")
    (ROOT / "docs/DEVELOPMENT_HISTORY_KO.md").write_text(text, encoding="utf8")
    print(f"Preserved {len(ordered)} distinct dated entries; {len(text.encode())} bytes")


if __name__ == "__main__":
    main()
