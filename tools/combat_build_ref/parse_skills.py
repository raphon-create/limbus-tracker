from bs4 import BeautifulSoup, NavigableString
import re,json,base64
ORDER=['yisang','faust','don','ryoshu','meursault','honglu','heathcliff','ishmael','rodion','sinclair','outis','gregor']
SINS=['분노','색욕','나태','탐식','우울','오만','질투']
KW=['화상','출혈','진동','파열','침잠','호흡','충전']
out={}
def tokens(s,a,b):
    st=False;res=[]
    for el in s.body.descendants:
        if el is a: st=True; continue
        if b is not None and el is b: break
        if not st: continue
        if isinstance(el,NavigableString):
            if el.parent.name in ('style','script'): continue
            t=el.strip()
            if t: res.append(t)
        elif el.name=='img' and el.get('data-src'): res.append('<IMG:'+(el.get('alt') or '')+'>')
    return res
for k in ORDER:
    s=BeautifulSoup(open(f'namu_{k}.html').read(),'lxml')
    anchors=[a for a in s.find_all('a',id=True) if re.match(r'^s-2\.[123]\.\d+$',a['id'])]
    allanch=[a for a in s.find_all('a',id=True) if re.match(r'^s-[\d.]+$',a['id'])]
    # nav keyword icons: after each 332x512 card linking to own anchors
    nav={}
    cur=None
    for el in s.body.descendants:
        if getattr(el,'name',None)=='img' and el.get('data-src'):
            src=el.get('src','')
            dims=None
            if src.startswith('data:image/svg'):
                m=re.findall(r'width="(\d+)" height="(\d+)"',base64.b64decode(src.split(',')[1]).decode()); dims=m[0] if m else None
            alt=el.get('alt') or ''
            if dims==('332','512'):
                a=el.find_parent('a'); href=a.get('href','') if a else ''
                m=re.search(r'#(s-2\.[123]\.\d+)$',href)
                cur=m.group(1) if m and cur!='DONE' else None
                if cur and cur in nav: cur=None  # only first occurrence
                if cur: nav[cur]=[]
            elif cur and alt.endswith('-테두리'):
                nav[cur].append(alt.replace('림버스','').replace('-테두리',''))
            elif cur and dims and int(dims[0])>200: cur=None
    for idx,a in enumerate(anchors):
        nxt=None
        pos=allanch.index(a)
        if pos+1<len(allanch): nxt=allanch[pos+1]
        T=tokens(s,a,nxt)
        name=re.sub(r'\s*\[편집\]$','',' '.join(T[:3])); name=re.sub(r'^[\d.]+\s*','',name).strip()
        # section title tokens: '2.2.1.' 'name' '[편집]'
        title=T[1] if len(T)>1 else ''
        # stop at 패닉 유형
        try: end=T.index('패닉 유형')
        except ValueError: end=len(T)
        body=T[:end]
        blocks=[];curb=None
        i=0
        while i<len(body):
            t=body[i]
            if t=='<IMG:림버스컴퍼니 범용스킬>':
                curb={'kind':'skill','tokens':[]}; blocks.append(curb)
            elif t in ('패시브','서포트 패시브') and (i+1<len(body)):
                curb={'kind':'passive' if t=='패시브' else 'support','name':body[i+1],'tokens':[]}; blocks.append(curb)
            elif curb is not None: curb['tokens'].append(t)
            i+=1
        skills=[];passives=[]
        for b in blocks:
            tk=b['tokens']; txt=' '.join(x for x in tk if not x.startswith('<IMG'))
            kwc={w:txt.count(w) for w in KW if w in txt}
            if b['kind']=='skill':
                slot=None;sin=None
                for x in tk[:4]:
                    m=re.match(r'<IMG:림버스컴퍼니 ('+'|'.join(SINS)+r')(\d)?>',x)
                    if m: sin=m.group(1); slot=m.group(2); break
                # confirm via 죄악 속성
                sin2=None
                if '죄악 속성' in tk:
                    j=tk.index('죄악 속성'); 
                    for x in tk[j+1:j+3]:
                        if x in SINS: sin2=x;break
                kind='attack' if '공격 유형' in tk else ('defense' if '수비 유형' in tk else '?')
                dtype=None;atype=None
                if kind=='defense':
                    j=tk.index('수비 유형'); dtype=next((x for x in tk[j+1:j+3] if x in ('방어','회피','반격')),None)
                    if dtype is None: dtype=next((x for x in tk[j+1:j+4] if not x.startswith('<')),None)
                if kind=='attack':
                    j=tk.index('공격 유형'); atype=next((x for x in tk[j+1:j+3] if x in ('참격','관통','타격')),None)
                nm=next((x for x in tk if not x.startswith('<')),None)
                amt=None
                if '스킬 수량' in tk:
                    j=tk.index('스킬 수량'); amt=next((x for x in tk[j+1:j+3] if not x.startswith('<')),None)
                skills.append({'kind':kind,'slot':slot,'sin':sin2 or sin,'sinIcon':sin,'name':nm,'atk':atype,'def':dtype,'amt':amt,'kw':kwc})
            else:
                sinreq=next((re.match(r'<IMG:림버스(\S+)UI>',x).group(1) for x in tk[:3] if re.match(r'<IMG:림버스(\S+)UI>',x)),None)
                cnt=None;rt=None
                for jx,x in enumerate(tk[:6]):
                    if x=='<IMG:림버스컴퍼니 수량>' and jx+1<len(tk): cnt=tk[jx+1]
                    if x in ('보유','공명'): rt=x
                passives.append({'kind':b['kind'],'name':b['name'],'kw':kwc,'req':sinreq,'reqN':cnt,'reqT':rt})
        out[f'{k}|{title}']={'anchor':a['id'],'nav':nav.get(a['id']),'skills':skills,'passives':passives}
json.dump(out,open('skills_parsed.json','w'),ensure_ascii=False,indent=1)
d=json.load(open('/workspace/limbus-site/data.json'))
names={f"{s['id']}|{i['name']}" for s in d['sinners'] for i in s['identities']}
print('missing',names-set(out)); print('extra',set(out)-names)
from collections import Counter
print(Counter(len([x for x in v['skills'] if x['kind']=='attack']) for v in out.values()))
print(Counter(len([x for x in v['skills'] if x['kind']=='defense']) for v in out.values()))
print(Counter(len(v['passives']) for v in out.values()))
print(Counter(str(v['nav']) for v in out.values()))
