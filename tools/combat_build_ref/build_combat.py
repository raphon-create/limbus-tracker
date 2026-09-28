import json,urllib.parse
N=json.load(open('skills_parsed.json')); G=json.load(open('wikigg_parsed.json'))
FC=json.load(open('fandom_sin_check.json'))
D=json.load(open('/workspace/limbus-site/data.json'))
KW=['화상','출혈','진동','파열','침잠','호흡','충전']
def dnorm(t):
    if not t: return None
    return t.replace('가드','방어')
man={}
for s in D['sinners']:
    for i in s['identities']:
        k=f"{s['id']}|{i['name']}"; n=N[k]; g=G.get(k)
        namu=i['source'].split(' ; ')[0]
        namu_url=namu.split('#')[0]+'#'+n['anchor']
        rec={'kw':[],'kwSub':[],'kwCount':{},'kwWhere':{},'skills':[],'skillsExtra':[],'defense':None,'defenseExtra':[],'passives':[],'check':[],
             'src':{'namu':namu_url}}
        if g: rec['src']['wikigg']='https://limbuscompany.wiki.gg/wiki/'+urllib.parse.quote(g['title'].replace(' ','_'))
        if k in FC['titles']: rec['src']['fandom']='https://limbuscompany.fandom.com/wiki/'+urllib.parse.quote(FC['titles'][k].replace(' ','_'))
        if n['nav'] is None or not n['skills']:
            rec['check'].append('출시 전/문서 미작성: 키워드·죄악 속성 확인 필요')
            rec['kwStatus']='확인 필요'; rec['sinStatus']='확인 필요'
            man[k]=rec; continue
        rec['kw']=list(n['nav'])
        at=[x for x in n['skills'] if x['kind']=='attack']; df=[x for x in n['skills'] if x['kind']=='defense']
        base=[];used=set()
        for slot in '123':
            c=[x for x in at if x['slot']==slot]
            if c:
                x=c[0]; used.add(id(x))
                base.append({'s':int(slot),'sin':x['sin'],'name':x['name'],'atk':x['atk'],'amt':int(x['amt']) if (x['amt'] or '').isdigit() else None,'kw':x['kw']})
        rec['skills']=[{kk:v for kk,v in b.items() if kk!='kw'} for b in base]
        for x in at:
            if id(x) not in used: rec['skillsExtra'].append({'s':int(x['slot']) if x['slot'] else None,'sin':x['sin'],'name':x['name'],'atk':x['atk'],'note':x['amt'] if x['amt'] and not x['amt'].isdigit() else None})
        if df:
            rec['defense']={'sin':df[0]['sin'],'type':dnorm(df[0]['def']),'name':df[0]['name']}
            rec['defenseExtra']=[{'sin':x['sin'],'type':dnorm(x['def']),'name':x['name']} for x in df[1:]]
        for p in n['passives']:
            rec['passives'].append({'kind':'패시브' if p['kind']=='passive' else '서포트 패시브','name':p['name'],'req':p['req'],'reqN':p['reqN'],'reqT':p['reqT']})
        # keyword block counts over base 6 blocks
        blocks=[('S'+str(b['s']),b['kw']) for b in base]
        if df: blocks.append(('수비',df[0]['kw']))
        for p in n['passives']: blocks.append(('패시브' if p['kind']=='passive' else '서포트',p['kw']))
        for w in KW:
            where=[lab for lab,kw in blocks if w in kw]
            if where: rec['kwCount'][w]=len(where); rec['kwWhere'][w]=where
        # verification
        if len(base)!=3: rec['check'].append('기본 스킬 3개를 모두 판독하지 못함')
        if g:
            gs=[g.get('skill1'),g.get('skill2'),g.get('skill3')]; ns=[b['sin'] for b in base]
            ok=gs==ns and (not df or g.get('defense')==df[0]['sin'])
            rec['sinStatus']='나무위키·wiki.gg 일치' if ok else '확인 필요'
            if not ok: rec['check'].append(f'죄악 속성 불일치: 나무위키 {ns}/{df[0]["sin"] if df else "-"} vs wiki.gg {gs}/{g.get("defense")}')
            rec['kwSub']=[w for w in g['kw'] if w not in rec['kw']]
            miss=[w for w in rec['kw'] if w not in g['kw']]
            if miss:
                rec['check'].append(f"키워드 {'/'.join(miss)}: 나무위키 분류에만 있음(wiki.gg 분류 없음) — 확인 필요")
                rec['kwStatus']='일부 확인 필요'; rec['kwUnverified']=miss
            else: rec['kwStatus']='나무위키 분류 + wiki.gg 분류 일치'
            notext=[w for w in rec['kw'] if w not in rec['kwCount'] and not any(w in x['kw'] for x in n['skills'])]
            if notext: rec['check'].append(f"키워드 {'/'.join(notext)}: 스킬/패시브 본문에 직접 언급 없음")
        else:
            rec['sinStatus']='나무위키만'; rec['kwStatus']='나무위키만'; rec['check'].append('wiki.gg 문서 매칭 실패')
        if k in FC['mismatch']:
            d=FC['mismatch'][k]['diff']; real={kk:v for kk,v in d.items() if v[0]}
            if real: rec['fandomNote']='Fandom 위키 값이 다름(구버전으로 보임): '+', '.join(f"{kk} Fandom {v[0]} → 현행 {v[1]}" for kk,v in real.items())
        man[k]=rec
