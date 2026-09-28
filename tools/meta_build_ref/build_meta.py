#!/usr/bin/env python3
"""커뮤니티 티어/메타 덱 manifest 생성기.
/workspace/research/meta/ 에 저장한 원본(HTML/텍스트/이미지 판독 결과)을 읽어 tools/meta_manifest.json 을 만든다.
집계(가중 평균·티어·합의도·추세·대체 후보)는 update_helpers.py merge-meta 가 manifest 를 읽어 수행한다.
실행: python3 tools/meta_build_ref/build_meta.py
"""
import json, re, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from idx import IDS, match_en, match_ko, ROOT
R = '/workspace/research/meta/'
OUT = os.path.join(ROOT, 'tools', 'meta_manifest.json')
warn = []

def split_en(nm):
    nm = nm.replace('\\u0026', '&').strip()
    for sn in ['Don Quixote', 'Yi Sang', 'Hong Lu', 'Ryoshu', 'Ryōshū', 'Faust', 'Meursault', 'Heathcliff', 'Ishmael', 'Rodion', 'Sinclair', 'Outis', 'Gregor']:
        if nm.endswith(sn): return nm[:-len(sn)].strip(), sn
    return nm, ''

# ---------------- 1. Prydwen (RR/endgame, Uptie 4) ----------------
PRY_N = {'11': 100, '10': 92, '9.5': 85, '9': 78, '8': 66, '7': 52, '6': 38, '5': 22}
PRY_L = {'11': 'SSS', '10': 'SS', '9.5': 'S+', '9': 'S', '8': 'A', '7': 'B', '6': 'C', '5': 'D'}
CAT = {'dps': '딜러', 'status': '상태이상 특화', 'support': '서포터', 'tank': '탱커'}
TAG = {'Burn': '화상', 'Bleed': '출혈', 'Tremor': '진동', 'Rupture': '파열', 'Sinking': '침잠', 'Poise': '호흡', 'Charge': '충전'}
pry = {}
for slug, r in json.load(open(R + 'prydwen_rows.json')).items():
    t, s = split_en(r['name']); k, w = match_en(t, s)
    if w: warn.append('prydwen: ' + w)
    if not k: continue
    v = str(r['ratings'].get('end'))
    if v not in PRY_N: continue
    pry[k] = {'raw': PRY_L[v], 'rawNum': float(v), 'score': PRY_N[v], 'role': CAT.get(r.get('cat'), r.get('cat')),
              'tags': [TAG.get(x, x) for x in r.get('tags', [])], 'updated': (r.get('updatedAt') or '')[:10]}

# ---------------- 2. GLL (general/RR, MD 제외 기준) ----------------
GLL_N = {'SSS': 100, 'SS': 92, 'S': 80, 'A': 64, 'B': 48, 'C': 34, 'D': 20}
L = [l.rstrip('\n') for l in open(R + 'gll.txt', encoding='utf-8')]
gll = {}; tier = None; i = next(i for i, l in enumerate(L) if re.match(r'^SSS tier \(\d+\)', l))
while i < len(L):
    l = L[i]; m = re.match(r'^(SSS|SS|S|A|B|C|D) tier \((\d+)\)', l)
    if m: tier = m.group(1); i += 1; continue
    if l.startswith('GREAT LIMBUS'): break
    if re.match(r'^Ø+$', l) and i + 2 < len(L) and L[i + 1].startswith('['):
        title = L[i + 1]; j = i + 2; new = False
        if L[j] == 'NEW': new = True; j += 1
        k, w = match_en(title, L[j])
        if w: warn.append('gll: ' + w)
        if k: gll[k] = {'raw': tier, 'score': GLL_N[tier], **({'new': True} if new else {})}
        i = j + 1; continue
    i += 1
# GLL changelog -> 이전 티어 기록
gll_hist = {}
C = open(R + 'gll_changelog.txt', encoding='utf-8').read().split('\n')
date = None
for l in C:
    m = re.match(r'^(\d{2})\.(\d{2})\.(\d{4})$', l.strip())
    if m: date = f'{m.group(3)}-{m.group(2)}-{m.group(1)}'; continue
    if not date or not l.startswith('['): continue
    tm = re.search(r'-\s*(SSS|SS|S|A|B|C|D)(?:\s*>\s*(SSS|SS|S|A|B|C|D))?\s*(?:Tier)?\s*$', l)
    if not tm: continue
    for title, sn in re.findall(r'(\[[^\]]+\])\s*((?:Don Quixote|Yi Sang|Hong Lu|Ry[oō]sh[uū]|Faust|Meursault|Heathcliff|Ishmael|Rodion|Sinclair|Outis|Gregor))', l):
        k, w = match_en(title, sn)
        if not k or (w and w.startswith('fuzzy')): continue
        frm, to = (tm.group(1), tm.group(2)) if tm.group(2) else (None, tm.group(1))
        gll_hist.setdefault(k, []).append({'date': date, 'from': frm, 'to': to})

