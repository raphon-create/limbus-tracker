#!/usr/bin/env python3
"""림버스 인격 트래커 유지보수 도구.

사용법 (사이트 폴더 /workspace/limbus-site 기준, 어디서 실행해도 됨):

  # 1) data.json 을 고친 뒤 data.js 재생성 (file:// 로 열 때 필요)
  python3 tools/update_helpers.py build-js

  # 2) img/portraits_manifest.json 의 초상화 정보를 data.json 에 병합 + data.js 재생성
  python3 tools/update_helpers.py merge-portraits

  # 3) 새 인격 초상화 추가 (이미지 URL 또는 위키 파일/문서 URL, 또는 로컬 파일)
  #    카드 비율(332:512) 이미지면 그대로 축소, 가로로 긴 일러스트면 --cx 로 가로 중심(0~1)을 지정해 크롭
  python3 tools/update_helpers.py add-portrait don "오트쿠튀르::르누아르 브랜드 매니저" \
      "https://static.wikia.nocookie.net/limbuscompany/images/..../File.png" [--cx 0.5] [--page 출처문서URL]
  #    -> img/<sinner>_<slug>.webp 저장, manifest + data.json + data.js 모두 갱신

  # 4) 초상화 누락 목록
  python3 tools/update_helpers.py missing

  # 5) tools/combat_manifest.json (상태이상 키워드·스킬 죄악 속성·출전 규칙) 을 data.json 에 병합 + data.js 재생성
  #    각 인격의 identities[].combat 필드와 meta.deck 이 갱신됨. 수동으로 고칠 땐 manifest 를 고친 뒤 이 명령 실행.
  python3 tools/update_helpers.py merge-combat
  #    전투 데이터가 없는/확인 필요 인격 목록
  python3 tools/update_helpers.py combat-missing

  # 6) 커뮤니티 티어·메타 덱: tools/meta_build_ref/build_meta.py 로 tools/meta_manifest.json 생성(원본은 /workspace/research/meta)
  #    -> merge-meta 가 출처별 점수를 0~100 정규화·가중 평균해 identities[].tier, meta.tier, meta.metaDecks 를 채움
  python3 tools/update_helpers.py merge-meta

  # 7) 사영전투(Reflectrial) 덱: tools/meta_build_ref/build_saeong.py 로 tools/saeong_manifest.json 생성(원본은 /workspace/research/saeong)
  #    -> merge-saeong 이 덱별 평균 티어·대체 후보(페이즈 접대 키워드/죄악/소속 가중)를 계산해 meta.saeong 을 채움 (merge-meta 이후 실행)
  python3 tools/update_helpers.py merge-saeong

키: data.json 의 sinners[].id (yisang faust don ryoshu meursault honglu heathcliff ishmael rodion
sinclair outis gregor) + identities[].name (한국어 인격명, data.json 과 정확히 일치).
필요 패키지: Pillow (pip install pillow). 네트워크 다운로드는 curl 사용.
"""
import sys, os, json, re, subprocess, tempfile, hashlib, argparse, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data.json')
DATAJS = os.path.join(ROOT, 'data.js')
IMG = os.path.join(ROOT, 'img')
MANIFEST = os.path.join(IMG, 'portraits_manifest.json')
W, H = 240, 370          # 인게임 카드 비율(332x512)에 맞춘 출력 크기
FIELDS = ('portrait', 'portraitSource', 'portraitSourceUrl', 'portraitSourcePage', 'portraitNote')

def load(p, d=None):
    if not os.path.exists(p): return d
    with open(p, encoding='utf-8') as f: return json.load(f)

def dump(p, obj):
    with open(p, 'w', encoding='utf-8') as f: json.dump(obj, f, ensure_ascii=False, indent=1)

def build_js():
    d = load(DATA)
    with open(DATAJS, 'w', encoding='utf-8') as f:
        f.write('window.LIMBUS_DATA=' + json.dumps(d, ensure_ascii=False) + ';\n')
    print(f'data.js 재생성 완료 ({os.path.getsize(DATAJS):,} bytes)')

