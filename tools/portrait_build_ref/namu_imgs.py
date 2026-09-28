from bs4 import BeautifulSoup
import re,base64,json,subprocess,os
ORDER=['yisang','faust','don','ryoshu','meursault','honglu','heathcliff','ishmael','rodion','sinclair','outis','gregor']
out={}
KO={'yisang':'이상','faust':'파우스트','don':'돈키호테','ryoshu':'료슈','meursault':'뫼르소','honglu':'홍루','heathcliff':'히스클리프','ishmael':'이스마엘','rodion':'로쟈','sinclair':'싱클레어','outis':'오티스','gregor':'그레고르'}
def dims(el):
    s=el.get('src','')
    if s.startswith('data:image/svg'):
        m=re.findall(r'width="(\d+)" height="(\d+)"',base64.b64decode(s.split(',')[1]).decode())
        if m: return tuple(map(int,m[0]))
    return None
for k in ORDER:
    s=BeautifulSoup(open(f'namu_{k}.html').read(),'lxml')
    anchors=[a for a in s.find_all('a',id=True) if re.match(r'^s-2\.[123]\.\d+$',a['id'])]
    ids=set(a['id'] for a in anchors)
    # heading names
    names={}
    for a in anchors:
        t=a.parent.get_text(' ',strip=True)
        t=re.sub(r'^\d+(\.\d+)*\.\s*','',t); t=re.sub(r'\s*\[편집\]$','',t)
        names[a['id']]=t
    cur=None; got={}
    for el in s.body.descendants:
        if getattr(el,'name',None)=='a' and el.get('id') in ids: cur=el['id']; continue
        if getattr(el,'name',None)=='a' and el.get('id','').startswith('s-3'): cur=None
        if cur and getattr(el,'name',None)=='img' and el.get('data-src'):
            d=dims(el)
            if d and d[0]>=600 and d[0]>d[1] and (el.get('alt') or '').startswith(KO[k]) and cur not in got:
                got[cur]=('https:'+el['data-src'],d,el.get('alt'))
    for aid,nm in names.items():
        out[f'{k}|{nm}']={'anchor':aid,'img':got.get(aid)}
json.dump(out,open('namu_base_imgs.json','w'),ensure_ascii=False,indent=1)
print(len(out), sum(1 for v in out.values() if v['img']))
for kk,v in out.items():
    if not v['img']: print('noimg',kk)