# ---------------- 3. Prydwen changelog (2026) ----------------
pry_hist = {}
PT = r'(SSS|SS|S\+|S|A|B|C|D)'
txt = open(R + 'prydwen_changelog.txt', encoding='utf-8').read()
chunks = re.split(r'(\d{2}\.\d{2}\.20\d{2})', txt)
for n in range(1, len(chunks) - 1, 2):
    d = chunks[n]; body = chunks[n + 1]; date = f'{d[6:10]}-{d[3:5]}-{d[0:2]}'
    if not date.startswith('2026'): continue
    for title, sn, a, b in re.findall(r'(\[[^\]]+\])\s*((?:Don Quixote|Yi Sang|Hong Lu|Ry[oō]sh[uū]|Faust|Meursault|Heathcliff|Ishmael|Rodion|Sinclair|Outis|Gregor))\s*-?\s*' + PT + r'\s*(?:->|→|>)\s*' + PT, body):
        k, w = match_en(title.replace('(Alteration)', '【Alteration】'), sn)
        if k: pry_hist.setdefault(k, []).append({'date': date, 'from': a, 'to': b})
        else: warn.append(f'prydwen changelog: {w}')

# ---------------- 4. 게임메카 국민트리 ----------------
GM_N = {'SS': 95, 'S': 82, 'A': 66}
G = [l.strip() for l in open(R + 'gamemeca.txt', encoding='utf-8')]
gm = {}; i = G.index('코멘트') + 1
def gm_roles(c):
    r = []
    if '딜탱' in c: r += ['딜러', '탱커']
    if '딜포터' in c: r += ['딜러', '서포터']
    if '서브 딜러' in c: r += ['서브 딜러']
    elif '딜러' in c and '딜러' not in r: r += ['딜러']
    if re.search(r'탱커(?! 인격)|탱커$', c) and '탱커' not in r: r += ['탱커']
    if '서포터' in c and '서포터' not in r: r += ['서포터']
    return r
while i + 3 < len(G) and G[i] in GM_N:
    t, n, s, c = G[i:i + 4]; k, w = match_ko(n, s)
    if w: warn.append('gamemeca: ' + w)
    if k: gm[k] = {'raw': t, 'score': GM_N[t], 'comment': c, 'role': gm_roles(c)}
    i += 4

# ---------------- 5. 아카라이브 챈 시즌7 3성 투표 티어표 (이미지 판독, 9/10 리뉴얼 + 9/2 초판) ----------------
AR_N = {'0': 94, '0.5': 84, '1': 72, '1.5': 60, '2': 48}
def T(**kw): return {tier.replace('_', '.').lstrip('t'): v for tier, v in kw.items()}
Y, F, D_, RY, M, HL, H, IS, RO, SC, O, GR = 'yisang', 'faust', 'don', 'ryoshu', 'meursault', 'honglu', 'heathcliff', 'ishmael', 'rodion', 'sinclair', 'outis', 'gregor'
k_ = lambda s, n: f'{s}|{n}'
DAE = k_(D_, '검지 대행자 - 개화 E.G.O::대행'); IDXY = k_(Y, '거미집 검지 아비'); ZAN = k_(RY, '로보토미 E.G.O::잔향 · 외로움')
RAF = k_(F, '거미집 약지 제자'); RAH = k_(HL, '거미집 약지 아비'); MBH = k_(H, '중지 작은 형님'); BLR = k_(RY, '거미집의 검')
MNO = k_(O, '거미집 중지 아비'); LCD = k_(IS, 'LCD 현장추리팀'); TNR = k_(RO, '거미집 엄지 아비'); DWF = k_(F, '새벽 사무소 해결사')
DWG = k_(GR, '새벽 사무소 대표'); AED = k_(GR, 'LCE E.G.O::AEDD'); DIM = k_(Y, 'LCE E.G.O::차원찢개'); TAH = k_(H, '거미집 엄지 제자')
MAI = k_(IS, '거미집 중지 제자'); UDJ = k_(O, 'LCA 우제트 선봉 3팀 팀장'); LMP = k_(GR, '로보토미 E.G.O::램프'); DOC = k_(RO, '약지 야수파 도슨트')
CE3 = k_(HL, '동부 섕크 협회 3과'); HOR = k_(M, '로보토미 E.G.O::호넷【변조】'); CHU = k_(HL, 'S사 추노꾼'); PNK = k_(SC, '거미집 소지 제자')
PAP = k_(F, '검지 수행자:【쪽지】'); RFS = k_(M, '약지 야수파 스튜던트')
ARCA = {
 'md':      {'0': [DAE, IDXY, ZAN, RAF, RAH, MBH, BLR, MNO, LCD, TNR, DWF, DWG], '0.5': [AED, DIM, TAH, MAI, UDJ],
             '1': [LMP, DOC, CE3, HOR, CHU, PNK], '1.5': [PAP], '2': [RFS]},
 'gen':     {'0': [IDXY, RAH, BLR, MNO, TNR, DWF, DWG], '0.5': [DAE, AED, RAF, LCD, ZAN, MBH, TAH, UDJ, LMP],
             '1': [DOC, CE3, CHU, HOR, MAI], '1.5': [PAP, PNK], '2': [RFS, DIM]},
 'md_old':  {'0': [UDJ, DAE, PNK, IDXY, ZAN, RAF, RAH, MBH, BLR, MNO, LCD, TNR, DWF, DWG], '0.5': [HOR, AED, CHU, DIM],
             '1': [PAP, MAI, LMP, DOC, TAH, CE3], '2': [RFS]},
 'gen_old': {'0': [UDJ, LMP, IDXY, ZAN, RAH, BLR, MNO, TNR, DWF, DWG], '0.5': [DAE, PNK, HOR, AED, RAF, LCD],
             '1': [PAP, DOC, MBH, CHU, TAH, CE3], '1.5': [MAI], '2': [RFS, DIM]},
}
arca = {}
for mode in ('md', 'gen', 'md_old', 'gen_old'):
    for t, ks in ARCA[mode].items():
        for k in ks:
            assert k in IDS, k
            arca.setdefault(k, {})[mode] = t

