"""인격 이름 매칭 도우미 (build_meta.py 용)."""
import json, re, os, sys, unicodedata, difflib
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, '/workspace/research')
from en_map import EN
D = json.load(open(os.path.join(ROOT, 'data.json'), encoding='utf-8'))
IDS = {}          # key -> identity dict
SIN = {}          # sid -> sinner dict
for s in D['sinners']:
    SIN[s['id']] = s
    for i in s['identities']:
        IDS[f"{s['id']}|{i['name']}"] = i
SIN_EN = {unicodedata.normalize('NFKD', v[0]).encode('ascii', 'ignore').decode().lower(): k for k, v in EN.items()}
SIN_KO = {s['name']: s['id'] for s in D['sinners']}
SIN_KO.update({'로슈': 'ryoshu', '그렉': 'gregor', '돈키': 'don', '싱클': 'sinclair', '히스': 'heathcliff', '마엘': 'ishmael', '뫼르소': 'meursault'})

def en_norm(t):
    t = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()
    t = t.replace('||||', 'iiii').replace('||', 'ii').replace('(', ' ').replace(')', ' ')
    t = re.sub(r'\b(the|assoc|association|of)\b', ' ', t)
    t = t.replace('awls', 'awl').replace('harpooner', 'harpooneer')
    return re.sub(r'[^a-z0-9]', '', t)

EN_IDX = {}
for sid, (sname, m) in EN.items():
    for ko, en in m.items():
        EN_IDX[(sid, en_norm(en))] = f'{sid}|{ko}'

def match_en(title, sinner):
    s = unicodedata.normalize('NFKD', sinner).encode('ascii', 'ignore').decode().lower().strip()
    sid = SIN_EN.get(s)
    if not sid: return None, f'sinner? {sinner}'
    n = en_norm(title)
    k = EN_IDX.get((sid, n))
    if k: return k, None
    cands = {nn: kk for (ss, nn), kk in EN_IDX.items() if ss == sid}
    best = difflib.get_close_matches(n, list(cands), n=1, cutoff=0.8)
    if best: return cands[best[0]], f'fuzzy {title} -> {cands[best[0]]}'
    return None, f'no match {title} / {sinner}'

def ko_norm(t):
    t = t.replace('E.G.O::', 'ego').replace('E.G.O', 'ego').replace('·', '')
    return re.sub(r'[^0-9a-z가-힣]', '', t.lower())

def match_ko(name, sinner_ko=None, sid=None):
    sid = sid or SIN_KO.get(sinner_ko)
    n = ko_norm(name)
    pool = {k: ko_norm(k.split('|')[1]) for k in IDS if (not sid or k.startswith(sid + '|'))}
    for k, v in pool.items():
        if v == n: return k, None
    best = difflib.get_close_matches(n, list(pool.values()), n=1, cutoff=0.75)
    if best:
        k = next(k for k, v in pool.items() if v == best[0]); return k, f'fuzzy {name} -> {k}'
    return None, f'no match {name}/{sinner_ko or sid}'
