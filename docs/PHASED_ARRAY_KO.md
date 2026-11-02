# 위상배열 초음파 acquisition 계약

`inspection.phased_array_acquisition_summary`는 사용자 관리 PAUT 절차와 encoded acquisition을
중립 계약으로 보존한다. 한 examination은 물리 범위·재료상태, specimen wave velocity와 근거,
encoder와 방향, probe element layout, probe별 wedge, focal law, 원 frame hash와 reported indication을
갖는다. pulse-echo, 별도 transmit/receive, sectorial, linear 및 full-matrix capture를 서로 구분한다.

계산은 다음 acquisition descriptor로 제한한다.

- probe physical aperture: `(N - 1) × pitch + element width`
- nominal specimen wavelength: `velocity / center frequency`
- element pitch / nominal wavelength
- 각 focal law의 transmit·receive delay span
- 원 순서의 encoder span, 고유 위치 수, 인접 중복 위치 수와 nonzero increment 범위

frame은 `frame_id`, encoder 위치, beam-law ID, 원 data SHA-256, sample 수·간격, transmit event 수,
receive channel 수, amplitude encoding과 time-zero basis를 가진다. conventional scan frame은 선언된
beam law를 참조해야 하고 FMC frame에는 precomputed law ID를 붙일 수 없다. 별도 transmit/receive
probe와 active aperture 범위도 각각 검사한다.

encoder 위치는 선언한 방향과 모순되면 거절하지만 같은 위치의 여러 law/frame은 순서와 중복을
그대로 유지한다. 파형을 정렬·평활·resample하지 않고 Snell 각도, delay, beam field 또는 focus를
재계산하지 않는다. TFM reconstruction, amplitude normalization, indication detection와 sizing도 하지
않는다.

보고 지시는 하나 이상의 원 frame ID와 증거를 유지한다. 자산 위치로 연결할 때만 physical location
ID와 mapping basis를 함께 요구한다. mapping 없는 지시는 삭제하지 않고 `needs_data`와
`unmapped_indication_ids`로 남긴다. 빈 indication은 별도의 negative-result review가 필요하다.

이 모델의 aperture·wavelength·pitch ratio·delay span·encoder 간격은 probe field, wedge/focal-law
적합성, image quality, 결함 크기, 규격 합격, POD, 잔여수명 또는 고장확률이 아니다. 사용자 허가를
받은 규격 provider가 없는 한 focal-law/coverage/acceptance threshold를 넣지 않는다.

직접 Python 예제는 `examples/phased_array.py`, JSON 예제는 `examples/model_inputs.json`, 공개
schema는 `docs/schemas/PhasedArrayExamination.json`에 있다. `scripts/validate_phased_array.py`는
독립 작성한 4-element probe와 세 encoder 위치에서 aperture, wavelength, delay span과 불균일 scan
increment를 대조한다.

## ML-NDT local-clone reader

`ml_ndt_data.list_ml_ndt_batches(root, repository_revision=...)`는 로컬 clone의 `data/training`과
`data/validation`에서 UUID별 `.bins`, `.meta`, `.jsons`, `.labels` 네 파일이 모두 있는지 조사한다.
기본값은 고정 commit `6fb6aee456e64add656d1beb4e414639b13df278`만 허용한다. Git commit 확인은
호출자가 수행하며 반환 계약에는 `caller_verified_local_clone`으로 그 근거 수준을 명시한다.

`read_ml_ndt_batch`는 UInt16 형상에 맞는 바이너리 바이트 수, 연결 JSON object 수, label 행 수,
파일별 SHA-256과 원 순서를 검사한다. JSON flaw 값은 제공자 문자열을 그대로 보존하고 size·equivalent
size·augmentation factor만 단위 미확정 숫자로 함께 노출한다. label과 JSON equivalent size가 다르면
수정하지 않고 mismatch로 기록한다. pickle이나 제공자 코드는 실행하지 않는다.

`.meta`에는 byte order가 없다. 따라서 `read_ml_ndt_image`는 `little` 또는 `big`을 호출자가 명시해야
한 영상만 C-order로 복사하며, 읽기 직전에 batch binary digest를 다시 확인한다. 이 reader는 공개 원자료를
패키지에 포함하지 않고 local clone을 참조한다. provider training/validation 분할, 201 batch와 20,100개
augmented 영상은 한 물리 pipe·세 원 crack의 독립 검증 자료로 승격하지 않는다. 공개 schema는
`MlNdtBatchAudit`, `MlNdtImageLabel`, `MlNdtFlawMetadata`다.