# ---------------- 6. goniblog (3성, 3동 기준, 2026-08-24 게시 / 개별 리뷰 날짜 = 이미지 업로드 월) ----------------
GO_N = {0: 94, 1: 80, 2: 64, 3: 48, 4: 32}
GO_FIX = {'동부-엄지-카포4-': k_(M, '동부 엄지 카포 IIII'), '검지-단말기-돈키혼테단돈': DAE, 'n사-경멸-경외-료슈경경': k_(RY, 'N사 E.G.O::경멸, 경외'),
          '피쿼드호-작살잡이-히스클리프퀴히': k_(H, '피쿼드호 작살잡이'), 'R사-': k_(H, 'R사 제 4무리 토끼팀'), '중싱.png': k_(SC, '중지 작은 아우'),
          '유로지비-20구-': k_(HL, '20구 유로지비'), '동백-': k_(Y, '개화 E.G.O::동백'), '료고파-': k_(RY, '료.고.파. 주방장'), '쥐어들자 파우스트': k_(F, '쥐는 자'), 'n사-경멸-경외-료슈경경슈': k_(RY, 'N사 E.G.O::경멸, 경외')}
SN = ['돈키호테', '이스마엘', '히스클리프', '싱클레어', '그레고르', '파우스트', '뫼르소', '오티스', '홍루', '로쟈', '료슈', '로슈', '이상']
from idx import SIN_KO
gh = open(R + 'goni.html', encoding='utf-8').read()
goni = {}
for tn, rows in json.load(open(R + 'goni_rows.json')).items():
    t = int(tn[-1])
    for disp, img, slug in rows:
        tx = slug if slug and 'yoochris' not in slug else (disp or img)
        tx = re.sub(r'^림버스-?컴퍼니-', '', tx); tx = re.sub(r'-(성능-)?평(가(-정리?)?)?$', '', tx); tx = re.sub(r'-성능$', '', tx)
        parts = tx.replace(' ', '-').split('-'); sid = None
        for p in reversed(parts):
            for s in SN:
                if p.endswith(s): sid = SIN_KO.get(s); break
            if sid: break
        name = '-'.join(parts)
        for s in SN:
            if name.endswith(s): name = name[:-len(s)]; break
        k = GO_FIX.get(tx) or GO_FIX.get(name)
        if not k:
            k, w = match_ko(name, sid=sid)
            if not k: warn.append(f'goni: {w}'); continue
        m = re.search(r'uploads/(\d{4})/(\d{2})/' + re.escape(img), gh)
        rev = f'{m.group(1)}-{m.group(2)}' if m else None
        fresh = 1.0 if rev and rev >= '2026' else 0.6 if rev and rev >= '2025' else 0.3
        if k in goni: warn.append(f'goni dup {k}'); continue
        goni[k] = {'raw': f'Tier{t}', 'score': GO_N[t], 'review': rev, 'fresh': fresh}

# ---------------- 소스 목록 ----------------
def rows(d, extra=None):
    return {k: {**v} for k, v in d.items()}
