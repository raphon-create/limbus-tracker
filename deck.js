'use strict';
/* 덱 탭 + 덱 빌더. app.js 보다 먼저 로드되지만, 함수는 데이터 로드 후 app.js 에서 호출됨.
   app.js 의 전역(DATA, isOwned, craft, esc, load, save, rarStr, key, ownMap, shMap)을 사용. */
const LS_DEPLOY='limbus.deploy.v1', LS_DECKS='limbus.decks.v1', LS_BLD='limbus.builder.v1', LS_BUN='limbus.builder.unowned.v1';
const DK=()=>DATA.meta.deck;
const KWS=()=>DK().keywords, SINS=()=>DK().sins;
const kwColor=id=>(KWS().find(k=>k.id===id)||{}).color||'#888';
const sinColor=id=>(SINS().find(k=>k.id===id)||{}).color||'#888';
const cb=i=>(i&&i.combat)||{};
const kwScore=(i,kw)=>((cb(i).kwCount)||{})[kw]||0;
const hasKw=(i,kw)=>(cb(i).kw||[]).includes(kw);
const sinnerById=id=>DATA.sinners.find(s=>s.id===id);
const findId=(s,name)=>name?s.identities.find(i=>i.name===name):null;
function deployN(){const v=Number(load(LS_DEPLOY,DK().deployDefault));return (v>=1&&v<=12)?v:DK().deployDefault}
function setDeploy(v){v=Math.max(1,Math.min(12,Math.round(Number(v))||DK().deployDefault));save(LS_DEPLOY,v);return v}
const cmpRel=(a,b)=>(a.release<b.release)?1:(a.release>b.release)?-1:0;
/* 정렬: 커뮤니티 종합 티어(구간) → 키워드 언급 블록 수 → 등급 → 출시일 */
function cmpFor(kw){return (a,b)=>(tierRank(b)-tierRank(a))||(kwScore(b,kw)-kwScore(a,kw))||(b.rarity-a.rarity)||cmpRel(a,b)}
const cmpGeneral=(a,b)=>(b.rarity-a.rarity)||cmpRel(a,b);

