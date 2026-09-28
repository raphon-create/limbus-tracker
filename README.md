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

## 덱 / 덱 빌더 (deck.js)
상단 탭 오른쪽의 **덱**, **덱 빌더** 탭. 파일 `deck.js`(app.js 보다 먼저 로드). 해시 `#deck`, `#builder` 로 바로 열 수 있음.

### 전투 데이터 (data.json → identities[].combat)
- `kw` 주 상태이상 키워드(화상·출혈·진동·파열·침잠·호흡·충전) = 나무위키 인격 목록의 키워드 아이콘. 빈 배열 = 범용/키워드 없음.
- `kwSub` 부 키워드 = wiki.gg "Identities with ○○" 분류에만 있는 상태이상(덱 소속 아님).
- `kwCount` / `kwWhere` = 기본 스킬 1·2·3 + 수비 + 패시브 + 서포트 패시브(최대 6블록) 중 그 키워드를 본문에 언급하는 블록 수/위치 (나무위키 4동기화 본문 기준).
- `skills` 스킬 1·2·3 (죄악 속성, 공격 유형, 수량 3/2/1), `defense` 수비 스킬(유형·죄악), `skillsExtra`/`defenseExtra` 추가·변형 스킬, `passives`.
- `sinStatus` / `kwStatus` / `check` 검증 상태: 죄악 속성은 나무위키와 wiki.gg IDPage 를 교차 확인(188개 전부 일치). 확인이 안 된 항목은 "확인 필요" 로 표시.
- `fandomNote` Fandom 위키가 다른 값(구버전으로 보임)을 적은 경우 메모. `src` 출처 URL(나무위키 앵커, wiki.gg, Fandom).
- 원본: `tools/combat_manifest.json` (키 "수감자id|인격명", `__meta__` = 키워드/죄악 색상, 출전 인원 규칙과 출처). 고친 뒤
  `python3 tools/update_helpers.py merge-combat` → data.json + data.js 갱신. 확인 필요 목록: `python3 tools/update_helpers.py combat-missing`
- 수집/파싱 스크립트 사본: `tools/combat_build_ref/` (fetch_wikis.py → parse_skills.py → compare_sources.py → build_combat.py).
- 새 인격 추가 시: combat_manifest.json 에 같은 형식으로 항목을 추가(최소 `kw`, `skills`[{s,sin,name,atk,amt}], `defense`, `kwCount`)하고 merge-combat.

### 출전 인원
- 기본 7명 = 현행 거울 던전 「이름과 거미의 거울」(2026-02-19~) 필드 최대 인원(12명 편성, 5명 후보). 스토리 스테이지는 5~7명으로 다양. 덱/빌더 상단에서 1~12 로 변경 가능(localStorage `limbus.deploy.v1`).
- 출전 순서 = 출전 화면에서 선택한 순서. 빌더에서는 순서 1~N 번이 출전, 나머지는 후보(체인 전투 교체 투입·서포트 패시브). 출처: wiki.gg Mirror Dungeon / Battles(Deployment Order).

### 덱 탭
- 키워드마다 덱 카드 1장, 수감자 12칸. 칸마다 그 키워드의 **보유** 인격 중 1순위를 픽(정렬: 키워드 언급 블록 수 → 등급 → 출시일 최신). 다른 보유 후보는 작은 썸네일.
- 보유가 없으면 빈 칸에 미보유 후보와 획득 방법(지금 교환 가능/파편 부족/한정/상시 풀/다음 기회) 표시.
- 완성도 = 보유 매칭 수감자 수 / 12, 출전 인원 충족 여부. 출전 픽의 죄악 분포 막대(스킬 수량 3/2/1 가중).
- "이게 있으면 덱이 완성/강화" = 빈 칸을 채우는 미보유(완성) + 현재 픽보다 언급 블록이 많은 미보유(강화), 지금 교환 가능하면 초록 테두리.
- **빌더로 열기** → 그 덱의 픽과 순서를 빌더로 불러옴.
- 강함/티어 평가는 넣지 않았음(검증 가능한 수치만 사용).