json.dump(man,open('/workspace/limbus-site/tools/combat_manifest.json','w'),ensure_ascii=False,indent=0)
from collections import Counter
print(len(man)); print(Counter(v.get('sinStatus') for v in man.values())); print(Counter(v.get('kwStatus') for v in man.values()))
for k,v in man.items():
    if v['check'] or v.get('fandomNote'): print(k,v['check'],v.get('fandomNote',''))

META={
 'asOf':'2026-09-28',
 'keywords':[{'id':'화상','en':'Burn','color':'#e8662e'},{'id':'출혈','en':'Bleed','color':'#d0344a'},{'id':'진동','en':'Tremor','color':'#d9b84a'},
   {'id':'파열','en':'Rupture','color':'#3fbf9a'},{'id':'침잠','en':'Sinking','color':'#5a7de0'},{'id':'호흡','en':'Poise','color':'#86cfee'},{'id':'충전','en':'Charge','color':'#a6d63c'}],
 'sins':[{'id':'분노','en':'Wrath','color':'#c8323b'},{'id':'색욕','en':'Lust','color':'#e3802b'},{'id':'나태','en':'Sloth','color':'#e2c23a'},
   {'id':'탐식','en':'Gluttony','color':'#83b83a'},{'id':'우울','en':'Gloom','color':'#3fb3c9'},{'id':'오만','en':'Pride','color':'#3a68c8'},{'id':'질투','en':'Envy','color':'#9346c2'}],
 'deployDefault':7,'deployPresets':[5,6,7],
 'deployNote':['현행 거울 던전 「이름과 거미의 거울」(2026-02-19~): 수감자 12명을 데리고 들어가며 필드에는 최대 7명, 나머지 5명은 후보(Backup)로 교체 투입된다.',
   '스토리·일반 스테이지는 스테이지마다 최대 출전 인원이 다르다(보통 5~7명, 집중 전투는 흔히 최대 6명).',
   '출전 순서 = 출전 화면에서 수감자를 선택한 순서(1번부터). 2턴부터 추가 스킬 슬롯이 이 순서대로 주어지고(최대 인원 미만 출전 시), 속도 동점이나 "가장 ~한 아군 1명" 같은 효과의 동점 대상 결정, 일부 E.G.O 기프트 대상 지정에 쓰인다.',
   '체인 전투(거울 던전 포함)에서는 최대 인원을 넘겨 선택한 수감자가 순서대로 후보가 되어, 출전 수감자가 사망/퇴각하면 출전 순서대로 교체 투입된다.',
   '서포트 패시브는 편성에는 있지만 출전하지 않은(후보) 인격의 것이 출전 아군에게 적용된다.'],
 'deploySources':[{'name':'Limbus Company Wiki (wiki.gg) — Mirror Dungeon (2026-09-24 편집본)','url':'https://limbuscompany.wiki.gg/wiki/Mirror_Dungeon'},
   {'name':'Limbus Company Wiki (wiki.gg) — Battles: Deployment Order (2026-09-26 편집본)','url':'https://limbuscompany.wiki.gg/wiki/Battles'},
   {'name':'Wikipedia — Limbus Company (스테이지별 5·6·7명)','url':'https://en.wikipedia.org/wiki/Limbus_Company'}],
 'sortRule':'정렬 기준(검증 가능한 값만): ① 해당 키워드를 본문에 언급하는 블록 수 — 기본 스킬 1·2·3 + 수비 스킬 + 패시브 + 서포트 패시브(최대 6, 나무위키 4동기화 기준 본문) ② 등급(000 > 00 > 0) ③ 출시일(최신 우선). 강함/티어 평가는 포함하지 않음.',
 'kwRule':'덱 소속 = 나무위키 인격 목록의 상태이상 키워드 아이콘(주 키워드). wiki.gg "Identities with ○○" 분류로 교차 확인, 나무위키 분류에 없고 wiki.gg 분류에만 있는 상태이상은 "부 키워드"로 표시(덱 소속 아님).',
 'sinRule':'스킬 1·2·3과 수비 스킬의 죄악 속성: 나무위키 인격 문서 + wiki.gg IDPage 템플릿 교차 확인(188개 전부 일치). Fandom 위키는 131개 문서 대조, 7개 인격에서 구버전 값으로 보이는 차이가 있음(각 인격 세부에 표기). 분포 막대는 스킬 수량(1스킬 3장·2스킬 2장·3스킬 1장) 가중.',
 'sources':[{'name':'나무위키 — 각 수감자 인격 문서','url':'https://namu.wiki/'},{'name':'Limbus Company Wiki (wiki.gg)','url':'https://limbuscompany.wiki.gg/'},{'name':'Limbus Company Fandom Wiki','url':'https://limbuscompany.fandom.com/'}]
}
man['__meta__']=META
json.dump(man,open('/workspace/limbus-site/tools/combat_manifest.json','w'),ensure_ascii=False,indent=0)