/* ---------- 공통 표시 조각 ---------- */
function kwChips(i,opt={}){
  const c=cb(i); if(!c.skills||!c.skills.length) return '<span class="kc chk">키워드 확인 필요</span>';
  const un=c.kwUnverified||[];
  let h=(c.kw||[]).map(k=>`<span class="kc" style="--c:${kwColor(k)}" title="${esc(k)}: ${esc((c.kwWhere||{})[k]?.join(', ')||'본문 직접 언급 없음')}${un.includes(k)?' · 나무위키 분류에만 있음(확인 필요)':''}">${esc(k)}${opt.count?`<small>${kwScore(i,k)}</small>`:''}${un.includes(k)?'<sup>?</sup>':''}</span>`).join('');
  if(!(c.kw||[]).length) h='<span class="kc gen" title="나무위키 목록에 상태이상 키워드 아이콘 없음">범용·키워드 없음</span>';
  if(opt.sub&&(c.kwSub||[]).length) h+=(c.kwSub).map(k=>`<span class="kc sub" style="--c:${kwColor(k)}" title="부 키워드(wiki.gg 분류에만 있음)">${esc(k)}</span>`).join('');
  return h;
}
function sinChips(i){
  const c=cb(i); if(!c.skills||!c.skills.length) return '<span class="sc chk">죄악 확인 필요</span>';
  let h=c.skills.map(k=>`<span class="sc" style="--c:${sinColor(k.sin)}" title="스킬${k.s} ${esc(k.name)} · ${esc(k.sin)} · ${esc(k.atk||'')} ×${k.amt||'?'}">${k.s}<b>${esc(k.sin)}</b></span>`).join('');
  if(c.defense) h+=`<span class="sc def" style="--c:${sinColor(c.defense.sin)}" title="수비 ${esc(c.defense.name)} · ${esc(c.defense.type||'')} · ${esc(c.defense.sin)}">${esc((c.defense.type||'수비').replace('강화 ','강'))}<b>${esc(c.defense.sin)}</b></span>`;
  if(c.sinStatus==='확인 필요') h+='<span class="sc chk">확인 필요</span>';
  return h;
}
function combatDetail(i){
  const c=cb(i); if(!c.src) return '';
  const src=[c.src.namu?`<a href="${esc(c.src.namu)}" target="_blank" rel="noopener">나무위키</a>`:'',c.src.wikigg?`<a href="${esc(c.src.wikigg)}" target="_blank" rel="noopener">wiki.gg</a>`:'',c.src.fandom?`<a href="${esc(c.src.fandom)}" target="_blank" rel="noopener">Fandom</a>`:''].filter(Boolean).join(' · ');
  const ex=(c.skillsExtra||[]).map(k=>`${k.s?('S'+k.s+' '):''}${esc(k.name)}(${esc(k.sin)})`).join(', ');
  const dx=(c.defenseExtra||[]).map(k=>`${esc(k.name)}(${esc(k.type||'')}·${esc(k.sin)})`).join(', ');
  const ps=(c.passives||[]).map(p=>`${esc(p.kind)} ${esc(p.name)}${p.req?` [${esc(p.req)} ${esc(p.reqN||'')} ${esc(p.reqT||'')}]`:''}`).join(' / ');
  const kwc=Object.entries(c.kwCount||{}).map(([k,v])=>`${esc(k)} ${v}(${esc((c.kwWhere||{})[k].join('·'))})`).join(', ');
  return `<br><b>전투 데이터</b> 키워드 ${esc(c.kwStatus||'')} · 죄악 ${esc(c.sinStatus||'')}${kwc?'<br>키워드 언급 블록: '+kwc:''}${(c.kwSub||[]).length?'<br>부 키워드(wiki.gg 분류): '+esc(c.kwSub.join(', ')):''}${c.defense?`<br>수비: ${esc(c.defense.name)} (${esc(c.defense.type||'')}, ${esc(c.defense.sin)})`:''}${ex?'<br>추가/변형 스킬: '+ex:''}${dx?'<br>추가 수비: '+dx:''}${ps?'<br>'+ps:''}${(c.check||[]).length?'<br><span class="est">⚠ '+c.check.map(esc).join(' / ')+'</span>':''}${c.fandomNote?'<br><span class="note">'+esc(c.fandomNote)+'</span>':''}<br>전투 출처: ${src}`;
}
function thumb(s,i,opt={}){
  if(!i) return `<span class="th none"><span class="thn">${esc(s.name)}</span></span>`;
  const own=isOwned(s,i);
  const t=`${s.name} · ${rarStr(i.rarity)} ${i.name}${own?' (보유)':' (미보유)'}${opt.kw?` · ${opt.kw} 언급 ${kwScore(i,opt.kw)}/6`:''}`;
  return `<span class="th r${i.rarity}${own?'':' un'}${opt.cls?' '+opt.cls:''}" title="${esc(t)}">${i.portrait?`<img src="${esc(i.portrait)}" loading="lazy" decoding="async" alt="" onerror="this.remove()">`:''}<span class="thr">${rarStr(i.rarity)}</span>${opt.ord?`<span class="tho">${opt.ord}</span>`:''}${opt.label!==false?`<span class="thn">${esc(opt.label||s.name)}</span>`:''}</span>`;
}
function availInfo(s,i){
  if(i.upcoming) return {cls:'new',t:'출시 예정'};
  const c=craft(s,i);
  if(c.ok) return {cls:'ok',t:`지금 교환 가능 (파편 ${i.shardCost})`,craft:true};
  if(c.rule) return {cls:'need',t:`교환 가능 시기 · 파편 ${c.need}개 부족`};
  if(i.type==='walpurgis') return {cls:'wal',t:'발푸르기스 한정'};
  if(i.limited) return {cls:'lim',t:'한정/이벤트'};
  if(i.standardPool===true) return {cls:'pool',t:'상시 추출 풀'};
  return {cls:'no',t:i.typeKo||'확인 필요'};
}
function sinTotals(list){const w={},c={};for(const i of list)for(const k of (cb(i).skills||[])){w[k.sin]=(w[k.sin]||0)+(k.amt||1);c[k.sin]=(c[k.sin]||0)+1}return {w,c}}
function sinBar(list,big){
  const {w,c}=sinTotals(list);const tot=Object.values(w).reduce((a,b)=>a+b,0);
  if(!tot) return '<div class="sinbar none">선택된 인격 없음</div>';
  return `<div class="sinbar${big?' big':''}">${SINS().filter(s=>w[s.id]).map(s=>`<i style="flex:${w[s.id]};--c:${s.color}" title="${s.id}: 스킬 수량 가중 ${w[s.id]} (스킬 ${c[s.id]}개)"><b>${s.id} ${w[s.id]}</b></i>`).join('')}</div>`;
}