def merge_portraits():
    d = load(DATA); man = load(MANIFEST, {})
    n = miss = 0
    for s in d['sinners']:
        for i in s['identities']:
            v = man.get(f"{s['id']}|{i['name']}")
            for k in FIELDS: i.pop(k, None)
            if v and os.path.exists(os.path.join(ROOT, v['portrait'])):
                i.update({k: v[k] for k in FIELDS if k in v}); n += 1
            else:
                i['portrait'] = None; miss += 1
    d.setdefault('meta', {})['portraitCredit'] = ('인격 카드 이미지 © Project Moon. 출처: Limbus Company Fandom Wiki(공식 카드 이미지) / '
                                                  '나무위키(동기화 전 일러스트를 카드 비율로 크롭). 개인용 비공식 트래커.')
    dump(DATA, d); print(f'초상화 병합: {n}개 있음, {miss}개 없음'); build_js()

def slugify(sid, name):
    h = hashlib.md5(name.encode()).hexdigest()[:6]
    asc = re.sub(r'[^A-Za-z0-9]+', '_', name).strip('_').lower()
    return f"{sid}_{asc + '_' if asc else ''}{h}"

def resolve_url(url):
    """위키 '파일:' 문서/Fandom 파일 문서 URL을 실제 이미지 URL로 바꿔 봄 (가능한 경우)."""
    if re.search(r'\.(png|webp|jpe?g|gif)(\?|/revision|$)', url, re.I) or url.startswith(('http://i.namu.wiki', 'https://i.namu.wiki')):
        return url
    m = re.match(r'https?://([^/]+)/wiki/(File:[^?#]+)', url)
    if m:
        api = f'https://{m.group(1)}/api.php?' + urllib.parse.urlencode({'action': 'query', 'titles': urllib.parse.unquote(m.group(2)),
                                                                          'prop': 'imageinfo', 'iiprop': 'url', 'format': 'json'})
        out = subprocess.run(['curl', '-sL', '-m', '30', '-A', 'Mozilla/5.0', api], capture_output=True, text=True).stdout
        for p in json.loads(out)['query']['pages'].values():
            return p['imageinfo'][0]['url']
    return url

def fetch(url, dst):
    ref = 'https://namu.wiki/' if 'namu.wiki' in url else url
    r = subprocess.run(['curl', '-sL', '-m', '60', '-A', 'Mozilla/5.0', '-e', ref, '-o', dst, '-w', '%{http_code}', url], capture_output=True, text=True)
    if r.stdout.strip() != '200' or os.path.getsize(dst) < 1000:
        raise SystemExit(f'다운로드 실패 (HTTP {r.stdout}): {url}')

def make_card(src_path, out_path, cx=None):
    from PIL import Image
    im = Image.open(src_path).convert('RGB'); w, h = im.size
    if w / h > 0.8:  # 가로 일러스트 -> 카드 비율로 크롭
        cw = round(h * 332 / 512); c = (cx if cx is not None else 0.5) * w
        x0 = int(max(0, min(w - cw, c - cw / 2))); im = im.crop((x0, 0, x0 + cw, h))
    im = im.resize((W, round(im.height * W / im.width)), Image.LANCZOS)
    im = im.crop((0, 0, W, H)) if im.height > H else im.resize((W, H), Image.LANCZOS)
    im.save(out_path, 'WEBP', quality=80, method=6)

def add_portrait(sid, name, url, cx=None, page=None):
    d = load(DATA)
    s = next((x for x in d['sinners'] if x['id'] == sid), None)
    if not s: raise SystemExit(f'수감자 id 없음: {sid}')
    if not any(i['name'] == name for i in s['identities']):
        raise SystemExit(f'data.json 에 "{name}" 인격이 없습니다. 먼저 data.json 에 인격을 추가하세요.')
    os.makedirs(IMG, exist_ok=True)
    rel = f'img/{slugify(sid, name)}.webp'
    with tempfile.TemporaryDirectory() as td:
        if os.path.exists(url): src = url; real = os.path.abspath(url)
        else:
            real = resolve_url(url); src = os.path.join(td, 'src'); fetch(real, src)
        make_card(src, os.path.join(ROOT, rel), cx)
    man = load(MANIFEST, {})
    man[f'{sid}|{name}'] = {'portrait': rel, 'portraitSource': 'manual', 'portraitSourceUrl': real,
                            'portraitSourcePage': page or url, 'portraitNote': '수동 추가' + (f' (크롭 중심 {cx})' if cx is not None else '')}
    dump(MANIFEST, man); print('저장:', rel); merge_portraits()

