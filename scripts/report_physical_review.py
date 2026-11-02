"""Record representative physical identities, assumptions and their limits."""

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Authored review statements, not extracts from a source document or standard.
# Criterion and limitation are kept separate: an algebraic success never grants
# transfer to another material, geometry or loading regime.
REVIEW = """
1|측정 질량=밀도×면적×평균 손실두께; 시간으로 나누어 속도 계산|세척 보정·밀도·노출 면적 근거 필요; 국부 최대 침식 깊이가 아님
2|전자수·Faraday 상수·전하량으로 금속 몰수 및 체적 환산|금속 용해 부분전류와 전류효율 필요; 부호 없는 총 전류를 용해 전류로 대체할 수 없음
3|decade 단위 Tafel 기울기와 면적 정규화 저항으로 전류밀도 산출|평형 부근 선형화와 Tafel 구간 성립 필요; 확산 지배·비정상 표면에 일반화하지 않음
4|각 전극 과전압과 전해질 전압강하의 합이 기전력과 일치|선형 편극 범위 밖에는 비선형 분극곡선·전해질 형상 모델 필요
5|면적 가중 양극·음극 전류의 합이 외부 순전류와 일치|영 순전류라도 금속 용해 부분전류는 존재; 정적 근이 동적 안정성을 보장하지 않음
6|전위 변화는 반응지수 로그·절대온도·전자수에 의존|활동도·표준상태·기준전극·반응 방향을 맞춰야 하며 농도만으로 전위를 확정할 수 없음
7|사용자가 선언한 시간 법칙 또는 속도 적분으로 손실 계산|적합 구간·초기 두께·균일 손실 가정 밖 수명 외삽은 미검증
8|자체 작성 로그 선형 자료의 계수와 보류값 복원 확인|실제 대기환경의 현장 예측 정확도·장기 재료 전이는 이 시험으로 확인하지 않음
9|선언된 부식·침식·상호작용 속도의 시간별 합산|상호작용 계수는 별도 실험 근거가 필요하며 합산이 결합 메커니즘의 증명은 아님
10|주어진 균열 속도를 시간에 따라 적분하고 길이 단위 보존|응력·환경에서 균열 속도 자체를 독립 예측하거나 임계 파괴를 결정하는 검증은 아님
11|질량작용 반응식·성분 보존·전하 평형의 동시 만족|누락 성분·부정확한 평형상수·허용하지 않은 고체상을 수치 수렴으로 보완할 수 없음
12|활동도 계수·농도와 몰랄 표준상태 변환·이온강도 일관성|각 Davies·Debye–Huckel·SIT·B-dot·외부 공급자의 온도·용매·농도 범위를 구분해야 함
13|고체·수용액 전체 성분 보존과 포화 조건의 일치|입력 후보 상 밖의 안정상·준안정상·실제 석출 시간은 확인하지 않음
14|반응 화학양론에 따른 성분 수지와 가역 반응의 해석해|반응속도 상수·메커니즘의 실험 적합성과 강성 반응망 전체는 별도
15|고체 생성·용해 몰수와 몰체적·두께·가용 재고의 일치|속도법칙 및 핵생성 매개변수의 재료·표면별 보정 필요
16|피복률은 0~1 내에서 부착·제거 수지와 지수 한계해 만족|표면 균질화 가정이며 실제 막 균열·국부 피복 모양·점착 강도를 검증하지 않음
17|직렬 확산 저항과 병렬 면적 가중 공급량의 일치|층의 유효 확산도·균열 통로·이동경계 물성은 외부 근거 필요
18|기체·액체 경계의 동일 몰 플럭스와 Henry 평형 연결|기체측 Pa 기반 계수와 액체측 m/s 계수·농도 표준상태를 혼동하면 안 됨
19|고정 원통 확산 한계해와 가스·액체·전극·고체 재고 수지|다성분 반응·스케일·유동의 전체 결합 물리 타당성이나 현장 정확도를 이 대표해로 보장하지 않음
20|Fick 표면 플럭스의 시간 적분이 용질 재고 변화와 일치|반무한·일정 확산도·경계 농도 가정이며 응력 구배·다상 수송은 별도
21|벽 소모와 입구 공급의 수지 및 무플럭스 끝단 조건|단순 슬릿의 고정 형상·선언된 벽 반응계수 범위
22|전기적 중성 제약·전하 플럭스·양극성 확산 한계와 일치|전기중성 근사이며 전기이중층·Poisson 공간전하를 직접 푸는 모델과 구분
23|내부 시간 단계에서 성분·고체 재고와 반응 피드백의 일치|내부 커널 수학 시험을 증거 계약이 완비된 현장 결합 검증으로 세지 않음
24|압력차·점성·관성·체적 변화의 부호와 연속방정식 일치|슬릿 유동의 유효 단면·층류 가정 및 이동경계 적용 범위 검토 필요
25|수소 원자 기준 총 재고·포획 평형과 방사형 확산 한계해|수소 분자 몰수와 원자 몰수 구분; 포획 자리·표면 반응·온도 물성의 실험 보정은 별도
26|Lame 경계 견인·정수압 이동 불변량과 박육 극한 일치|폐단·개방단을 구분; 외압 좌굴·소성·용접 잔류응력을 이 탄성식으로 판정하지 않음
27|평면 회전에서 주응력·von Mises 응력 보존|주응력 출력은 면내 값; 면외 성분이 있는 3차원 응력 상태와 구분
28|자유 팽창은 응력 0, 완전 구속 가열은 압축 응력|선형 탄성·구속 조건·두께방향 평면 상태를 명시; 소성 완화는 별도
29|무마찰 나사 한 회전의 토크 일이 축력×리드와 일치|마찰·접촉 상태·조립 편차·프리로드 산포는 현장 보정 필요
30|조인트 축력·강성·가스켓 압축 반력 평형|분리 후 인장 가스켓 힘을 만들지 않으며 3차원 플랜지 휨 전체를 대체하지 않음
31|Prony 감쇠와 탄성 조인트 끝점 힘 평형|선언된 점탄성·이력 보간 범위이며 압축 크리프·손상·온도 열화는 자동 포함되지 않음
32|보정 유량식의 공간·시간 적분과 누설량 일치|보정 가스·압력·접촉·온도 구간 밖 외삽과 실제 조립체 기밀 인증은 별도
33|선언된 압력차–두께 관계의 정방향·역방향 일치|사용자 관계의 대수적 일관성 검토이며 규격 계수·실제 파열 용량의 검증은 아님
34|K는 응력과 길이 제곱근에 비례; 영 하중에서 임계 깊이를 만들지 않음|선형 탄성·해당 균열 형상·하중 모드 및 작은 소성 영역의 적합성 필요
35|무차원 평가점과 사용자 경계곡선의 보간 관계|입력 K·인성·참조응력 해와 곡선 권리·적용성은 별도; 내부점이 규격 합격을 뜻하지 않음
36|Paris 성장속도 역수의 균열 길이 적분이 수명과 일치|임계값·과부하 지연·폐쇄·미소균열·불안정 파괴 구간을 자동 포함하지 않음
37|Norton 속도는 선언 응력의 거듭제곱, 정상 변형은 속도×시간|정상 크리프만 해당하며 1·3차 크리프나 다축 파단을 독립 검증하지 않음
38|Larson–Miller 온도·로그 시간의 기준 단위 일치|시간 초와 시간(hour) 변환 및 합금별 상수·응력 관계의 근거 필요
39|크리프 시간분율과 선언된 크리프–피로 상호작용 수지|선형 누적은 사용자 가정; 실제 순서·상호작용·파단 확률은 별도
40|Basquin 응력 범위 배율에 따른 수명 변화와 Goodman 인장 평균응력 보정|범위와 진폭·사이클과 반전수를 구분; 평균응력 극한 및 재료 보정 구간 필요
41|변형률–수명 식의 탄성·소성 항과 2N 반전수 일치|Morrow·SWT의 평균응력 처리 및 보정된 재료·수명 구간 밖 전이는 미검증
42|Miner 손상은 블록 분할·순서에 불변|순서 효과가 없다는 모델 가정이지 실제 피로가 순서와 무관하다는 실험 결론이 아님
43|단축 하중의 임계면 해석해와 회전된 응력·변형률 투영 일치|유한 후보면의 최댓값이며 연속 모든 면의 전역 최적해나 다축 재료 검증과 구분
44|비례 순수전단에서 불변량 기준의 단축 환원|Sines 시간 평균 정수압과 Crossland 최대 정수압을 구분; 각 기준의 재료 상수 필요
45|비비례 추가 경화계수 0에서 기존 변형률–수명 한계로 환원|비영 추가 경화계수와 실제 비비례 경로의 재료 검증은 별도
46|J2 항복의 편차응력 의존·정수압 무소성·방사 복귀 일치|소변형·선언 경화법칙 범위이며 ratcheting·평균응력 완화 전체의 검증은 아님
47|Neuber 국부 응력×변형률과 탄성 노치 에너지 곱의 일치|스칼라 단축 안정화 추정이며 다축·기울기·반복 과도·균열 개시는 별도
48|응력–변형률 경로의 부호 있는 일 적분과 방향 반전 일치|닫힌 경로 일이 항상 비가역 소산이나 피로 손상은 아님; 에너지의 의미를 별도 선언
49|정상 열유속과 열저항·대류 경계 수지|복사에는 절대온도·방사율 필요; 대류 대표 시험을 복사 전체 검증으로 세지 않음
50|제어체적 엔탈피 변화=유입 경계열+체적 발열|에너지 폐합과 격자·시간 수렴·실제 온도 정확도는 서로 다른 확인 항목
51|Rosenthal 이동 점열원 해의 거리·열확산·속도 의존|원점 특이점·상수 물성·반무한 가정; 용융·잠열·유한 판·실제 용접 온도장은 별도
52|상태방정식의 포화 Clapeyron 관계·상 구분·절대압 단위|동일 EOS의 열역학적 자기 일관성으로 독립 실험 정확도를 증명하지 않음
53|응축 몰수×몰질량과 액막 재고·밀도×두께 일치|주어진 응축 플럭스의 재고 검토이며 전체 잠열·막 유동·열유속 결합 검증은 별도
54|선언된 기체 상태의 압력·질량 수지와 등엔트로피 일 적분|절대압 필요; 등온 누설과 등엔트로피 팽창을 동일 과정으로 취급하지 않음
55|Archard 마모 체적은 정상력×거리/경도, 평균 깊이는 체적/면적|경도 단위 Pa와 마모계수 근거 필요; 국부 마모 형상·마모 기구 전이는 별도
56|포물선 산화에서 두께 제곱 증가량과 속도 적분 일치|산화물 두께를 금속 손실 두께로 바로 바꾸지 않음; 상·박리·재료별 계수 필요
57|Arrhenius 정·역 온도 이동 배율의 곱이 1|Kelvin·활성화에너지·반응 메커니즘 유지 범위 필요; 가속 노화의 현장 전이는 별도
58|Ramberg–Osgood 총 변형률의 탄성·소성 합 및 피팅 일치|단조와 반복 곡선·공학/진 응력·변형률을 구분; 피팅 자체가 독립 검증은 아님
59|완전혼합 성분수지의 지수 희석 해와 반감기 일치|일정 압력·온도·체적, 실제 체적유량과 표준 체적유량 구분; 사각지대·흡착은 별도
60|시간별 전류 적분과 전하·양극 소모·사용 가능 재고 일치|전류효율·이용률·재료 전기화학 용량·전위 분포의 외부 근거 필요
61|절대 유체압–증기압과 수두 환산 일치|압력 여유 지표를 공동 발생률·손상률·펌프 인증값으로 바꾸지 않음
62|명시한 음속·기하에서 왕복 전파 시간과 위치·깊이의 일치|굴절·이방성·음속 불확도·피크 식별·현장 결함 크기 검증은 별도
63|송신·수신 경로 합과 TFM 초점의 해석 기하 일치|유한 격자·음속·소자·파형 근거 필요; 밝은 영상점이 결함 치수·POD·합격 기준은 아님
"""