/* ---------- 덱 계산 ---------- */
function computeDeck(kw){
  const N=deployN(), cmp=cmpFor(kw), slots=[];
  for(const s of DATA.sinners){
    const m=s.identities.filter(i=>hasKw(i,kw)).sort(cmp);
    const own=m.filter(i=>isOwned(s,i)&&!i.upcoming), un=m.filter(i=>!isOwned(s,i));
    slots.push({s,pick:own[0]||null,alts:own.slice(1),un,best:m.find(i=>!i.upcoming)||null});
  }
  const filled=slots.filter(x=>x.pick).sort((a,b)=>cmp(a.pick,b.pick));
  filled.forEach((x,n)=>x.ord=n+1);
  const order=[...filled.map(x=>x.s.id),...slots.filter(x=>!x.pick).map(x=>x.s.id)];
  const deployed=filled.slice(0,N).map(x=>x.pick);
  const up=[];
  for(const x of slots)for(const i of x.un){
    if(!x.pick) up.push({s:x.s,i,tag:'완성'});
    else if(cmp(i,x.pick)<0&&!i.upcoming) up.push({s:x.s,i,tag:'강화'});
  }
  up.forEach(u=>u.a=availInfo(u.s,u.i));
  up.sort((a,b)=>(!!b.a.craft-!!a.a.craft)||((a.tag==='완성'?0:1)-(b.tag==='완성'?0:1))||cmp(a.i,b.i));
  return {kw,slots,filled,order,deployed,up,N};
}
function deckToBuilder(D){return {name:`${D.kw} 덱`,order:D.order.slice(),picks:Object.fromEntries(D.slots.map(x=>[x.s.id,x.pick?x.pick.name:null])),from:D.kw}}

