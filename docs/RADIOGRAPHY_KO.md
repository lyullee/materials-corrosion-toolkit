# 방사선투과검사 기록과 촬영기하

`inspection.radiographic_geometry_summary`는 사용자 관리 절차와 촬영 기록을 공개 Python 계약으로
보존한다. 입력은 X-ray 또는 gamma source, 장비 ID, 노출시간, source-object 거리, object-detector
거리, 초점 크기, 검출기와 원 영상 해시, 원 픽셀 크기, detector pixel pitch, IQI 기록 및 영상 지시를
포함한다. X-ray 전압과 gamma isotope는 서로 섞을 수 없다.

계산값은 pinhole 기하의 세 가지 서술량뿐이다.

- source-detector distance: `SDD = SOD + ODD`
- magnification: `M = SDD / SOD`
- focal-spot geometric unsharpness: `Ug = f × ODD / SOD`
- detector pitch가 있을 때 object-plane pitch: `p_object = p_detector / M`

거리 두 개가 없으면 값을 추정하지 않고 `needs_data`로 남긴다. 초점 크기나 pixel pitch가 없으면 해당
서술량만 `null`이다. 영상 지시는 원본 pixel bounding box, 원 영상 ID와 증거를 유지한다. 물리 위치로
옮긴 경우 위치 ID와 mapping basis를 함께 요구하며, mapping이 없는 지시는 삭제하지 않고
`unmapped_indication_ids`에 보존한다.

IQI의 종류·배치·보고 결과는 사용자가 제공한 사실로만 기록한다. 어떤 규격의 wire/hole 기준, 허용
unsharpness, 노출표, 농도·SNR·CNR 기준 또는 합격 한계도 내장하지 않는다. 따라서 계산된 magnification,
geometric unsharpness와 object-plane pitch는 총 시스템 분해능, 영상 품질 적합, 실제 결함 치수, 검출확률,
규격 합격, 잔여수명 또는 고장확률이 아니다.

직접 Python 객체 예제는 `examples/radiography.py`, JSON/dict 실행 예제는
`examples/model_inputs.json`, 공개 schema는 `docs/schemas/RadiographicExamination.json`에 있다.
독립 산술 대조는 `scripts/validate_radiography.py`가 SOD 1.0 m, ODD 0.2 m, focal spot 1 mm,
detector pitch 0.2 mm에서 M=1.2, Ug=0.2 mm, object-plane pitch=1/6 mm를 확인한다.

다음 확장은 실제 사용자 절차 export adapter, 원 영상 보존소 adapter, detector calibration 이력, 촬영
배치 내 image/physical-scope 다대다 연결이다. 자동 지시 검출·분할·크기 산정과 POD는 별도 검증 계약으로
분리한다.