def main():
    base = json.loads((ROOT / "tests/data/core_physics_formula_cases.json").read_text(encoding="utf8"))[
        "groups"
    ]
    coverage = json.loads((ROOT / "artifacts/validation/formula_63/coverage.json").read_text(encoding="utf8"))
    verified = {r["group"]: r["status"] for r in coverage["groups"]}
    nodes = list(ET.parse(ROOT / "artifacts/validation/physical_review/invariants.xml").iter("testcase"))
    additions = {}
    for node in nodes:
        match = re.search(r"test_group(\d+)_", node.get("name", ""))
        if match:
            additions.setdefault(int(match[1]), []).append(
                dict(
                    name=node.get("name"),
                    passed=not any(node.find(t) is not None for t in ("failure", "error", "skipped")),
                )
            )
    authored = {int(line.split("|")[0]): line.split("|")[1:] for line in REVIEW.strip().splitlines()}
    assert set(authored) == set(range(1, 64))
    rows = [
        dict(
            group=g["group"],
            name=g["name"],
            physics_check=authored[g["group"]][0],
            limitation=authored[g["group"]][1],
            reference_nodes=g["nodes"],
            representative_reference_status=verified[g["group"]],
            additional_checks=additions.get(g["group"], []),
        )
        for g in base
    ]
    result = dict(
        scope="Representative mathematical/physical consistency and applicability review, not all-branch or independent experimental validation.",
        reviewed_groups=len(rows),
        representative_reference_passed_groups=sum(
            r["representative_reference_status"] == "passed" for r in rows
        ),
        reference_cases=coverage["executed_cases"],
        additional_identity_groups=len(additions),
        identity_and_balance_cases=len(nodes),
        failed_identity_cases=sum(any(n.find(t) is not None for t in ("failure", "error")) for n in nodes),
        skipped_identity_cases=sum(n.find("skipped") is not None for n in nodes),
        groups=rows,
        test_source_sha256=hashlib.sha256(
            (ROOT / "tests/test_physical_consistency_review.py").read_bytes()
        ).hexdigest(),
        sources=[
            dict(
                title="NIST CODATA physical constants",
                url="https://physics.nist.gov/cuu/Constants/index.html",
            ),
            dict(
                title="MIT fracture/fatigue Basquin and Miner exercise",
                url="https://ocw.mit.edu/courses/3-35-fracture-and-fatigue-fall-2003/aeeb332d12e15004232fbeb6b2f4324c_ps7_soln.pdf",
            ),
            dict(
                title="IAPWS saturation properties supplementary release",
                url="https://iapws.org/technical-guidance/release/Supp-sat",
            ),
            dict(
                title="CoolProp water EOS and references",
                url="https://coolprop.org/fluid_properties/fluids/Water.html",
            ),
        ],
    )
    (ROOT / "validation/physical_review_receipt.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
    )
    lines = [
        "# 63개 계산군 물리 일관성 검토",
        "",
        f"대표 물리식·적용 한계 검토: {len(rows)}/63개 군. 대표 기준값·물리 항등식 비교: {result['representative_reference_passed_groups']}/63개 군, {result['reference_cases']}개 시험.",
        f"이번 추가 스케일·불변량 검사: {len(additions)}개 군. 추가 검사와 선택한 수소/열수지 재확인: {len(nodes)}개 사례, 실패 {result['failed_identity_cases']}개, 건너뜀 {result['skipped_identity_cases']}개.",
        "",
        "63/63은 대표 문제의 물리식·차원 관계·적용 한계를 검토했다는 뜻이다. 232개 하위 API의 모든 물리 분기 또는 실험 검증을 완료했다는 뜻이 아니다. 통합 위험성 평가·FTA의 물리는 이번 범위에 포함하지 않는다.",
        "",
        "## 이번에 보강한 확인",
        "",
        "- 전하량이 같으면 Faraday 손실이 같은지, 편극저항과 전류밀도가 반비례하는지 확인했다.",
        "- 공통 압력을 더하면 폐단 원통의 응력에는 정수압만 추가되고 von Mises 응력은 유지되는지, 박육 해가 Lame 해에 접근하는지 확인했다.",
        "- 응력 좌표 회전 불변량, 가열·냉각 구속 응력의 부호, J2 정수압 하중에서 소성 변형이 생기지 않는지를 확인했다.",
        "- Basquin 하중–수명 배율, Goodman 평균응력 보정, Miner 블록 분할, Norton 응력 배율, Archard 일/경도 배율, Fick 재고 수지, Arrhenius 정·역 이동 관계를 확인했다.",
        "- 포화 압력의 수치 미분을 잠열·비체적 차로 계산한 Clapeyron 기울기와 비교했다. 이는 동일 EOS 내부의 열역학 관계 확인이며 독립 실험 검증은 아니다.",
        "- 수소 확산의 입·출구 구분과 보존, 열전도의 경계열 부호·평판/원통 에너지 수지도 재실행했다.",
        "- Faraday 추가 시험의 최초 실패는 약 1e-23 m 반올림 차이였다. 상대오차 1e-13을 명시해 수정했고 생산 계산식을 바꾸지 않았다.",
        "",
        "## 남는 물리적 한계",
        "",
        "비선형 결합 전체·비비례 다축 경로·실제 재료 계수·현장 음속·측정 오차·다상 유체 영역은 대표 수학 시험만으로 검증할 수 없다. 각 군의 아래 제한을 유지한다. 실측 두께와 자료 사용권한이 없는 전수 실행 2건도 여전히 보류다.",
        "",
        "| 번호 | 계산군 | 확인한 물리 관계 | 남는 조건·한계 |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row['group']} | {row['name']} | {row['physics_check']} | {row['limitation']} |")
    lines += [
        "",
        "## 재현 및 근거",
        "",
        "```powershell",
        "python scripts/verify_core_physics_formulas.py",
        "python -m pytest -q tests/test_physical_consistency_review.py tests/test_hydrogen_cylinder.py::test_axial_linear_steady_state_keeps_end_surfaces_distinct_and_conservative tests/test_thermal_transient.py::test_prescribed_flux_sign_and_energy_are_retained tests/test_thermal_transient.py::test_cylindrical_geometry_conserves_flux_energy --junitxml=artifacts/validation/physical_review/invariants.xml",
        "python scripts/report_physical_review.py",
        "```",
        "",
        "공개 집계: `validation/physical_review_receipt.json`. 로컬 원 영수증: `artifacts/validation/physical_review/invariants.xml` 및 `artifacts/validation/formula_63/results.xml`. 새 관측자료나 원문은 배포하지 않는다.",
        "",
    ]
    lines += [f"- [{s['title']}]({s['url']})" for s in result["sources"]]
    (ROOT / "docs/PHYSICAL_REVIEW_KO.md").write_text("\n".join(lines) + "\n", encoding="utf8")
    print(
        f"reviewed {len(rows)}/63; reference {result['reference_cases']}; extra {len(nodes)}; failures {result['failed_identity_cases']}"
    )
    return (
        1
        if result["failed_identity_cases"]
        or result["skipped_identity_cases"]
        or result["representative_reference_passed_groups"] != 63
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