/* ---------- 덱 탭 ---------- */
function deployCtl(id){
  const N=deployN();
  return `<div class="dctl"><label>출전 인원 <input type="number" min="1" max="12" id="${id}" value="${N}"></label>
   ${DK().deployPresets.map(p=>`<button class="chip${p===N?' on':''}" data-deploy="${p}">${p}명</button>`).join('')}
   <span class="note">기본 ${DK().deployDefault}명 = 현행 거울 던전 최대 필드 인원</span></div>`;
}
function deployInfo(){
  return `<details class="more dinfo"><summary>출전 인원·출전 순서 규칙 (출처)</summary><div><ul class="rules">${DK().deployNote.map(t=>`<li>${esc(t)}</li>`).join('')}</ul>
  출처: ${DK().deploySources.map(s=>`<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.name)}</a>`).join(' · ')}</div></details>`;
}
function renderDecks(){
  const el=document.getElementById('deckView'); const N=deployN();
  const decks=KWS().map(k=>computeDeck(k.id));
  let h=metaDeckSection()+`<section class="panel"><h2>키워드 덱 <span class="note">자동 구성</span></h2>${deployCtl('deployIn')}
   <div class="dsum">${decks.map(D=>`<a class="dsb" href="#deck-${esc(D.kw)}" data-jump="${esc(D.kw)}" style="--c:${kwColor(D.kw)}"><b>${esc(D.kw)}</b><span class="${D.filled.length>=N?'off':'est'}">${D.filled.length}/12</span><i style="width:${D.filled.length/12*100}%"></i></a>`).join('')}</div>
   <p class="note">숫자 = 해당 키워드 인격을 보유한 수감자 수 / 12 · 출전 ${N}명 기준으로 충족 여부 표시. 픽 정렬: 커뮤니티 종합 티어 → ${esc(DK().sortRule)}<br>${esc(DK().kwRule)}</p>${deployInfo()}</section>`;
  for(const D of decks) h+=deckCard(D);
  el.innerHTML=h;
}
function deckCard(D){
  const N=D.N, ok=D.filled.length>=N, col=kwColor(D.kw);
  const slots=D.slots.map(x=>{
    if(x.pick){
      return `<div class="slot${x.ord<=N?' dep':' bk'}">
        <div class="sn">${esc(x.s.name)}<span class="ordb">${x.ord<=N?x.ord+'번 출전':'후보 '+x.ord}</span></div>
        ${thumb(x.s,x.pick,{kw:D.kw,label:false})}
        <div class="pn" title="${esc(x.pick.name)}">${esc(x.pick.name)}</div>
        <div class="ps">${tierBadge(x.pick,{empty:true})}<span class="kc" style="--c:${col}">${esc(D.kw)}<small>${kwScore(x.pick,D.kw)}/6</small></span></div>
        ${x.best&&x.best!==x.pick?`<div class="subl" title="이 자리의 최고 티어 ${esc(x.best.name)}(${esc(x.best.tier?x.best.tier.t:'-')})는 미보유 → 보유 인격으로 대체 중">대체 ← ${esc(x.best.name)} ${tierBadge(x.best)}</div>`:''}
        ${x.alts.length?`<div class="alts" title="다른 보유 후보">${x.alts.map(i=>thumb(x.s,i,{kw:D.kw,label:false,cls:'mini'})).join('')}</div>`:''}
        ${x.un.length?`<div class="unc">미보유 ${x.un.length}</div>`:''}
      </div>`;
    }
    return `<div class="slot vac"><div class="sn">${esc(x.s.name)}<span class="ordb no">보유 없음</span></div>
      ${x.un.length?x.un.map(i=>{const a=availInfo(x.s,i);return `<div class="cand">${thumb(x.s,i,{kw:D.kw,label:false,cls:'mini'})}<div><div class="cn">${rarStr(i.rarity)} ${esc(i.name)}</div><span class="b ${a.cls}">${esc(a.t)}</span>${a.craft||a.cls==='need'?'':`<div class="cx">${esc((i.next||'').slice(0,60))}</div>`}</div></div>`}).join(''):'<div class="note">이 키워드 인격 없음</div>'}
    </div>`;
  }).join('');
  const up=D.up.length?`<ul class="uplist">${D.up.map(u=>`<li class="${u.a.craft?'cr':''}"><span class="b ${u.tag==='완성'?'fill':'upg'}">${u.tag}</span> ${esc(u.s.name)} · ${rarStr(u.i.rarity)} ${esc(u.i.name)} <span class="kc" style="--c:${col}">${esc(D.kw)}<small>${kwScore(u.i,D.kw)}/6</small></span> <span class="b ${u.a.cls}">${esc(u.a.t)}</span></li>`).join('')}</ul>`:'<p class="note">해당 없음 — 이 키워드의 미보유 인격이 없습니다.</p>';
  return `<section class="panel deck" id="deck-${esc(D.kw)}" style="--c:${col}">
   <div class="dhead"><h2><span class="kwd">${esc(D.kw)}</span> 덱</h2>
     <div class="comp ${ok?'ok':'no'}">보유 매칭 수감자 <b>${D.filled.length}</b>/12 · 출전 ${N}명 ${ok?'<span class="off">충족</span>':`<span class="est">${N-D.filled.length}명 부족</span>`}</div>
     <button class="btn" data-open="${esc(D.kw)}">빌더로 열기 ▶</button></div>
   <div class="dsin"><span class="note">출전 ${Math.min(N,D.filled.length)}명 죄악 분포 (스킬 수량 가중)</span>${sinBar(D.deployed)}</div>
   <div class="slots">${slots}</div>
   <h3>이게 있으면 덱이 완성/강화</h3><p class="note">완성 = 빈 자리를 채움 · 강화 = 현재 픽보다 ${esc(D.kw)} 언급 블록 수가 많음 · 초록 테두리 = 현재 파편으로 지금 교환 가능</p>${up}
  </section>`;
}

