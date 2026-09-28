"""wiki.gg / Fandom 위키텍스트에서 스킬1~3·수비 죄악 속성과 "Identities with <상태이상>" 분류를 뽑아
나무위키 파싱 결과(skills_parsed.json)와 비교 → wikigg_parsed.json, fandom_sin_check.json 생성."""
import json,re
SM={'wrath':'분노','lust':'색욕','sloth':'나태','gluttony':'탐식','gluthony':'탐식','gloom':'우울','pride':'오만','envy':'질투'}
KM={'Burn':'화상','Bleed':'출혈','Tremor':'진동','Rupture':'파열','Sinking':'침잠','Poise':'호흡','Charge':'충전'}
def sins(wt):
    o={}
    for key in ['skill1','skill2','skill3','defense']:
        i=wt.find('|'+key+'={{')
        if i<0: continue
        m=re.search(r'\|sin=\s*(\w+)',wt[i:i+600])
        if m: o[key]=SM.get(m.group(1).lower(),m.group(1))
    return o
P=json.load(open('wikigg_pages.json')); W=json.load(open('wikigg_titles.json'))['match']
out={}
for k,t in W.items():
    wt=P[t]['wt']; o=sins(wt); cats=re.findall(r'\[\[Category:Identities with ([^\]|]+)',wt)
    o.update({'cats':cats,'kw':[KM[c] for c in KM if c in cats],'title':t,'ts':P[t]['ts']}); out[k]=o
json.dump(out,open('wikigg_parsed.json','w'),ensure_ascii=False,indent=1)
N=json.load(open('skills_parsed.json')); F=json.load(open('fandom_pages.json')); mis={}
for k,v in F.items():
    fs=sins(v['wt']); sk=N[k]['skills']; ns={}
    for slot in '123':
        a=[x for x in sk if x['kind']=='attack' and x['slot']==slot]
        if a: ns['skill'+slot]=a[0]['sin']
    d=[x for x in sk if x['kind']=='defense']
    if d: ns['defense']=d[0]['sin']
    diff={kk:(fs.get(kk),ns.get(kk)) for kk in ns if fs.get(kk)!=ns.get(kk)}
    if diff: mis[k]={'diff':diff,'title':v['title']}
json.dump({'checked':list(F),'mismatch':mis,'titles':{k:v['title'] for k,v in F.items()}},open('fandom_sin_check.json','w'),ensure_ascii=False,indent=1)
