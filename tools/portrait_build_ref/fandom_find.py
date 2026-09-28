import json,urllib.request,urllib.parse,re,time
exec(open('en_map.py').read())
API='https://limbuscompany.fandom.com/api.php?'
def get(p):
    u=API+urllib.parse.urlencode(p)
    req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 (personal identity tracker)'})
    for t in range(3):
        try: return json.load(urllib.request.urlopen(req,timeout=40))
        except Exception as e: err=e; time.sleep(2)
    raise err
def info(titles):
    out={}
    for i in range(0,len(titles),45):
        d=get({'action':'query','titles':'|'.join(titles[i:i+45]),'prop':'imageinfo','iiprop':'url|size','format':'json','formatversion':2})
        norm={n['to']:n['from'] for n in d['query'].get('normalized',[])}
        for p in d['query']['pages']:
            if 'imageinfo' in p:
                ii=p['imageinfo'][0]; out[norm.get(p['title'],p['title'])]=(p['title'],ii['url'],ii['width'],ii['height'])
    return out
res={}
cands={}
for sid,(sn,m) in EN.items():
    for ko,en in m.items():
        base=f'{en} {sn}'
        vs=[base, base.replace('::',' '), base.replace('::','_'), base.replace(':',''), base.replace('::',''),base.replace('::',': ').replace(':','')]
        vs=list(dict.fromkeys(vs))
        cands[(sid,ko)]=[f'File:{v}{ext}' for v in vs for ext in ('.png','.webp','.jpg')]+[f'File:{v} Full{ext}' for v in vs for ext in ('.png','.webp')]
allt=sorted({t for v in cands.values() for t in v})
print(len(allt))
I=info(allt)
for k,v in cands.items():
    card=[I[t] for t in v if t in I and ' Full' not in t]
    full=[I[t] for t in v if t in I and ' Full' in t]
    res['|'.join(k)]={'card':card[0] if card else None,'full':full[0] if full else None}
json.dump(res,open('fandom_found.json','w'),ensure_ascii=False,indent=1)
nc=sum(1 for v in res.values() if v['card']); nf=sum(1 for v in res.values() if not v['card'] and v['full'])
print('card',nc,'fullonly',nf,'none',len(res)-nc-nf)
for k,v in res.items():
    if not v['card']: print(k, 'FULL' if v['full'] else 'NONE')