/* ---------- 덱 빌더 ---------- */
const canon=()=>DATA.sinners.map(s=>s.id);
function defaultPick(s){const o=s.identities.filter(i=>isOwned(s,i)&&!i.upcoming).sort(cmpGeneral);return (o.find(i=>i.type==='base')||o[0]||{}).name||null}
function blankDeck(){return {name:'새 덱',order:canon(),picks:Object.fromEntries(DATA.sinners.map(s=>[s.id,defaultPick(s)]))}}
function normDeck(d){
  const ids=canon(); const ord=(d.order||[]).filter(x=>ids.includes(x)); for(const x of ids) if(!ord.includes(x)) ord.push(x);
  const picks={}; for(const s of DATA.sinners){const n=(d.picks||{})[s.id]; picks[s.id]=findId(s,n)?n:null}
  return {name:String(d.name||'이름 없는 덱').slice(0,40),order:[...new Set(ord)],picks,curId:d.curId||null,from:d.from||null};
}
let B=null;
function bLoad(){B=normDeck(load(LS_BLD,null)||blankDeck())}
function bSave(){save(LS_BLD,B)}
const decksAll=()=>load(LS_DECKS,[]);
function openInBuilder(d){B=normDeck(d);B.curId=null;bSave();st.tab='builder';save(LS_TAB,st.tab);history.replaceState(null,'','#builder');renderAll();window.scrollTo({top:0})}
function bMembers(){const N=deployN();return B.order.map((id,n)=>{const s=sinnerById(id);const i=findId(s,B.picks[id]);return {s,i,n,dep:n<N}})}
function renderBuilder(){
  if(!B) bLoad();
  const el=document.getElementById('builderView'); const N=deployN(); const inc=!!load(LS_BUN,false);
  const saved=decksAll(); const M=bMembers(); const dep=M.filter(m=>m.dep&&m.i); const bk=M.filter(m=>!m.dep&&m.i);
  const rows=M.map(m=>{
    const cmpT=(a,b)=>(tierScore(b)-tierScore(a))||cmpGeneral(a,b);
    const s=m.s, own=s.identities.filter(i=>isOwned(s,i)&&!i.upcoming).sort(cmpT), un=s.identities.filter(i=>!isOwned(s,i)).sort(cmpT);
    const cur=m.i; const curOwn=cur?isOwned(s,cur):false;
    const opt=i=>`<option value="${esc(i.name)}"${cur&&cur.name===i.name?' selected':''}>${i.tier?'['+esc(i.tier.t)+'] ':''}${rarStr(i.rarity)} ${esc(i.name)}${(cb(i).kw||[]).length?' ['+esc(cb(i).kw.join('·'))+']':''}${isOwned(s,i)?'':' (미보유)'}</option>`;
    const unList=inc?un:(cur&&!curOwn?[cur]:[]);
    const warn=!cur?'<span class="wbad">픽 없음</span>':(!curOwn?'<span class="wbad">미보유</span>':'');
    return `<div class="brow${m.dep?' dep':' bk'}${warn?' warnrow':''}">
      <div class="bo"><span class="num">${m.n+1}</span><span class="lab">${m.dep?'출전':'후보'}</span>
        <button class="mv" data-mv="-1" data-sid="${s.id}" ${m.n===0?'disabled':''} title="위로">▲</button><button class="mv" data-mv="1" data-sid="${s.id}" ${m.n===11?'disabled':''} title="아래로">▼</button></div>
      ${thumb(s,cur,{label:false,cls:'mini2'})}
      <div class="bm"><div class="bs">${esc(s.name)} ${cur?tierBadge(cur,{empty:true}):''} ${warn}</div>
        <select data-pick="${s.id}"><option value="">— 선택 안 함 —</option><optgroup label="보유">${own.map(opt).join('')}</optgroup>${unList.length?`<optgroup label="미보유">${unList.map(opt).join('')}</optgroup>`:''}</select>
        <div class="bchips">${cur?kwChips(cur,{count:true,sub:true})+' '+sinChips(cur):''}</div></div>
      <div class="bord"><label title="출전 순서 직접 지정">순서 <input type="number" min="1" max="12" value="${m.n+1}" data-ord="${s.id}"></label></div>
    </div>`;
  }).join('');
  // live summary
  const depI=dep.map(m=>m.i);
  const kwRows=KWS().map(k=>{const mem=depI.filter(i=>hasKw(i,k.id));const sub=depI.filter(i=>(cb(i).kwSub||[]).includes(k.id));const blk=depI.reduce((a,i)=>a+kwScore(i,k.id),0);
    return `<tr><td><span class="kc" style="--c:${k.color}">${k.id}</span></td><td class="cnum"><b>${mem.length}</b>/${N}</td><td class="cnum">${blk}</td><td class="cnum">${sub.length||''}</td><td><div class="minibar"><i style="width:${mem.length/Math.max(N,1)*100}%;background:${k.color}"></i></div></td></tr>`}).join('');
  const {w,c}=sinTotals(depI);
  const sinRows=SINS().map(s=>`<tr><td><span class="sc" style="--c:${s.color}"><b>${s.id}</b></span></td><td class="cnum"><b>${w[s.id]||0}</b></td><td class="cnum">${c[s.id]||0}</td><td class="cnum">${depI.filter(i=>cb(i).defense&&cb(i).defense.sin===s.id).length||''}</td></tr>`).join('');
  const warns=[];
  M.forEach(m=>{if(!m.i) warns.push(`${m.s.name}: 선택된 인격 없음${m.dep?' (출전 자리)':''}`);else if(!isOwned(m.s,m.i)) warns.push(`${m.s.name}: ${m.i.name} 미보유${m.dep?' (출전 자리)':''} — ${availInfo(m.s,m.i).t}`)});
  if(dep.length<N) warns.push(`출전 자리 ${N}개 중 ${dep.length}명만 인격이 선택됨`);
  const chk=depI.filter(i=>(cb(i).check||[]).length).map(i=>i.name);
  el.innerHTML=`<section class="panel"><h2>덱 빌더</h2>
    <div class="bbar">
      <label>저장된 덱 <select id="bSel"><option value="">(작업 중 — 저장 안 됨)</option>${saved.map(d=>`<option value="${esc(d.id)}"${B.curId===d.id?' selected':''}>${esc(d.name)}</option>`).join('')}</select></label>
      <label>이름 <input type="text" id="bName" value="${esc(B.name)}" maxlength="40"></label>
      <button class="btn" id="bSaveBtn">${B.curId?'저장(덮어쓰기)':'저장'}</button>
      <button class="ghost" id="bSaveAs">새 이름으로 저장</button>
      <button class="ghost" id="bRename" ${B.curId?'':'disabled'}>이름 변경</button>
      <button class="ghost" id="bDel" ${B.curId?'':'disabled'}>삭제</button>
      <button class="ghost" id="bNew">새 덱(초기화)</button>
    </div>
    <div class="bbar">${deployCtl('deployIn2')}
      <button class="chip toggle${inc?' on':''}" id="bInc">미보유 인격도 선택지에 표시</button>
      <label>키워드 기준 자동 순서 <select id="bSort"><option value="">선택…</option>${KWS().map(k=>`<option>${k.id}</option>`).join('')}</select></label>
      <label>메타 덱 불러오기 <select id="bMeta"><option value="">선택…</option>${(DATA.meta.metaDecks||[]).map(d=>`<option value="${esc(d.id)}">${esc(d.t)} · ${esc(d.name)}</option>`).join('')}</select></label>
      <label>키워드 덱 불러오기 <select id="bFrom"><option value="">선택…</option>${KWS().map(k=>`<option>${k.id}</option>`).join('')}</select></label>
    </div>
    <div class="bbar io"><textarea id="bIO" rows="2" placeholder="내보내기 결과가 여기 표시됩니다. 공유받은 덱 코드/JSON 을 붙여넣고 [가져오기]를 누르세요."></textarea>
      <div class="iob"><button class="btn" id="bExp">코드 복사</button><button class="ghost" id="bExpJ">JSON 복사</button><button class="ghost" id="bImp">가져오기</button></div></div>
    <div class="note" id="bMsg">${B.from?`「${esc(B.from)} 덱」에서 불러옴 · `:''}출전 = 순서 1~${N}번, 나머지는 후보(체인 전투에서 교체 투입, 서포트 패시브 제공). 순서는 ▲▼ 또는 숫자로 변경.</div>
    ${deployInfo()}
  </section>
  <div class="blayout"><section class="panel brows">${rows}</section>
  <aside class="panel bsum">${(()=>{const T=teamTier(depI);return T?`<div class="ttier"><span class="note">출전 평균 티어</span> <span class="tb ${tierCls(T.t)}" title="출전 인격 ${T.n}명의 커뮤니티 종합 점수 평균 ${T.avg} (합계 ${T.total}) · ${esc(TM().asOf)} 기준 참고용">${T.t}</span> <b>${T.avg}</b><span class="note">점 · 합계 ${T.total} · 평가 ${T.n}/${depI.length}명 <a href="#" data-tsrc="1">출처·기준</a></span></div>`:''})()}<h3>출전 ${dep.length}/${N}명 키워드</h3>
    <table class="st"><tr><th>키워드</th><th title="주 키워드 보유 출전 인원">인원</th><th title="출전 인원의 해당 키워드 언급 블록 합(인당 최대 6)">블록</th><th title="부 키워드(wiki.gg 분류)로만 가진 인원">부</th><th></th></tr>${kwRows}</table>
    <h3>출전 죄악 속성</h3>${sinBar(depI,true)}
    <table class="st"><tr><th>죄악</th><th title="스킬 1·2·3 수량 가중(3/2/1)">가중</th><th title="스킬 1·2·3 개수">스킬</th><th title="수비 스킬">수비</th></tr>${sinRows}</table>
    <h3>경고</h3>${warns.length?`<ul class="wl">${warns.map(t=>`<li>${esc(t)}</li>`).join('')}</ul>`:'<p class="note off">모든 수감자가 보유 인격으로 선택됨</p>'}
    ${chk.length?`<p class="note est">데이터 확인 필요 포함: ${chk.map(esc).join(', ')}</p>`:''}
    <h3>후보 (서포트 패시브)</h3>${bk.length?`<ul class="wl sp">${bk.map(m=>{const sp=(cb(m.i).passives||[]).find(p=>p.kind==='서포트 패시브');return `<li>${esc(m.s.name)} · ${esc(m.i.name)}${sp?` — ${esc(sp.name)}${sp.req?` [${esc(sp.req)} ${esc(sp.reqN||'')} ${esc(sp.reqT||'')}]`:''}`:''}</li>`}).join('')}</ul>`:'<p class="note">없음</p>'}
  </aside></div>`;
}
/* 덱 코드: LCD1~출전인원~순서(16진 12자)~픽(수감자별 인격 인덱스 36진, '.' 구분, '-'=없음)~이름(base64url)
   인격 인덱스 = (출시일, 이름) 정렬 순서 → 새 인격이 추가돼도 기존 인덱스 유지 */
