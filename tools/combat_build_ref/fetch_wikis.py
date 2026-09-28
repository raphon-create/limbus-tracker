"""전투 데이터 교차 확인용 위키 원문 수집 (참고용, /workspace/research 기준 경로).
1) wiki.gg: Category:Identities 목록 → en_map.py 영문명과 매칭 → api.php 로 IDPage 위키텍스트 일괄 수집 (wikigg_pages.json)
2) Fandom: 같은 영문명으로 api.php revisions 수집 (fandom_pages.json)
나무위키 HTML(namu_<sinner>.html)은 초상화 작업 때 받은 것을 parse_skills.py 가 파싱.
순서: fetch_wikis.py → parse_skills.py → (wikigg_parsed / fandom_sin_check 생성: build_combat.py 앞부분 참조) → build_combat.py
      → python3 tools/update_helpers.py merge-combat"""
import json,urllib.request,urllib.parse,time,unicodedata,re
UA={'User-Agent':'Mozilla/5.0 (personal limbus tracker)'}
def api(base,p,post=False):
    if post: req=urllib.request.Request(base,data=urllib.parse.urlencode(p).encode(),headers=UA)
    else: req=urllib.request.Request(base+'?'+urllib.parse.urlencode(p),headers=UA)
    return json.load(urllib.request.urlopen(req,timeout=90))
exec(open('en_map.py').read())
G='https://limbuscompany.wiki.gg/api.php'
mem=[];cont={}
while True:
    d=api(G,{'action':'query','list':'categorymembers','cmtitle':'Category:Identities','cmlimit':500,'format':'json',**cont})
    mem+=[m['title'] for m in d['query']['categorymembers'] if m['ns']==0]
    if 'continue' in d: cont=d['continue']
    else: break
norm=lambda t: re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',t).encode('ascii','ignore').decode().lower())
nm={norm(t):t for t in mem}; match={}
for sid,(sn,m) in EN.items():
    for ko,en in m.items():
        t=nm.get(norm(en+' '+sn))
        if t: match[f'{sid}|{ko}']=t
json.dump({'members':mem,'match':match},open('wikigg_titles.json','w'),ensure_ascii=False,indent=1)
res={}; tl=list(match.values())
for i in range(0,len(tl),25):
    d=api(G,{'action':'query','prop':'revisions','rvprop':'content|timestamp','rvslots':'main','titles':'|'.join(tl[i:i+25]),'format':'json','formatversion':2},post=True)
    for p in d['query']['pages']:
        if 'revisions' in p: res[p['title']]={'wt':p['revisions'][0]['slots']['main']['content'],'ts':p['revisions'][0]['timestamp']}
    time.sleep(0.5)
json.dump(res,open('wikigg_pages.json','w'),ensure_ascii=False)