### 덱 빌더
- 수감자 12행: 인격 선택(기본은 보유만, "미보유 인격도 선택지에 표시" 토글), ▲▼/숫자로 출전 순서 변경, "키워드 기준 자동 순서".
- 오른쪽 요약: 출전 인원의 키워드별 인원·언급 블록 합·부 키워드, 죄악 속성 합계(가중/스킬 수/수비), 경고(픽 없음·미보유), 후보의 서포트 패시브.
- 여러 덱 저장/이름 변경/삭제 (localStorage `limbus.decks.v1`, 작업 중인 덱은 `limbus.builder.v1`).
- 공유: **코드 복사** → `LCD1~출전인원~순서~픽~이름` 형식의 짧은 코드(약 70자), **JSON 복사** → 사람이 읽을 수 있는 JSON. 받은 코드/JSON 을 칸에 붙여넣고 **가져오기**.
  코드의 인격 번호는 수감자별 (출시일, 이름) 정렬 순서라 새 인격이 추가돼도 기존 코드가 유지됨.
- 보유 여부는 기존 로직(스크린샷 기본값 + 사용자가 클릭한 값), 교환 가능 여부는 수감자 탭의 파편 입력값을 그대로 사용.
- 전체/수감자 탭의 인격 카드에도 키워드 칩(점선 = 부 키워드, ? = 확인 필요)과 스킬 1·2·3·수비 죄악 칩이 표시되고, 필터에 "키워드" 그룹이 추가됨.

## 커뮤니티 티어 · 메타 덱 (meta.js)
모든 티어는 **커뮤니티 평가를 모아 계산한 참고용** 값입니다(공식 아님). 기준일 2026-09-28, 시즌 8(2026-09-17 시작).

- **신선도 컷오프: 2026-06-01 이후 갱신된 자료만 반영.** S7 후반 핵심 인격(거미집 엄지 6/25, 새벽 사무소 7/9, 차원찢개 7/23)과 중지·약지 덱 평가 이후 자료만 남기기 위함. 그 이전 자료는 제외(지속 갱신 페이지는 최종 갱신일 기준). 제외 목록과 사유는 `tools/meta_manifest.json` → `excluded`와 사이트의 "티어 출처·기준" 모달에 있음.
- **사용 출처**: Prydwen(굴절철도/엔드게임), Great Limbus Library(gll-fun, 2026-09-02 리워크), 게임메카 국민트리(26/09/17), 아카라이브 채널 투표 티어(S7 3성, 거던/거던밖, 2026-09-10 리뉴얼), 고니 블로그 3성 티어표(2026-08-24, 리뷰 연도별 신선도 가중).
- **점수 방식**: 출처별 등급 → 0~100 정규화 → 가중 평균(Prydwen 1.0, GLL 1.0, 아카 표당 0.5, 게임메카 0.9, 고니 0.6×신선도) → SS≥92, S+≥87, S≥82, S-≥77, A+≥72, A≥66, A-≥60, B≥48, C≥34, D.
  합의도 = 출처 수와 표준편차(σ≤7 높음, ≤12 보통, 그 이상 낮음), 범위 25점 이상이면 "의견 갈림". 추세(▲▼)는 아카 초판→리뉴얼, GLL/Prydwen 변경 로그 기준. 모드별 티어: 굴절철도(Prydwen+GLL), 거울던전(아카 "거던"), 일반.
- **데이터**: `data.json` → `identities[].tier`(s, t, n, sd, agree, split, modes, trend, roles, reason, alts, src[]), `meta.tier`(출처·제외·구간), `meta.metaDecks`(core/flex/alts/출처/신뢰도).
- **UI**: 카드 헤더에 작은 티어 배지+추세 화살표(툴팁에 요약), 세부/출처에 출처별 표. 덱 탭 맨 위 "메타 덱"(보유 x/y, 미보유 목록·제작 가능 표시, 대체 한 줄, 빌더로 보내기), 자동 키워드 덱은 티어 → 기존 기준 순으로 픽, 최고 티어 픽이 미보유면 "대체 ←" 표시. 빌더는 선택지에 [티어], 출전 평균 티어, "메타 덱 불러오기".

### 갱신 절차
```
python3 tools/meta_build_ref/build_meta.py     # research 원자료 → tools/meta_manifest.json
python3 tools/update_helpers.py merge-meta      # manifest → data.json(tier/metaDecks) + data.js 재생성
```
원자료는 `/workspace/research/meta/`(Prydwen JSON, GLL 렌더 텍스트, 게임메카·고니·아카 텍스트). 이미지로만 제공되는 아카 표는 수동 판독값이 `build_meta.py`에 들어 있음. 파일 수정 후 `index.html`의 `?v=` 값을 올릴 것.