COMBAT = os.path.join(ROOT, 'tools', 'combat_manifest.json')

def merge_combat():
    d = load(DATA); man = load(COMBAT, {})
    meta = man.get('__meta__')
    n = miss = 0
    for s in d['sinners']:
        for i in s['identities']:
            v = man.get(f"{s['id']}|{i['name']}")
            if v: i['combat'] = v; n += 1
            else:
                i['combat'] = {'kw': [], 'skills': [], 'check': ['전투 데이터 없음 — 확인 필요'], 'kwStatus': '확인 필요', 'sinStatus': '확인 필요'}; miss += 1
    if meta: d.setdefault('meta', {})['deck'] = meta
    dump(DATA, d); print(f'전투 데이터 병합: {n}개, 없음 {miss}개'); build_js()

def combat_missing():
    d = load(DATA)
    for s in d['sinners']:
        for i in s['identities']:
            c = i.get('combat') or {}
            if not c.get('skills') or c.get('check'):
                print(f"{s['id']}|{i['name']}:", '; '.join(c.get('check') or ['전투 데이터 없음']))

def missing():
    d = load(DATA)
    for s in d['sinners']:
        for i in s['identities']:
            if not i.get('portrait'): print(f"{s['id']}|{i['name']}")

SAEONG = os.path.join(ROOT, 'tools', 'saeong_manifest.json')
META = os.path.join(ROOT, 'tools', 'meta_manifest.json')
BANDS = [(92, 'SS'), (87, 'S+'), (82, 'S'), (77, 'S-'), (72, 'A+'), (66, 'A'), (60, 'A-'), (48, 'B'), (34, 'C'), (0, 'D')]
LET = {'SSS': 100, 'SS': 92, 'S+': 85, 'S': 80, 'A': 64, 'B': 48, 'C': 34, 'D': 20}

def band(x):
    return next(t for lim, t in BANDS if x >= lim)

