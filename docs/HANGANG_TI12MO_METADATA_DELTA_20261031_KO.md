# Ti12Mo5Hf metadata 전용 증분

이 묶음은 source ZIP을 취득하거나 열지 않는다. 새 ModelSpec·세 공개 계약·source ID·CC0 dataset 이용조건·기존에 확보한 README hash의 서로 일치하는지 확인하는 두 metadata 작업만 수행한다. 이전 job과 snapshot은 변경하지 않는다.

`scripts/hpc_ti12mo_metadata_delta_20261031.py`의 `contracts`는 standalone ModelSpec, member_count의 단위 `1`, runtime schema/저장 schema, central registry의 import/등록 loop AST를 대조한다. 최소 dependency closure만 사용하므로 전체 registry를 실행했다고 주장하지 않는다.

`provenance`는 source/설치용 catalog에서 복사한 해당 세 row와 capture 시점의 전체 catalog 파일 hash 선언, source 이용조건, CC0 dataset record, asset byte/MD5 pin, README의 기존 로컬 byte/MD5/SHA-256 관측을 비교한다. Catalog 전체나 README 본문을 계산노드로 복사하지 않는다. 따라서 README를 계산노드에서 재해시하거나 ZIP SHA/member/관측값을 검증하는 작업이 아니다. 비교의 정확한 범위를 결과에 남긴다.

최소 source closure, 세 schema, 이 metadata 발췌 및 digest 기록만 immutable archive에 담는다. raw/evidence와 원본 ZIP/README text는 제외한다. `hpc-results/hangang-ti12mo-metadata-*/dispatch.json`에 고정 archive SHA·파일별 hash·stage·task·job ID를 보존한다. 기존 공유 CPU `run.sh cpu` 연결만 사용하고, QoS가 꽉 차면 로컬 비동기 dispatcher가 제출 여유를 확인하는 동안 개발을 계속한다. 결과가 없으면 통과로 집계하지 않는다.
