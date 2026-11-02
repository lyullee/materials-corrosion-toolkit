# 와전류검사 acquisition과 DICONDE 자료

`inspection.eddy_current_acquisition_summary`는 사용자 절차·리비전, 검사 물리 범위와 재료상태,
probe mode와 coil/channel, excitation frequency, lift-off 관리 근거, reference standard의 물리 feature,
encoded scan hash와 indication을 보존한다. reference standard가 실제 probe와 모든 scan frequency를
포함하지 않으면 거절한다.

검토된 raster increment와 origin이 모두 있을 때만 scan span을 계산한다. conductivity, relative magnetic
permeability, 온도와 근거가 모두 있고 사용자가 선형·균질 고전 skin-depth 가정을 적용 가능하다고
검토한 경우에만 `sqrt(1/(pi*f*mu*sigma))`를 descriptor로 반환한다. 이 값은 실제 probe field,
ferromagnetic hysteresis, edge/curvature, lift-off, coating, flaw orientation 또는 검출 깊이를 뜻하지 않는다.

indication은 원 scan ID, signal response 설명, 비교한 reference feature와 증거를 유지한다. 자산 위치로
연결하려면 physical location과 mapping basis를 함께 요구한다. indication이 없으면 별도 negative-result
review가 필요하다. 신호 회전·혼합·필터·평활·threshold, lift-off 보상, 결함 검출·치수·합격·POD·수명은
수행하지 않는다.

## DICONDE reader

`eddy_current_data.read_eddy_current_diconde`는 pydicom을 선택 의존성으로 사용한다. Eddy Current Image
Storage SOP class와 `EC` modality, 비압축 pixel data, frame/row/column, signed/unsigned encoding,
padding value, frame별 view/rescale metadata와 파일 SHA-256을 검사한다. component order는 파일에서
추정하지 않고 호출자가 근거와 함께 제공해야 한다. 반환 배열은 저장된 정수와 padding mask이며 slope,
intercept, phase rotation 또는 threshold를 자동 적용하지 않는다. 사람 관련 DICOM field는 공개 계약으로
내보내지 않는다.

DICOM physical unit code 3의 cm delta와 `PixelSpacing`의 mm 값을 각각 SI로 변환해 일치 여부를
기록한다. 둘이 다르면 한쪽을 선택하지 않는다. 공개 계약은 `EddyCurrentDicondeRecord`,
`EddyCurrentProbe`, `EddyCurrentReferenceFeature`, `EddyCurrentReferenceStandard`,
`EncodedEddyCurrentScan`, `EddyCurrentIndication`, `EddyCurrentExamination`이다.

## 확보한 공개자료

BAM의 Zenodo `10.5281/zenodo.14186333`은 CC BY 4.0이다. 제공자 MD5를 확인한 simulation archive
3,469바이트와 laboratory archive 166,091바이트를 확보했다. Simulation은 상용 Faraday BEM 출력 CSV
12개이고, laboratory 자료는 DICONDE 10개다. CSV는 7행 3개, 13행 3개, 15행 6개이며 위치 mm와 real/
imaginary voltage V를 명시한다. 네 번째 `total rel. acc` header는 있지만 행 값은 비어 있어 채우지 않는다.

실험 DICONDE 10개는 모두 2×20×253 signed-int16, 150 kHz이고 provider record가 첫 frame을 real,
둘째를 imaginary로 설명한다. cm physical delta와 mm pixel spacing은 SI 변환 후 모두 일치한다. 각 파일은
512자 LO value에 대한 pydicom 경고 하나를 내므로 숨기지 않고 감사 기록에 남겼다. 제공자 filename/comment의
결함 숫자와 간격은 독립 치수 truth나 서로 다른 물리 시편 ID로 승격하지 않는다. 원 archive·DICONDE·CSV와
상용 solver는 공개 wheel에 넣지 않는다. 집계는 `validation/eddy_current_dataset_audit.json`에 있다.