def merge_meta():
    """tools/meta_manifest.json (커뮤니티 티어 출처·원점수·메타 덱) -> 집계 후 data.json 병합 + data.js 재생성."""
    import statistics
    d = load(DATA); man = load(META)
    if not man: raise SystemExit('tools/meta_manifest.json 없음 — tools/meta_build_ref/build_meta.py 먼저 실행')
    mm = man['__meta__']; S = {s['id']: s for s in man['sources']}
    ids = {f"{s['id']}|{i['name']}": (s, i) for s in d['sinners'] for i in s['identities']}
    def kws(i):
        c = i.get('combat') or {}; return set(c.get('kw') or []) | set(c.get('kwSub') or [])
    agg = {}
    for key, (s, i) in ids.items():
        ent = []
        r = S['prydwen']['ratings'].get(key)
        if r: ent.append({'id': 'prydwen', 'raw': r['raw'], 's': r['score'], 'w': 1.0, 'm': ['RR'], 'd': r.get('updated') or S['prydwen']['date'],
                          'note': ' · '.join(x for x in [r.get('role'), '/'.join(r.get('tags') or [])] if x)})
        r = S['gll']['ratings'].get(key)
        if r: ent.append({'id': 'gll', 'raw': r['raw'], 's': r['score'], 'w': 1.0, 'm': ['RR', 'general'], 'd': S['gll']['date']})
        r = S['gamemeca']['ratings'].get(key)
        if r: ent.append({'id': 'gamemeca', 'raw': r['raw'], 's': r['score'], 'w': S['gamemeca']['weight'], 'm': ['general'], 'd': S['gamemeca']['date'], 'note': r['comment']})
        r = S['arca']['ratings'].get(key)
        if r:
            nm = S['arca']['norm']
            if 'md' in r: ent.append({'id': 'arca', 'sub': 'md', 'raw': f"거던 {r['md']}", 's': nm[r['md']], 'w': 0.5, 'm': ['MD'], 'd': S['arca']['date'],
                                      **({'note': f"초판(9/2) {r['md_old']}"} if r.get('md_old') and r['md_old'] != r['md'] else {})})
            if 'gen' in r: ent.append({'id': 'arca', 'sub': 'gen', 'raw': f"거던밖 {r['gen']}", 's': nm[r['gen']], 'w': 0.5, 'm': ['general'], 'd': S['arca']['date'],
                                       **({'note': f"초판(9/2) {r['gen_old']}"} if r.get('gen_old') and r['gen_old'] != r['gen'] else {})})
        r = S['goni']['ratings'].get(key)
        if r: ent.append({'id': 'goni', 'raw': r['raw'], 's': r['score'], 'w': round(S['goni']['weight'] * r['fresh'], 2), 'm': ['general'], 'd': S['goni']['date'],
                          'note': f"개별 리뷰 {r['review']}" + (' (구 평가, 가중 축소)' if r['fresh'] < 1 else '')})
        if not ent: continue
        tw = sum(e['w'] for e in ent); sc = sum(e['s'] * e['w'] for e in ent) / tw
        per = {}
        for e in ent:
            if e['w'] >= 0.5 or e['id'] == 'arca': per.setdefault(e['id'], []).append(e['s'])   # 합의도는 신선한(가중 0.5+) 평가만
        vals = [sum(v) / len(v) for v in per.values()] or [sc]
        sd = statistics.pstdev(vals) if len(vals) > 1 else 0.0
        rng = max(vals) - min(vals) if len(vals) > 1 else 0
        agree = '단일' if len(vals) == 1 else '높음' if sd <= 7 else '보통' if sd <= 12 else '낮음'
        modes = {}
        for mo in ('RR', 'MD', 'general'):
            es = [e for e in ent if mo in e['m']]
            if es:
                x = sum(e['s'] * e['w'] for e in es) / sum(e['w'] for e in es); modes[mo] = {'t': band(x), 's': round(x)}
        # 추세
        sig = []
        for e in ent:
            if e['id'] == 'arca' and e.get('note'):
                old = e['note'].split()[-1]; nw = e['raw'].split()[-1]
                sig.append({'src': 'arca', 'd': '2026-09-10', 'txt': f"아카 {'거던' if e['sub']=='md' else '거던밖'} {old}→{nw}", 'v': S['arca']['norm'][nw] - S['arca']['norm'][old]})
        for src, cur in (('gll', S['gll']['ratings'].get(key)), ('prydwen', S['prydwen']['ratings'].get(key))):
            h = sorted(man['history'][src].get(key, []), key=lambda x: x['date'])
            h26 = [x for x in h if x['date'] >= '2026-01-01']
            for x in h26:
                if x['from']:
                    sig.append({'src': src, 'd': x['date'], 'txt': f"{'GLL' if src=='gll' else 'Prydwen'} {x['from']}→{x['to']} ({x['date'][5:].replace('-', '/')})", 'v': LET[x['to']] - LET[x['from']]})
            if h and cur and h[-1]['date'] >= '2026-01-01' and h[-1]['to'] != cur['raw'] and cur['raw'] in LET:
                dd = '2026-09-02' if src == 'gll' else h[-1]['date']
                sig.append({'src': src, 'd': dd, 'txt': f"{'GLL' if src=='gll' else 'Prydwen'} {h[-1]['to']}→{cur['raw']} ({'9/2 리워크' if src=='gll' else h[-1]['date'][5:].replace('-', '/') + ' 이후 재평가'})",
                            'v': LET[cur['raw']] - LET[h[-1]['to']]})
        recent = [x for x in sig if x['d'] >= mm['cutoff']]
        basis = recent or [dict(x, v=x['v'] / 2) for x in sig]
        tot = sum(x['v'] for x in basis)
        rel = i.get('release') or ''
        trend = 'new' if rel >= '2026-09-01' else ('up' if tot > 3 else 'down' if tot < -3 else ('flat' if basis else None))
        roles = []
        for e in ent:
            if e['id'] == 'prydwen':
                rr = S['prydwen']['ratings'][key].get('role')
                if rr and rr not in roles: roles.append(rr)
            if e['id'] == 'gamemeca':
                for rr in S['gamemeca']['ratings'][key].get('role') or []:
                    if rr not in roles: roles.append(rr)
        gmr = S['gamemeca']['ratings'].get(key)
        if gmr: reason = gmr['comment'] + ' (게임메카)'
        else:
            bits = []
            pr = S['prydwen']['ratings'].get(key); gl = S['gll']['ratings'].get(key)
            if pr: bits.append(f"Prydwen RR {pr['raw']}" + (f" {pr['role']}" if pr.get('role') else '') + (f" ({'/'.join(pr['tags'])})" if pr.get('tags') else ''))
            if gl: bits.append(f"GLL {gl['raw']}")
            ar = S['arca']['ratings'].get(key)
            if ar and 'md' in ar: bits.append(f"아카 투표 거던 {ar['md']}·밖 {ar['gen']}")
            reason = ' · '.join(bits)
        agg[key] = {'t': band(sc), 's': round(sc, 1), 'n': len(vals), 'sd': round(sd, 1), 'agree': agree, **({'split': True} if rng >= 25 else {}),
                    'range': [round(min(vals)), round(max(vals))], 'trend': trend, 'trendNote': [x['txt'] for x in sorted(sig, key=lambda x: x['d'], reverse=True)][:4],
                    'modes': modes, 'roles': roles, 'reason': reason, 'src': ent}
    # 대체 후보: 같은 수감자 + 키워드 공유, 점수 순
    def alts_for(key, want_kw, n=5, prefer=()):
        s, i = ids[key]; out = []
        for j in s['identities']:
            k2 = f"{s['id']}|{j['name']}"
            if k2 == key: continue
            shared = sorted(kws(j) & set(want_kw))
            if not shared and k2 not in prefer: continue
            out.append((k2 in prefer, agg.get(k2, {}).get('s', 0), len(shared), k2, shared))
        out.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
        return [{'k': k2, 'kw': sh} for _, _, _, k2, sh in out[:n]]
    for key, (s, i) in ids.items():
        i.pop('tier', None)
        if key in agg:
            a = agg[key]
            if a['s'] >= 77: a['alts'] = alts_for(key, kws(i) or set())
            i['tier'] = a
    decks = []
    for dk in man.get('decks', []):
        dk = json.loads(json.dumps(dk))
        cs = [agg.get(k, {}).get('s', 0) for k in dk['core']]
        dk['s'] = round(sum(cs) / len(cs), 1); dk['t'] = band(dk['s'])
        flex_by_sin = {}
        for k in dk['flex']: flex_by_sin.setdefault(k.split('|')[0], []).append(k)
        dk['alts'] = {k: alts_for(k, dk['kw'], 5, prefer=tuple(flex_by_sin.get(k.split('|')[0], []))) for k in dk['core']}
        decks.append(dk)
    decks.sort(key=lambda x: -x['s'])
    srcs = [{k: v for k, v in s.items() if k != 'ratings'} | {'count': len(s['ratings'])} for s in man['sources']]
    d['meta']['tier'] = {**mm, 'bands': [[a, b] for a, b in BANDS], 'sources': srcs, 'deckSources': man.get('deckSources', []), 'excluded': man.get('excluded', [])}
    d['meta']['metaDecks'] = decks
    dump(DATA, d)
    top = sorted(agg.items(), key=lambda x: -x[1]['s'])
    print(f'커뮤니티 티어 병합: 평가 {len(agg)}개 / 전체 {len(ids)}개, 메타 덱 {len(decks)}개')
    print('상위:', ', '.join(f"{k}({v['t']} {v['s']})" for k, v in top[:12]))
    build_js()