const stableList=s=>[...s.identities].sort((a,b)=>(a.release<b.release?-1:a.release>b.release?1:(a.name<b.name?-1:a.name>b.name?1:0)));
const b64e=t=>{const u=new TextEncoder().encode(t);let s='';u.forEach(x=>s+=String.fromCharCode(x));return btoa(s).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'')};
const b64d=t=>{t=t.replace(/-/g,'+').replace(/_/g,'/');while(t.length%4)t+='=';const s=atob(t);return new TextDecoder().decode(Uint8Array.from(s,c=>c.charCodeAt(0)))};
function encodeDeck(d){
  const ids=canon();
  const ord=d.order.map(id=>ids.indexOf(id).toString(16)).join('');
  const p=DATA.sinners.map(s=>{const ix=stableList(s).findIndex(i=>i.name===d.picks[s.id]);return ix<0?'-':ix.toString(36)}).join('.');
  return `LCD1~${deployN()}~${ord}~${p}~${b64e(d.name)}`;
}
function decodeDeck(t){
  t=t.trim();
  if(t.startsWith('LCD1~')){
    const [,n,ord,p,nm]=t.split('~'); const ids=canon();
    const order=[...ord].map(c=>ids[parseInt(c,16)]).filter(Boolean);
    const px=p.split('.'); const picks={};
    DATA.sinners.forEach((s,k)=>{const v=px[k];picks[s.id]=(!v||v==='-')?null:(stableList(s)[parseInt(v,36)]||{}).name||null});
    return {deck:{name:nm?b64d(nm):'가져온 덱',order,picks},deploy:Number(n)};
  }
  const j=JSON.parse(t); if(!j||typeof j!=='object'||!j.picks) throw new Error('형식 오류');
  return {deck:{name:j.name,order:j.order,picks:j.picks},deploy:Number(j.deploy)};
}
async function copyText(t){
  try{await navigator.clipboard.writeText(t);return true}catch(e){
    const ta=document.getElementById('bIO');ta.value=t;ta.focus();ta.select();try{return document.execCommand('copy')}catch(_){return false}}
}
function bMsg(t){const m=document.getElementById('bMsg');if(m){m.textContent=t;m.classList.add('flash');setTimeout(()=>m.classList.remove('flash'),900)}}
function moveSid(sid,to){const o=B.order.filter(x=>x!==sid);to=Math.max(0,Math.min(11,to));o.splice(to,0,sid);B.order=o;bSave();renderBuilder()}
function deckEvents(){
  document.addEventListener('click',async e=>{
    const dp=e.target.closest('[data-deploy]'); if(dp){setDeploy(dp.dataset.deploy);renderAll();return}
    const op=e.target.closest('[data-open]'); if(op){openInBuilder(deckToBuilder(computeDeck(op.dataset.open)));return}
    const jp=e.target.closest('[data-jump]'); if(jp){e.preventDefault();document.getElementById('deck-'+jp.dataset.jump)?.scrollIntoView({behavior:'smooth'});return}
    const mv=e.target.closest('[data-mv]'); if(mv){moveSid(mv.dataset.sid,B.order.indexOf(mv.dataset.sid)+Number(mv.dataset.mv));return}
    const id=e.target.id;
    if(id==='bInc'){save(LS_BUN,!load(LS_BUN,false));renderBuilder();return}
    if(id==='bNew'){if(confirm('작업 중인 덱을 기본(보유 인격, 수감자 기본 순서)으로 초기화할까요? 저장된 덱은 지워지지 않습니다.')){B=normDeck(blankDeck());bSave();renderBuilder()}return}
    if(id==='bSaveBtn'||id==='bSaveAs'){
      const L=decksAll(); let name=document.getElementById('bName').value.trim()||B.name;
      if(id==='bSaveAs'||!B.curId){ if(id==='bSaveAs'){const n=prompt('새 덱 이름',name+(B.curId?' (복사)':''));if(n===null)return;name=n.trim()||name}
        const nid='d'+Date.now().toString(36); L.push({id:nid,name,order:B.order,picks:B.picks,deploy:deployN(),savedAt:new Date().toISOString()}); B.curId=nid; }
      else { const d=L.find(x=>x.id===B.curId); if(d) Object.assign(d,{name,order:B.order,picks:B.picks,deploy:deployN(),savedAt:new Date().toISOString()}); }
      B.name=name; save(LS_DECKS,L); bSave(); renderBuilder(); bMsg(`「${name}」 저장됨 (이 브라우저 localStorage)`); return}
    if(id==='bRename'&&B.curId){const L=decksAll();const d=L.find(x=>x.id===B.curId);if(!d)return;const n=prompt('덱 이름 변경',d.name);if(n===null||!n.trim())return;d.name=n.trim();B.name=d.name;save(LS_DECKS,L);bSave();renderBuilder();return}
    if(id==='bDel'&&B.curId){const L=decksAll();const d=L.find(x=>x.id===B.curId);if(!d||!confirm(`저장된 덱 「${d.name}」 을(를) 삭제할까요? (작업 중인 내용은 남습니다)`))return;save(LS_DECKS,L.filter(x=>x.id!==B.curId));B.curId=null;bSave();renderBuilder();return}
    if(id==='bExp'||id==='bExpJ'){
      const t=id==='bExp'?encodeDeck(B):JSON.stringify({v:1,name:B.name,deploy:deployN(),order:B.order,picks:B.picks});
      document.getElementById('bIO').value=t; const ok=await copyText(t); bMsg(ok?'클립보드에 복사됨 — 붙여넣어 공유하세요':'자동 복사 실패 — 위 칸의 내용을 직접 복사하세요'); return}
    if(id==='bImp'){const t=document.getElementById('bIO').value;if(!t.trim()){bMsg('붙여넣은 내용이 없습니다');return}
      try{const r=decodeDeck(t);B=normDeck(r.deck);B.curId=null;if(r.deploy>=1&&r.deploy<=12)setDeploy(r.deploy);bSave();renderAll();bMsg(`「${B.name}」 가져옴 — 저장하려면 [저장]`)}catch(err){bMsg('가져오기 실패: 덱 코드(LCD1~…) 또는 JSON 형식이 아닙니다')}return}
  });
  document.addEventListener('change',e=>{
    const t=e.target;
    if(t.id==='deployIn'||t.id==='deployIn2'){setDeploy(t.value);renderAll();return}
    if(t.dataset.pick){B.picks[t.dataset.pick]=t.value||null;bSave();renderBuilder();return}
    if(t.dataset.ord){moveSid(t.dataset.ord,Number(t.value)-1);return}
    if(t.id==='bName'){B.name=t.value.trim()||B.name;bSave();return}
    if(t.id==='bSel'){if(!t.value){B.curId=null;bSave();renderBuilder();return}const d=decksAll().find(x=>x.id===t.value);if(d){B=normDeck(d);B.curId=d.id;if(d.deploy)setDeploy(d.deploy);bSave();renderAll()}return}
    if(t.id==='bSort'&&t.value){const kw=t.value,cmp=cmpFor(kw);const M=B.order.map(id=>({id,i:findId(sinnerById(id),B.picks[id])}));
      M.sort((a,b)=>{const ha=a.i&&hasKw(a.i,kw),hb=b.i&&hasKw(b.i,kw);if(ha!==hb)return hb-ha;if(ha)return cmp(a.i,b.i);return 0});B.order=M.map(m=>m.id);bSave();renderBuilder();bMsg(`${kw} 인격을 앞으로 정렬 (언급 블록 수 → 등급 → 출시일)`);return}
    if(t.id==='bFrom'&&t.value){openInBuilder(deckToBuilder(computeDeck(t.value)));return}
  });
}