SOURCES = [
 {'id': 'prydwen', 'site': 'Prydwen.gg', 'region': '해외(EN)', 'title': 'Limbus Company Tier List', 'url': 'https://www.prydwen.gg/limbus-company/tier-list',
  'author': 'Prydwen 편집진', 'date': '2026-09-23', 'dateNote': '헤더 "Last updated 23/August/2026", S8 신규 인격 개별 갱신 2026-09-23(항목 updatedAt)',
  'season': 'S8 초반(신규 2종 포함)', 'modes': ['RR'], 'modeNote': '엔드게임(굴절 철도) 기준, 동기화 4, 역할(딜러/상태이상/서포터/탱커) 내 비교',
  'scale': 'SSS>SS>S+>S>A>B>C>D (숫자 11~5)', 'norm': {'SSS': 100, 'SS': 92, 'S+': 85, 'S': 78, 'A': 66, 'B': 52, 'C': 38, 'D': 22}, 'weight': 1.0, 'ratings': pry},
 {'id': 'gll', 'site': 'Great Limbus Library (gll-fun.com)', 'region': '해외(EN/RU)', 'title': 'Limbus Company Identity Tier List', 'url': 'https://gll-fun.com/limbus/en/tierlist/identities/',
  'author': 'GLL 팀(Ritsy 외)', 'date': '2026-09-02', 'dateNote': '변경 로그 02.09.2026 "Identities Tierlist Rework" + S8 신규(수선실 로쟈 NEW 등) 반영 확인(2026-09-28 열람)',
  'season': 'S8 초반', 'modes': ['RR', 'general'], 'modeNote': '개별 성능+EGO 시너지+팀 가치, 최대 동기화. 거울 던전은 평가 기준 아님(명시)',
  'scale': 'SSS>SS>S>A>B>C>D', 'norm': GLL_N, 'weight': 1.0, 'ratings': gll},
 {'id': 'gamemeca', 'site': '게임메카 국민트리', 'region': '국내(KR)', 'title': '림버스 컴퍼니 티어표', 'url': 'https://trees.gamemeca.com/view.php?seq=1584',
  'author': '게임메카', 'date': '2026-09-17', 'dateNote': '"최종 업데이트 26/09/17"', 'season': 'S7 말~S8 시작', 'modes': ['general'],
  'modeNote': '종합(범용성). SS=범용·대체불가, S=조건부 강함, A=특정 시너지/제한 환경. 미등재 인격은 "평가 없음"으로 취급(추정하지 않음)',
  'scale': 'SS>S>A (51종만 등재)', 'norm': GM_N, 'weight': 0.9, 'ratings': gm},
 {'id': 'arca', 'site': '아카라이브 로보토미 코퍼레이션(림버스) 채널', 'region': '국내(KR)', 'title': '📌정보/공략 시즌 3성 인격 티어표 리뉴얼본 (투표 결과)',
  'url': 'https://arca.live/b/lobotomycoperation/182606246', 'author': '채널 유저 투표(작성자 고정닉, 투표 집계)', 'date': '2026-09-10',
  'dateNote': '9/10 20:00 재투표 반영본. 초판 2026-09-02(https://arca.live/b/lobotomycoperation/181820051)을 추세 비교에 사용',
  'season': 'S7 3성 인격만(25종)', 'modes': ['MD', 'general'], 'modeNote': '"거던 기준"과 "거던 밖 기준" 두 표. 0 > 0.5 > 1 > 1.5 > 2 (인플레로 0티어 과반)',
  'scale': '0/0.5/1/1.5/2/2.5/3', 'norm': AR_N, 'weight': 1.0, 'ratings': arca},
 {'id': 'goni', 'site': '고니 블로그(goniblog.com)', 'region': '국내(KR)', 'title': '림버스 컴퍼니 티어표 (3성 인격 기준)',
  'url': 'https://goniblog.com/림버스-컴퍼니-티어표-3성-인격-기준/', 'author': '고니', 'date': '2026-08-24', 'dateNote': '게시/수정 2026-08-24. 개별 인격 평가글 날짜는 2023~2026로 섞여 있어 리뷰 이미지 업로드 월로 신선도 가중(2026=1.0, 2025=0.6, 2024 이전=0.3)',
  'season': 'S7 후반(S7 인격 대부분 포함, 동부 섕크3 홍루까지)', 'modes': ['general'], 'modeNote': '다양한 컨텐츠 종합, 3동 기준. Tier0~4', 'scale': 'Tier0>1>2>3>4',
  'norm': {'Tier0': 94, 'Tier1': 80, 'Tier2': 64, 'Tier3': 48, 'Tier4': 32}, 'weight': 0.6, 'ratings': goni},
]
DECK_SOURCES = [
 {'id': 'arca_deck', 'site': '아카라이브 채널 덱/편성 질문·답변 글', 'region': '국내(KR)', 'date': '2026-09-14~2026-09-28', 'modes': ['MD', 'story'],
  'posts': [
   {'url': 'https://arca.live/b/lobotomycoperation/183034582', 'date': '2026-09-15', 'title': '그래서 새벽엄지화진덱 대기편성까지 완성형이 뭐임?'},
   {'url': 'https://arca.live/b/lobotomycoperation/183287989', 'date': '2026-09-17', 'title': '10장 밀기용 새벽 화진덱 편성 순서 어떻게 짬?'},
   {'url': 'https://arca.live/b/lobotomycoperation/183297749', 'date': '2026-09-17', 'title': '다들 화진덱 순서랑 편성 어캐함?'},
   {'url': 'https://arca.live/b/lobotomycoperation/183325937', 'date': '2026-09-18', 'title': '님들아 충출덱 편성 어케하면 좋을까?'},
   {'url': 'https://arca.live/b/lobotomycoperation/183515302', 'date': '2026-09-20', 'title': '호침덱 편성인원 누구하는게 정배임??'},
   {'url': 'https://arca.live/b/lobotomycoperation/184141106', 'date': '2026-09-26', 'title': '충출덱 편성 어떻게해서 쓰고있어?'},
   {'url': 'https://arca.live/b/lobotomycoperation/184156793', 'date': '2026-09-26', 'title': '흑수덱 편성 질문이용!'},
   {'url': 'https://arca.live/b/lobotomycoperation/184236893', 'date': '2026-09-27', 'title': '현역인 성능덱 알려줘잉'},
   {'url': 'https://arca.live/b/lobotomycoperation/184242744', 'date': '2026-09-27', 'title': '충출덱 2번자리 이스하고 파우중에 누구임?'},
   {'url': 'https://arca.live/b/lobotomycoperation/184250477', 'date': '2026-09-27', 'title': '중지덱 중지맨 다있어야함?'},
   {'url': 'https://arca.live/b/lobotomycoperation/184264972', 'date': '2026-09-27', 'title': '중지덱에 렘그렉 넣어야하나?'},
   {'url': 'https://arca.live/b/lobotomycoperation/177393617', 'date': '2026-07-20', 'title': '현 메타 거던 15층 1티어 덱 뭐라고 생각해? (S7 후반, 참고)'},
  ], 'note': '개별 유저 의견(댓글 포함). 여러 글에서 반복되는 구성만 core 로 채택. KST 기준 날짜'},
 {'id': 'prydwen_teams', 'site': 'Prydwen Teams Database', 'region': '해외(EN)', 'url': 'https://www.prydwen.gg/limbus-company/teams-database', 'date': '2026-05-22',
  'modes': ['RR', 'general'], 'note': '"Last updated 22/May/2026" — S7 후반 인격(새벽·엄지·중지 완성) 이전이라 core 판단엔 쓰지 않고 flex/대체 참고로만 사용(화상: 리우3 이상·마탄 오티스, 파열: 흑수 편성 등)'},
 {'id': 'gamemeca', 'site': '게임메카 국민트리 코멘트', 'region': '국내(KR)', 'url': 'https://trees.gamemeca.com/view.php?seq=1584', 'date': '2026-09-17', 'modes': ['general'],
  'note': '"다른 새벽 사무소 인격과 연계", "다른 흑수 인격들과 상호작용", "질투 공명" 등 시너지 서술을 core 근거로 사용'},
]
EXCLUDED = [
 {'site': 'TierMaster (tiermaster.vercel.app/ko/limbus)', 'url': 'https://tiermaster.vercel.app/ko/limbus/general', 'date': '2026-05-15', 'reason': '마지막 갱신 2026-05-15(컷오프 이전), 익명 투표+DC 시트 기반, 인격명 OCR 깨짐 다수, S7 후반·S8 인격 미배치'},
 {'site': 'Gamerch JP 최강 인격 랭킹', 'url': 'https://gamerch.com/limbuscompany/662980', 'date': '2026-08-21(페이지) / 표는 "2026/7/30 편집 중"', 'reason': '티어표 본문이 7/30 편집 중 상태로 새벽 사무소(7/9)·엄지 거미집(6/25) 등 S7 후반 인격 누락, 캐릭터 애칭 표기가 많아 인격 매칭 신뢰도 낮음'},
 {'site': 'Prydwen Teams Database', 'url': 'https://www.prydwen.gg/limbus-company/teams-database', 'date': '2026-05-22', 'reason': '티어 점수엔 미사용(티어 정보 없음). 덱은 S7 후반 이전 구성이라 flex/대체 참고만'},
 {'site': '아카라이브 "현재 메타 0티어 덱 리스트 정리"', 'url': 'https://arca.live/b/lobotomycoperation/178430504', 'date': '2026-07-30', 'reason': '본문 말미 "라는 상상을 해보았습니다" — 미출시/가상 인격을 전제로 한 상상글이라 제외'},
 {'site': '아카라이브 "인격 티어표 짜봄"', 'url': 'https://arca.live/b/lobotomycoperation/180090498', 'date': '2026-08-16', 'reason': '개인 체감 기준(작성자 명시), 비추천 13 > 추천 6, 댓글에서 기준 부재 지적 다수'},
 {'site': '아카라이브 "개인적 림버스 티어표" / "호감고닉 티어표"', 'url': 'https://arca.live/b/lobotomycoperation/183706018', 'date': '2026-09-21', 'reason': '인기/유머 티어표(성능 아님)'},
 {'site': 'Beebom / ChainPlay / allthings.how / PropelRC / games.gg / Gamebrott / lawod', 'url': '', 'date': '2026-06~08', 'reason': 'Prydwen 티어를 재가공한 파생 글 — 중복 가중 방지'},
 {'site': '2upskill 티어/팀 가이드', 'url': 'https://2upskill.com', 'date': '2026-07-02', 'reason': 'S7 중반 기준 SEO형 글, 자체 평가 근거 불명확'},
 {'site': 'PixelNitro 팀 가이드', 'url': 'https://pixelnitro.com', 'date': '2026(S7)', 'reason': '존재하지 않는 인격명을 언급하는 등 신뢰 불가(자동 생성 의심)'},
 {'site': 'HostedGG / penguingames / appmatch / pekuo 등 SEO 랭킹', 'url': '', 'date': '2026-08~09', 'reason': '출처·기준 불명 요약형 글, 1차 평가로 보기 어려움'},
 {'site': 'gamesfuze 수감자 투자 우선순위', 'url': '', 'date': '2026-09', 'reason': '인격 단위 평가 아님'},
 {'site': 'Game8 (EN)', 'url': 'https://game8.co/games/Limbus-Company', 'date': '-', 'reason': '티어 페이지 URL 404 / 최신판 확인 불가'},
 {'site': 'Pocket Gamer 티어', 'url': '', 'date': '미표기', 'reason': '날짜 미표기·구버전 인격 위주'},
 {'site': '인벤 림버스 게시판', 'url': 'https://www.inven.co.kr/', 'date': '-', 'reason': '림버스 전용 공략 게시판을 찾지 못함(시도한 board 번호는 다른 게임) — 확인 불가'},
 {'site': 'DC 림버스 컴퍼니 마이너 갤러리', 'url': 'https://gall.dcinside.com/mgallery/board/lists/?id=limbuscompany', 'date': '2026-09-20~28 검색', 'reason': '"티어표" 검색 결과가 리세/질문글 위주, 구조화된 최신 성능 티어표 없음'},
 {'site': 'Reddit r/limbuscompany 티어 토론', 'url': 'https://www.reddit.com/r/limbuscompany/', 'date': '2026', 'reason': '평점표 아님 — "Prydwen은 RR 기준", "GLL은 구 인격을 높게 둠", "Prydwen이 중지 돈을 과소평가" 같은 불일치 의견만 참고(점수 미반영)'},
 {'site': 'goniblog 개별 구 리뷰(2023~2024 이미지)', 'url': 'https://goniblog.com/림버스-컴퍼니-티어표-3성-인격-기준/', 'date': '2023~2024', 'reason': '제외는 아니고 가중치 0.3으로 축소(예: 남부 디에치 4과 로쟈 Tier0는 2023 평가)'},
]
man = {
 '__meta__': {
  'asOf': '2026-09-28', 'season': 8, 'seasonStart': '2026-09-17',
  'cutoff': '2026-06-01', 'cutoffWhy': 'S7 후반 핵심 인격(거미집 엄지 6/25, 새벽 사무소 7/9, 차원찢개 7/23)과 중지·약지 덱 완성 이후 평가만 남기기 위해 2026-06-01 이후 갱신된 자료만 점수에 반영. 2026-05 이전 자료는 제외(단, 지속 갱신 페이지는 최종 갱신일 기준)',
  'method': ['각 출처의 고유 등급을 0~100으로 정규화(출처별 표 참조)',
             '가중 평균: Prydwen 1.0, GLL 1.0, 아카 투표 1.0(거던/거던밖 두 표를 0.5씩), 게임메카 0.9, 고니 0.6×리뷰 신선도(2026=1.0, 2025=0.6, ≤2024=0.3)',
             '티어 구간: SS≥92, S+≥87, S≥82, S-≥77, A+≥72, A≥66, A-≥60, B≥48, C≥34, D<34',
             '합의도: 평가 출처 수 + 표준편차(σ≤7 높음, ≤12 보통, 그 외 낮음, 1곳=단일), 최고-최저 25점 이상이면 "의견 갈림"',
             '추세: GLL 변경 로그(2026-08) 및 9/2 리워크 전후, 아카 투표 초판(9/2)→재투표(9/10), Prydwen 2026-04 변경(보조)',
             '모드별: RR=Prydwen+GLL, MD=아카 "거던 기준"표(S7 3성만), 일반=GLL+게임메카+아카 "거던 밖"+고니',
             '미평가 인격은 점수를 추정하지 않음(평가 없음)'],
  'disclaimer': '커뮤니티 평가를 모아 계산한 참고용 티어입니다. 공식 아님 · 기준일 2026-09-28'},
 'sources': SOURCES, 'deckSources': DECK_SOURCES, 'excluded': EXCLUDED,
 'history': {'gll': gll_hist, 'prydwen': pry_hist},
}

