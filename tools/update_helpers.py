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

def missing():
    d = load(DATA)
    for s in d['sinners']:
        for i in s['identities']:
            if not i.get('portrait'): print(f"{s['id']}|{i['name']}")

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('build-js'); sub.add_parser('merge-portraits'); sub.add_parser('missing')
    a = sub.add_parser('add-portrait'); a.add_argument('sinner'); a.add_argument('name'); a.add_argument('url')
    a.add_argument('--cx', type=float); a.add_argument('--page')
    x = ap.parse_args()
    if x.cmd == 'build-js': build_js()
    elif x.cmd == 'merge-portraits': merge_portraits()
    elif x.cmd == 'missing': missing()
    else: add_portrait(x.sinner, x.name, x.url, x.cx, x.page)