def merge_saeong():
    """tools/saeong_manifest.json -> data.json meta.saeong (덱 평균 티어 + 슬롯별 대체 후보) + data.js 재생성."""
    d = load(DATA); man = load(SAEONG)
    if not man: raise SystemExit('tools/saeong_manifest.json 없음 — tools/meta_build_ref/build_saeong.py 먼저 실행')
    ids = {f"{s['id']}|{i['name']}": (s, i) for s in d['sinners'] for i in s['identities']}
    def kws(i):
        c = i.get('combat') or {}; return set(c.get('kw') or []) | set(c.get('kwSub') or [])
    def sins(i):
        c = i.get('combat') or {}; return [x.get('sin') for x in (c.get('skills') or []) + (c.get('skillsExtra') or [])]
    def dsin(i):
        return ((i.get('combat') or {}).get('defense') or {}).get('sin')
    def tscore(i): return (i.get('tier') or {}).get('s', 0)
    for st in man['stages']:
        for dk in st['decks']:
            ph = [p for p in st['phases'] if p['n'] in dk['phases']]
            fkw = set(dk['kw']) | {k for p in ph for k in p['fav']['kw']}
            fsin = {k for p in ph for k in p['fav']['sin']}; ffac = {k for p in ph for k in p['fav']['fac']}
            flex = set(dk['flex']) | set(dk.get('bench', []))
            cs = [tscore(ids[k][1]) for k in dk['core']]
            dk['s'] = round(sum(cs) / len(cs), 1); dk['t'] = band(dk['s'])
            dk['alts'] = {}
            for k in dk['core']:
                s, i = ids[k]; out = []
                want_def = i.get('combat', {}).get('defense', {}).get('sin') if i.get('combat') else None
                for j in s['identities']:
                    k2 = f"{s['id']}|{j['name']}"
                    if k2 == k or j.get('upcoming'): continue
                    why = []; sc = 0
                    if k2 in flex: sc += 6; why.append('출처 언급')
                    dkw = sorted(kws(j) & set(dk['kw'])); pkw = sorted((kws(j) & fkw) - set(dk['kw']))
                    if dkw: sc += 2 * len(dkw); why.append('덱 키워드 ' + '·'.join(dkw))
                    if pkw: sc += 1 * len(pkw); why.append('접대 키워드 ' + '·'.join(pkw))
                    ns = sum(1 for x in sins(j) if x in fsin)
                    if ns: sc += 1.5 * min(ns, 3); why.append('접대 속성 ' + '·'.join(sorted(fsin)) + f'×{ns}')
                    if want_def and dsin(j) == want_def and want_def in fsin: sc += 1.5; why.append(f'{want_def} 수비')
                    fac = sorted(set(j.get('keywords') or []) & ffac)
                    if fac: sc += 3; why.append('소속 ' + '·'.join(fac))
                    if sc <= 0: continue
                    sc += tscore(j) / 25
                    out.append((sc, k2, why))
                out.sort(key=lambda x: -x[0])
                dk['alts'][k] = [{'k': k2, 'why': why, 'fit': round(sc, 1)} for sc, k2, why in out[:5]]
    d['meta']['saeong'] = man
    dump(DATA, d)
    for st in man['stages']:
        print(st['name'], [(dk['name'], dk['t'], dk['s']) for dk in st['decks']])
    build_js()

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('build-js'); sub.add_parser('merge-portraits'); sub.add_parser('missing')
    sub.add_parser('merge-combat'); sub.add_parser('combat-missing'); sub.add_parser('merge-meta'); sub.add_parser('merge-saeong')
    a = sub.add_parser('add-portrait'); a.add_argument('sinner'); a.add_argument('name'); a.add_argument('url')
    a.add_argument('--cx', type=float); a.add_argument('--page')
    x = ap.parse_args()
    if x.cmd == 'build-js': build_js()
    elif x.cmd == 'merge-portraits': merge_portraits()
    elif x.cmd == 'missing': missing()
    elif x.cmd == 'merge-combat': merge_combat()
    elif x.cmd == 'combat-missing': combat_missing()
    elif x.cmd == 'merge-meta': merge_meta()
    elif x.cmd == 'merge-saeong': merge_saeong()
    else: add_portrait(x.sinner, x.name, x.url, x.cx, x.page)