# ---------------- 메타 덱 (출처 근거 명시) ----------------
DECKS = [
 {'id': 'hwajin', 'name': '화진덱 (새벽·엄지)', 'kw': ['화상', '진동'], 'modes': ['MD', 'story'],
  'core': [DWF, DWG, k_(SC, '새벽 사무소 해결사'), TNR, TAH, k_(M, '동부 엄지 카포 IIII')],
  'flex': [k_(Y, '남부 리우 협회 3과'), BLR, k_(O, '로보토미 E.G.O::마탄'), k_(IS, '정사무소 대표'), k_(D_, '동부 섕크 협회 3과'), k_(HL, '마침표 사무소 대표')],
  'evidence': ['아카 9/15: 6인 구성 "새벽사무소 3인 + 엄지듀오 + 뫼횡(카포IIII)", 7인은 거검슈/리우 이상 추가, 7번째로 정사무소 이스·마탄 오티스 제안',
               '아카 9/17: "엄지3 새벽3 뤼상", "엄지아비 새벽3은 유지"', '아카 9/27: 현역 성능덱으로 "엄지새벽 화진덱" 반복 언급',
               '게임메카: 새벽 파우스트/그레고르 "다른 새벽 사무소 인격과 연계된 화상&진동"'],
  'sources': ['arca_deck', 'gamemeca', 'prydwen_teams'], 'date': '2026-09-27'},
 {'id': 'middle', 'name': '중지덱 (질투 공명 화상·출혈)', 'kw': ['화상', '출혈'], 'modes': ['MD', 'story'],
  'core': [MNO, MAI, MBH, k_(D_, '중지 작은 아우'), k_(M, '중지 작은 아우'), k_(SC, '중지 작은 아우')],
  'flex': [LMP, k_(Y, '남부 리우 협회 3과'), k_(RY, '로보토미 E.G.O::적안 · 참회')],
  'evidence': ['아카 9/27: "중지맨 6인 채우면 됨 — 6인이면 질투 6공명"', '아카 9/27: "거던이면 6인, 그 외는 7번째 램그렉이 정석", "거던은 중지 5인+리우 이상도"',
               '아카 7/20: "중지 화출" 4대장 덱', '게임메카: 중지 아비 오티스 "질투 공명 + 반격"'],
  'sources': ['arca_deck', 'gamemeca'], 'date': '2026-09-27'},
 {'id': 'ring', 'name': '충출덱 (약지 출혈·충전)', 'kw': ['출혈', '충전'], 'modes': ['MD', 'story'],
  'core': [RAH, RAF, DOC, k_(Y, '약지 점묘파 스튜던트')],
  'flex': [AED, k_(H, 'W사 4등급 정리 요원 - CCA'), RFS, k_(IS, '오트쿠튀르::르루주 부티크'), k_(RY, '로보토미 E.G.O::적안 · 참회'), k_(M, 'R사 제 4무리 코뿔소팀')],
  'evidence': ['아카 9/26: 약루/약파우/르루주 이스/약로쟈/약르소(약상)/W 히스/충그렉(AEDD) 편성 공유 — "편성 인원 자체는 정상"',
               '아카 9/27: "충출은 약지 아비·제자 1,2번", 르루주 이스는 거던에서 예열이 어려워 비추', '아카 9/18: 적참 료슈는 거던에서 "꼽사리"', '아카 7/20: "약지 충출" 4대장'],
  'sources': ['arca_deck'], 'date': '2026-09-27'},
 {'id': 'heishou', 'name': '흑수덱 (파열·호흡)', 'kw': ['파열', '호흡'], 'modes': ['MD', 'story', 'RR'],
  'core': [k_(HL, '홍원 군주'), k_(F, '흑수 - 묘 필두'), k_(O, '흑수 - 묘'), k_(RY, '흑수 - 묘')],
  'flex': [k_(RO, '흑수 - 사'), k_(IS, '가주 후보'), k_(Y, '흑수 - 오 필두'), k_(GR, '흑수 - 사'), k_(D_, '흑수 - 미'), k_(H, '흑수 - 유 필두')],
  'evidence': ['아카 9/26: "거던 흑수는 군루+묘티스면 충분, 거던 밖 흑수는 군루·묘티스·묘슈·묘파우 필요", "사로쟈 정도는 있는 게 좋다"',
               '게임메카: 홍원 군주 "다른 흑수 인격들과 상호작용", 묘 필두 파우 "파열 유지"', 'Prydwen 5/22 Rupture 팀: 묘 필두 파우·묘 오티스·묘 료슈·사 로쟈·가주 후보 이스·오 필두 이상·홍원 군주',
               'Prydwen 변경 로그: 홍원 군주 SSS 승급 사유 "흑수와 3개 아키타입"'],
  'sources': ['arca_deck', 'gamemeca', 'prydwen_teams'], 'date': '2026-09-26'},
 {'id': 'index', 'name': '호침덱 (검지·마침표 호흡·침잠)', 'kw': ['호흡', '침잠'], 'modes': ['MD', 'story'],
  'core': [IDXY, DAE, PAP, k_(HL, '마침표 사무소 대표'), k_(H, '마침표 사무소 해결사'), ZAN],
  'flex': [UDJ, PNK, k_(M, '검계 우두머리')],
  'evidence': ['아카 9/20: "검지3+마침표2에 잔슈까지 고정", 7번째는 우티스 등 취향(“3검지까지만 고정”)', '아카 7/20: 뤼상(검지 아비 이상)은 호침덱',
               '게임메카: 검지 아비 이상·대행 돈·쪽지 파우스트 모두 "침잠&호흡"', 'Prydwen 5/22 Poise-Fullstops: 마침표 2인+검지 아비 이상+소지 제자 싱클'],
  'sources': ['arca_deck', 'gamemeca', 'prydwen_teams'], 'date': '2026-09-20'},
 {'id': 'jinchim', 'name': '진침탕 (진동·침잠)', 'kw': ['진동', '침잠'], 'modes': ['MD'],
  'core': [UDJ, k_(Y, '로보토미 E.G.O::엄숙한 애도'), k_(IS, '정사무소 대표'), ZAN],
  'flex': [k_(RO, '로보토미 E.G.O::눈물로 벼려낸 검'), k_(H, '와일드헌트'), k_(D_, '흑수 - 미')],
  'evidence': ['아카 9/20: "우티스는 진침탕에서 써야 돼서", "애도 이상 없어서 진침탕 완성 못함"', '아카 7/20·9/27: "에깊 좋은 진침탕" 1티어/현역 언급',
               '게임메카: 정사무소 이스·잔향 료슈·우제트 오티스 "진동&침잠"'],
  'confidence': '낮음', 'confidenceNote': '구성원 전체 목록을 준 출처가 없어 언급된 인격 + 진동·침잠 키워드로 구성',
  'sources': ['arca_deck', 'gamemeca'], 'date': '2026-09-27'},
 {'id': 'spider', 'name': '거미집 (거검슈 중심)', 'kw': ['화상', '출혈', '호흡'], 'modes': ['MD', 'story'],
  'core': [BLR, IDXY, RAH, TNR, MNO],
  'flex': [RAF, TAH, MAI, PNK],
  'evidence': ['아카 9/27 "현역 성능덱": "거미집" 최다 언급', '아카 7/20: "거검슈 1인"(단독 캐리)', '게임메카: 거검슈 "같은 소속이 사망할수록 강해지는"',
               'Prydwen/GLL: 거미집 아비 4종+거검슈 모두 SSS~SS'],
  'confidence': '보통', 'confidenceNote': '거미집 아비들은 각자 다른 키워드 덱의 핵심이라, 실제로는 각 손가락 덱에 섞어 쓰는 경우가 많음',
  'sources': ['arca_deck', 'gamemeca'], 'date': '2026-09-27'},
]
for d in DECKS:
    for k in d['core'] + d['flex']: assert k in IDS, (d['id'], k)
man['decks'] = DECKS
json.dump(man, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('saved', OUT, {s['id']: len(s['ratings']) for s in SOURCES})
print('history', {k: len(v) for k, v in man['history'].items()})
for w in warn: print('WARN', w)
