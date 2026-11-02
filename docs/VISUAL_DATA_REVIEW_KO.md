# 공개 표면영상 자료 조사

기준일은 2026년 10월 27일이다. 저장소 메타데이터와 공식 API의 파일·라이선스 필드를 함께
확인했다. “Open” 표시는 이용허락의 대체물이 아니므로 API가 명시한 license ID를 별도로 기록했다.

## 우선 등록 자료

`visual-sheet-metal-cracks`는 Zenodo `10.5281/zenodo.18731788`의 CC BY 4.0 자료다. 676,496,455
바이트 ZIP의 제공자 MD5는 `0919900c73b690f854a345a3dc650991`이다. 각 물리 부품에 서로 다른
시점의 영상 네 장이 있고, controlled backlight 조건에서 정상/균열 image-level label을 제공한다.
네 view는 독립 시편으로 세지 않는다.

이 자료는 현장 육안검사나 용접부 검사가 아니라 제조 품질 영상이다. 숫자 scale, 균열 치수,
indication-level 위치, 검사원·절차 자격, 독립 파괴확인은 공개 설명에서 확인되지 않았다. 따라서
영상 분류·다시점 grouping과 입력 파이프라인 후보일 뿐, VT 절차·POD·규격 합격·잔여수명의 검증
자료가 아니다. 원 ZIP은 공개 source/wheel에서 제외한다.

대용량 파일은 기본 자동취득에서 제외하고 명시적 `--include-optional` 요청만 허용한다. 두 번의
Python 스트림 시도는 제공자 read timeout으로 실패했다. 수집기를 HTTP Range 재개 방식으로
보완하고 검증했으며 현재 부분 파일을 보존했다. 전체 파일과 MD5가 일치하기 전에는 acquired로
계산하지 않는다.

## 검토했지만 아직 등록하지 않은 후보

- `10.5281/zenodo.7808654`: CC BY 4.0, 282,499,470바이트의 small-weld 영상과 bounding box가
  있으나 공개 설명만으로 물리 부품 ID·OK/NOT OK 판정 근거·결함 끝점·scale이 부족하다.
- `10.5281/zenodo.20301441`: CC BY 4.0, 49개 MIG/MAG fillet-weld 단면 영상·mask다. 표면 지시
  검출 자료가 아니라 weld-region segmentation/기하 추출 자료이므로 제작 형상 검증 후보로 분리한다.
- `10.5281/zenodo.17210929`: CC BY 4.0, 논문 그림·표 재현용 4.3 MB supplement다. 일반 목적의
  독립 시편 visual-validation set으로 간주하지 않는다.
- `10.5281/zenodo.10547589`: Zenodo record는 CC BY 4.0이지만 12개 기존 산업영상 자료를 256×256
  형식으로 표준화한 compilation이다. 원 자료별 권리·변환·분할·물리 시편 ID를 먼저 재검토해야 한다.

침투검사와 자분검사에 대한 초기 저장소 검색에서는 procedure metadata, 물리 시편, 원 indication,
독립 truth와 명시적 데이터 라이선스를 함께 갖춘 자료를 확인하지 못했다. magnetic-tile 표면결함
영상이나 방법 설명 논문을 실제 magnetic-particle inspection 관측으로 바꾸지 않는다. 후속 조사는
기관 저장소·보충자료와 원 시험 보고서를 대상으로 계속한다.
