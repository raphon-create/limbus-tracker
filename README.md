# 림버스 컴퍼니 인격 수집 트래커 (정적 사이트)
- 실행: `cd /workspace/limbus-site && python3 -m http.server 8765` → http://localhost:8765/  (탭 직접 링크: #gregor 등)
- 데이터: data.json (인격 목록/출시일/획득 방법/교환 규칙/일정). 보유 체크·파편·끈 입력은 브라우저 localStorage에 저장.
- 발푸르기스의 밤이 시작되면 data.json → schedule.walpurgisActive 에 {"start":"YYYY-MM-DD","end":"YYYY-MM-DD"} 를 추가하면 발푸 인격 교환 가능 표시가 켜짐.
- 데이터 생성 스크립트 사본: build_data.py.txt (원본 /workspace/research/build.py, 나무위키 파싱 결과 기반)

## file:// 로 바로 열기
- index.html 을 더블클릭해도 동작합니다 (data.js 에 data.json 내용이 들어 있음). **data.json 을 고치면 반드시 data.js 재생성:**
  `python3 tools/update_helpers.py build-js`

## 인격 초상화 (img/)
- img/*.webp : 인격별 카드 이미지 (240×370, 인게임 카드 비율 332:512). data.json 각 인격의 `portrait`(상대경로), `portraitSource`, `portraitSourceUrl`, `portraitSourcePage`, `portraitNote` 필드.
- 출처: Limbus Company Fandom Wiki 의 공식 카드 이미지(동기화 전, 109개) / 나무위키 인격 문서의 "동기화 전(기본)" 일러스트를 카드 비율로 크롭(79개, 크롭 중심은 수동 검수).
- 이미지 매핑 원본: img/portraits_manifest.json (키 = "수감자id|인격명"). build_data 스크립트로 data.json 을 새로 만든 경우 `python3 tools/update_helpers.py merge-portraits` 로 초상화 필드를 다시 합치세요.
- 새 인격 추가 시:
  1. data.json 의 해당 수감자 identities 에 인격 추가
  2. `python3 tools/update_helpers.py add-portrait <수감자id> "<인격명>" "<이미지 URL 또는 Fandom File: 문서 URL>" [--cx 0.5]`
     (카드 비율 이미지는 그대로 축소, 가로 일러스트는 --cx 로 인물의 가로 위치(0~1)를 지정해 크롭) → img 저장 + manifest + data.json + data.js 자동 갱신
  3. `python3 tools/update_helpers.py missing` 으로 누락 확인
- 이미지가 없거나 로드에 실패하면 카드에 수감자 이름 자리표시가 표시됩니다.
- 카드 초상화를 클릭해도 보유/미보유가 전환됩니다 (기본 지급 LCB 제외).
- tools/portrait_build_ref/ : 최초 일괄 수집에 쓴 스크립트 사본(참고용, /workspace/research 경로 기준).
- 이미지 © Project Moon. 개인용 비공식 트래커.
