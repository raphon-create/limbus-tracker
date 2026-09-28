import json,os,re,hashlib,cv2,numpy as np
from PIL import Image, ImageDraw, ImageFont
exec(open('en_map.py').read())
nb=json.load(open('namu_base_imgs.json')); fd=json.load(open('fandom_found.json'))
OVR=json.load(open('crop_overrides.json')) if os.path.exists('crop_overrides.json') else {}
casc=cv2.CascadeClassifier('lbpcascade_animeface.xml')
d=json.load(open('/workspace/limbus-site/data.json'))
W,H=240,370  # ~332x512 ratio
res={}
def slug(sid,name):
    en=EN[sid][1].get(name,name)
    s=re.sub(r'[^A-Za-z0-9]+','_',en).strip('_').lower()
    return f'{sid}_{s}'
for s in d['sinners']:
    for i in s['identities']:
        k=f"{s['id']}|{i['name']}"; out=f"img/{slug(s['id'],i['name'])}.webp"
        f=fd.get(k,{}); n=nb.get(k,{})
        mode=OVR.get(k,{}).get('mode')
        if f.get('card') and mode!='namu':
            im=Image.open(f['file']).convert('RGB')
            im=im.resize((W,round(im.height*W/im.width)),Image.LANCZOS)
            if im.height!=H: # center/top crop to ratio
                if im.height>H: im=im.crop((0,0,W,H))
                else: im=im.resize((W,H),Image.LANCZOS)
            src={'portraitSource':'fandom','portraitSourceUrl':f['card'][1],'portraitSourcePage':'https://limbuscompany.fandom.com/wiki/'+f['card'][0].replace(' ','_'),'portraitNote':'공식 인격 카드 이미지(동기화 전)'}
        elif n.get('file'):
            im=Image.open(n['file']).convert('RGB'); w,h=im.size
            cw=round(h*332/512)
            if k in OVR and 'cx' in OVR[k]: cx=OVR[k]['cx']*w; how='manual'
            else:
                g=cv2.cvtColor(np.array(im),cv2.COLOR_RGB2GRAY); g=cv2.equalizeHist(g)
                faces=casc.detectMultiScale(g,1.08,4,minSize=(int(h*0.08),int(h*0.08)))
                if len(faces):
                    x,y,fw,fh=max(faces,key=lambda r:r[2]*r[3]); cx=x+fw/2; how='face'
                else: cx=w/2; how='center'
            x0=int(max(0,min(w-cw,cx-cw/2)))
            im=im.crop((x0,0,x0+cw,h)).resize((W,H),Image.LANCZOS)
            src={'portraitSource':'namu','portraitSourceUrl':n['img'][0],'portraitSourcePage':i['source'].split(' ; ')[-1]+'#'+n['anchor'],'portraitNote':f'나무위키 동기화 전 일러스트를 카드 비율로 크롭({how})'}
            src['_how']=how
        else:
            res[k]=None; continue
        im.save('/workspace/limbus-site/'+out,'WEBP',quality=80,method=6)
        src['portrait']=out
        res[k]=src
json.dump(res,open('portraits.json','w'),ensure_ascii=False,indent=1)
from collections import Counter
print(Counter((v or {}).get('_how',(v or {}).get('portraitSource','MISSING')) for v in res.values()))
