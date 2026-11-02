# 316L SECCM 국부부식 자료 계약

## 출처와 권리

자료는 Coelho 등 저자의 **Correlative SECCM–SEM/EBSD dataset for 316L pitting: CA traces,
descriptors, and imaging tables**, DOI `10.5281/zenodo.18668632`다. 고정 동반 저장소 README는 data가
CC BY 4.0이라고 선언하지만, 2026-10-29에 확인한 Zenodo record HTML의 Rights 영역은 license identifier를
보이지 않았다. 이 근거 차이는 dataset catalog에 기록했다. 원 ZIP은
공개 배포물에 넣지 않고 `data/raw/`의 제외 경로에서만 사용한다. 제공자 분석 저장소는 commit
`5ae5802d189cb100d0071b8efc557805060fcdf6`과 MIT 고지를 확인했다. notebook은 단위와 provenance
확인에만 읽었고 실행·복제하거나 그 처리 코드를 옮기지 않았다.

## 고정한 원자료

- ZIP 크기: 9,683,560바이트
- 제공자 MD5: `5650c5b968f60445e5708c1668c09da0`
- 프로젝트 SHA-256: `84134e37cfc3864d1206bc86d12a90dc42458ea4463610dc7de687a7674bc95e`
- exact manifest: raw CA, acquisition parameter, 두 descriptor, label, footprint pixel, SEM/EBSD,
  filtered EBSD, oxygen-flux table, README의 열 파일
- raw CA: `MAP_Point_1`–`MAP_Point_205`, 위치별 7,782개 표본, 시간 0–59.9915 s,
  전류 7.02e-12–3.58e-09 A, 비유한값 0개

`validation/seccm_316l_pitting_dataset.json`은 archive/member hash와 전수 수치 감사를 기록한다.
공개 검증 파일에는 raw 시계열이나 영상 값을 복제하지 않는다.

관련 표의 구조 감사에서는 acquisition parameter가 205행이며 `x/y` 값은 1–205의 순열이지만 행
순서는 map ID 순서가 아니고 retract charge 한 칸이 비어 있음을 확인했다. 원 descriptor와 제공자
정규화 descriptor는 각각 205행·map ID 1–205, label은 98개 고유 map ID의 부분집합이다. footprint는
205개 oval에 22,821개 점을 담고 oval별 72–197개 점이 있다. SEM 표는 194,512개, filtered EBSD는
194,513개의 고유 좌표 문자열 쌍을 가진다. 이 개수와 ID 조건은 구조 증거일 뿐 서로의 행이나 좌표가
정합되었다는 증거가 아니다. 좌표 단위와 registration은 계속 미확정이다.

## Python 사용

```python
from matintegrity.seccm_data import audit_seccm_archive, read_seccm_ca_trace

audit = audit_seccm_archive(local_zip)
trace = read_seccm_ca_trace(
    local_zip,
    1,
    physical_specimen_id="provider-map-physical-scope-unresolved",
    source_group_id="seccm-map-1031-c",
)
time_s = trace["time_s"]
current_A = trace["substrate_current_A"]
```

reader는 ZIP 경로 안전성, exact manifest, size gate, checksum, 두 header, 열 수, 유한값과 시간 단조성을
확인한다. 선택하지 않은 위치의 전류도 구조 감사 중 수치로 파싱한다. scaling, smoothing, baseline
correction, descriptor 계산, label 부착 또는 영상표 join은 수행하지 않는다.

선택 trace는 `adapters.seccm_chronoamperometry_summary_inputs`를 거쳐 등록된 일반 계산기
`corrosion.chronoamperometry_window_summary`에 연결할 수 있다. 이때 archive/member hash 외에 선택한
두 배열의 canonical SHA-256을 새로 만들고, 창·경계정책과 호출자 검토 부호 basis를 기록한다. 고정
map 1 전체 hold에 이 경로를 실행했지만 provider descriptor와 같은 정의라는 주장은 하지 않는다.
재현 결과는 `validation/chronoamperometry_window_summary_math.json`에 있다.

## 해석 경계와 다음 자격화

205개 map point는 한 mapping campaign의 반복 위치이며 서로 독립인 물리 시편으로 세지 않는다.
현재 확인된 것은 member 역할뿐이다. parameter row와 map point, footprint pixel과 전류, SEM/EBSD
좌표와 SECCM 위치, label과 관측의 정합은 아직 검토되지 않았다. 따라서 다음 정보를 원 계측 metadata와
독립 근거로 확인해야 한다.

1. 물리 시편 수, map geometry와 각 위치의 독립성
2. acquisition parameter의 위치별 대응 규칙
3. footprint·SEM·EBSD 좌표 단위, 원점, 방향과 registration 오차
4. label 생성 정의와 독립 reference truth 여부
5. 별도 물리 시편을 이용한 calibration/holdout 설계

그 전에는 descriptor 재현, 부식 class truth, pit 크기, 분류 성능, POD, 잔여수명, 합격 또는 고장확률로
승격하지 않는다.
