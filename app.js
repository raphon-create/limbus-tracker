'use strict';
const LS_OWN='limbus.owned.v1', LS_SH='limbus.shards.v1', LS_TH='limbus.thread.v1', LS_TAB='limbus.tab.v1';
let DATA=null;
const st={tab:'all',own:'all',rar:new Set([1,2,3]),kind:'all',kw:'all',craft:false,q:''};
const VIEW_TABS=['deck','builder'];
const load=(k,d)=>{try{return JSON.parse(localStorage.getItem(k))??d}catch(e){return d}};
const save=(k,v)=>localStorage.setItem(k,JSON.stringify(v));
let ownMap=load(LS_OWN,{}), shMap=load(LS_SH,{});
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const today=()=>{const d=new Date();const k=new Date(d.getTime()+(d.getTimezoneOffset()+540)*60000);return k.toISOString().slice(0,10)}; // KST date
const key=(s,i)=>s.id+'|'+i.name;
const isOwned=(s,i)=>{const k=key(s,i);if(k in ownMap)return ownMap[k];if(i.type==='base')return true;return s.screenshot?!!i.ownedFromScreenshot:false};
const shards=s=>{const v=shMap[s.id];return (v===undefined||v===null||v==='')?s.shardsDefault:Number(v)};
const rarStr=r=>'0'.repeat(r);
function walActive(){const t=today();return (DATA.schedule.walpurgisActive||[]).some(w=>t>=w.start.slice(0,10)&&t<=w.end.slice(0,10))}
// craft status for an identity: {rule:true/false, ok:bool, need:number, text}
function craft(s,i){
  if(!i.shardCost) return {rule:false,ok:false,text:'교환 대상 아님'};
  let rule=!!i.craftNow;
  if(i.craftFromDate) rule = today()>=i.craftFromDate && (i.season===DATA.meta.currentSeason);
  if(i.craftWindow==='walpurgis') rule=walActive();
  if(i.upcoming) rule=false;
  const have=shards(s);
  if(!rule) return {rule:false,ok:false,text:'현재 교환 불가'};
  if(have>=i.shardCost) return {rule:true,ok:true,text:`지금 교환 가능 (파편 ${i.shardCost})`};
  return {rule:true,ok:false,need:i.shardCost-have,text:`교환 가능 시기 · 파편 ${i.shardCost-have}개 부족`};
}
function nextHtml(i){
  let t=esc(i.next||'확인 필요');
  if(i.nextEstimate) t=t.replace(/(다음 예상|예상)/,'<span class="tag-est">예상</span>$1');
  if(/^공식:/.test(i.next||'')) t='<span class="tag-off">공식</span>'+t.replace(/^공식:\s*/,'');
  return t;
}
function card(s,i){
  const own=isOwned(s,i), c=own?null:craft(s,i);
  const cls=['card','r'+i.rarity]; if(i.type==='walpurgis')cls.push('wal'); if(!own)cls.push('unowned'); if(c&&c.ok)cls.push('craftable');
  const b=[];
  if(i.upcoming) b.push('<span class="b new">출시 예정</span>');
  if(i.standardPool===true) b.push('<span class="b pool">상시 추출 풀</span>');
  if(i.type==='walpurgis') b.push(`<span class="b wal">발푸르기스 ${i.wn?('제'+i.wn+'회'):''} 한정</span>`);
  else if(i.limited) b.push('<span class="b lim">한정/이벤트</span>');
  b.push(`<span class="b">${esc(i.typeKo)}</span>`);
  if(i.equipped && own) b.push('<span class="b eq">장착 중</span>');
  if(!own && c){ b.push(c.ok?`<span class="b ok">${esc(c.text)}</span>`:(c.rule?`<span class="b need">${esc(c.text)}</span>`:`<span class="b no">${esc(c.text)}</span>`)); }
  const ph=`<div class="ph"><span class="phs">${esc(s.name)}</span><span class="phn">${esc(i.name)}</span><span class="phx">이미지 없음</span></div>`;
  const pic=i.portrait?`<img src="${esc(i.portrait)}" alt="${esc(s.name+' '+i.name)}" loading="lazy" decoding="async" onerror="this.outerHTML=this.nextElementSibling.innerHTML">`+`<template>${ph}</template>`:ph;
  return `<div class="${cls.join(' ')}">
   <div class="pf" data-k="${esc(key(s,i))}" title="${esc(s.name+' · '+i.name)}${i.type==='base'?'':' (클릭: 보유 전환)'}">${pic}
     <span class="pr">${rarStr(i.rarity)}</span>${own?'<span class="ribbon on">보유</span>':`<span class="ribbon">${i.upcoming?'출시 예정':'미보유'}</span>`}</div>
   <div class="cbody">
   <div class="chead"><div><span class="rar">${rarStr(i.rarity)}</span> <span class="sinner">${esc(s.name)}</span>
     <div class="nm">${esc(i.name)}</div></div>
     <button class="own ${own?'yes':''}" data-k="${esc(key(s,i))}" data-o="${own?1:0}" ${i.type==='base'?'disabled title="기본 지급"':''}>${own?'✓ 보유':'미보유'}</button></div>
   <div class="badges">${b.join('')}</div>
   <div class="kwrow">${kwChips(i,{sub:true})}</div><div class="kwrow">${sinChips(i)}</div>
   <div class="kv"><b>출시</b>${esc(i.release)} · 시즌 ${esc(i.seasonLabel)}</div>
   ${own?'':`<div class="kv"><b>획득</b>${esc(i.obtainRaw)}</div>
   <div class="kv"><b>교환</b>${i.shardCost?('파편 '+i.shardCost+' · '):''}${esc(i.craftNote)}</div>
   <div class="kv"><b>다음 기회</b>${nextHtml(i)}</div>`}
   <details class="more"><summary>세부/출처</summary><div>${own&&i.obtainRaw?('획득: '+esc(i.obtainRaw)+'<br>'):''}특성 키워드: ${esc(i.keywords)}${i.ocrRead?('<br>스크린샷 판독: '+esc(i.ocrRead)):''}<br>출처: ${i.source.split(' ; ').map(u=>`<a href="${esc(u)}" target="_blank" rel="noopener">${esc(decodeURI(u).slice(0,60))}</a>`).join(' , ')}${i.portrait?`<br>초상화: <a href="${esc(i.portraitSourcePage||i.portraitSourceUrl)}" target="_blank" rel="noopener">${i.portraitSource==='fandom'?'Limbus Company Fandom Wiki':i.portraitSource==='namu'?'나무위키':'출처'}</a> (${esc(i.portraitNote||'')})`:'<br>초상화: 없음'}${combatDetail(i)}</div></details>
   </div>
  </div>`;
}
function stats(s){const ids=s.identities.filter(i=>!i.upcoming);const o=ids.filter(i=>isOwned(s,i)).length;
  const cr=ids.filter(i=>!isOwned(s,i)&&craft(s,i).ok);return {total:ids.length,owned:o,un:ids.length-o,cr}}
function renderTabs(){
  const t=document.getElementById('tabs');
  let h=`<button class="tab ${st.tab==='all'?'on':''}" data-t="all">전체</button>`;
  for(const s of DATA.sinners){const x=stats(s);h+=`<button class="tab ${st.tab===s.id?'on':''}" data-t="${s.id}">${esc(s.name)}<span class="cnt">${x.owned}/${x.total}</span></button>`}
  h+=`<span class="tabsep"></span><button class="tab vt ${st.tab==='deck'?'on':''}" data-t="deck">덱</button><button class="tab vt ${st.tab==='builder'?'on':''}" data-t="builder">덱 빌더</button>`;
  t.innerHTML=h;
}
function renderSummary(){
  const el=document.getElementById('summary');
  if(st.tab==='all'){
    let h='<h2>수감자별 요약</h2><div class="sumgrid">';
    let T=0,O=0,C=0;
    for(const s of DATA.sinners){const x=stats(s);T+=x.total;O+=x.owned;C+=x.cr.length;
      h+=`<div class="sbox" data-t="${s.id}"><div class="t"><span>${esc(s.name)}</span><span>${x.owned} / ${x.total}</span></div>
      <div class="bar"><i style="width:${(x.owned/x.total*100).toFixed(0)}%"></i></div>
      <div class="s">미보유 ${x.un} · 파편 ${shards(s)}</div><div class="c">${x.cr.length?('지금 교환 가능: '+x.cr.map(i=>esc(i.name)).join(', ')):'<span class="note">지금 교환 가능한 미보유 없음</span>'}</div></div>`}
    h+=`</div><p class="note">전체 보유 ${O} / ${T} (미보유 ${T-O}) · 지금 파편으로 교환 가능한 미보유 인격 ${C}개 · 기준일 ${today()} (KST) · 현재 ${esc(DATA.meta.currentSeasonName)}</p>`;
    el.innerHTML=h;
  }else{
    const s=DATA.sinners.find(x=>x.id===st.tab);const x=stats(s);
    const up=s.identities.filter(i=>i.upcoming);
    const rules=s.identities.filter(i=>!isOwned(s,i)&&craft(s,i).rule);
    el.innerHTML=`<h2>${esc(s.name)}</h2><div class="sinfo">
      <div><div class="note">보유 / 전체</div><div class="big">${x.owned} / ${x.total}</div></div>
      <div><div class="note">미보유</div><div class="big">${x.un}</div></div>
      <div><label class="note">자아 파편(인격 조각)<br><input type="number" min="0" id="shIn" value="${shards(s)}"></label></div>
      <div class="note">기본값 ${s.shardsDefault} (파편::끈 교환기 스크린샷 기준)<br>2성 150 · 3성 400</div></div>
      <h3>지금 교환 가능한 미보유 인격</h3>
      ${rules.length?('<ul class="craftlist">'+rules.map(i=>{const c=craft(s,i);return `<li>${rarStr(i.rarity)} ${esc(i.name)} — ${c.ok?'<span class="off">가능</span>':'<span class="est">'+c.need+'개 부족</span>'} (파편 ${i.shardCost})</li>`}).join('')+'</ul>'+(()=>{const ok=rules.filter(i=>craft(s,i).ok);const sum=ok.reduce((a,i)=>a+i.shardCost,0);return ok.length>1?`<p class="note">개별로는 교환 가능하지만, 모두 교환하려면 합계 ${sum}개 필요 (보유 ${shards(s)}) ${sum>shards(s)?'→ 동시에 전부는 불가, 우선순위 선택 필요':''}</p>`:''})()):'<p class="note">현재 교환 규칙상 가능한 미보유 인격이 없습니다.</p>'}
      ${up.length?('<div class="warn">출시 예정: '+up.map(i=>esc(i.name)+' ('+esc(i.next)+')').join(', ')+'</div>'):''}
      <p class="note">수감자 특정 추출(로테이션) 기록: ${s.rotationHistory.slice(-4).join(', ')} → <span class="tag-est">예상</span>다음 ${s.rotationEstimate.from} ~ ${s.rotationEstimate.to} (신뢰도 낮음)</p>`;
    document.getElementById('shIn').addEventListener('input',e=>{shMap[s.id]=e.target.value===''?null:Number(e.target.value);save(LS_SH,shMap);renderGrid();renderTabs();
      // update list without losing focus
      clearTimeout(window._t);window._t=setTimeout(()=>{const pos=e.target.selectionStart;renderSummary();const n=document.getElementById('shIn');n.focus();},600)});
  }
}
function renderGrid(){
  const g=document.getElementById('grid');const q=st.q.trim();
  const list=[];
  for(const s of DATA.sinners){ if(st.tab!=='all'&&s.id!==st.tab)continue;
    for(const i of s.identities){const own=isOwned(s,i);
      if(st.own==='owned'&&!own)continue; if(st.own==='unowned'&&own)continue;
      if(!st.rar.has(i.rarity))continue;
      if(st.kind==='pool'&&i.standardPool!==true)continue;
      if(st.kind==='limited'&&!i.limited)continue;
      if(st.kind==='walpurgis'&&i.type!=='walpurgis')continue;
      if(st.kw!=='all'){const kk=(i.combat&&i.combat.kw)||[]; if(st.kw==='none'?(kk.length||!(i.combat&&i.combat.skills&&i.combat.skills.length)):!kk.includes(st.kw))continue;}
      if(st.craft&&(own||!craft(s,i).ok))continue;
      if(q&&!i.name.includes(q)&&!s.name.includes(q))continue;
      list.push([s,i]);}}
  list.sort((a,b)=>(isOwned(...a)-isOwned(...b))||(b[1].rarity-a[1].rarity)||(a[1].release<b[1].release?1:-1));
  if(st.tab!=='all') list.sort((a,b)=>(b[1].rarity-a[1].rarity)||(isOwned(...a)-isOwned(...b))||(a[1].release<b[1].release?1:-1));
  g.innerHTML=list.length?list.map(([s,i])=>card(s,i)).join(''):'<div class="empty">조건에 맞는 인격이 없습니다.</div>';
}
function renderSchedule(){
  const S=DATA.schedule;
  let h='<h2>추출 일정</h2><h3><span class="tag-off">공식</span>진행 중 / 발표된 특정 추출</h3><table><tr><th>배너</th><th>시작 (KST)</th><th>종료 (KST)</th><th>상태</th><th>출처</th></tr>';
  for(const b of S.official) h+=`<tr><td>${esc(b.name)}</td><td>${esc(b.start)}</td><td>${esc(b.end)}</td><td>${esc(b.status)}</td><td>${b.source.split(' ; ').map((u,n)=>`<a href="${esc(u)}" target="_blank">[${n+1}]</a>`).join(' ')}</td></tr>`;
  h+='</table><p class="note">현재 진행 중인 발푸르기스의 밤: 없음 (제9회 2026-07-09 ~ 07-23 종료). 제10회는 공식 발표 전.</p>';
  h+='<h3><span class="tag-est">예상</span>공식 발표되지 않은 추정 (확정 아님)</h3><div class="warn">아래는 과거 주기로 계산한 추정치이며 공식 일정이 아닙니다.</div><table><tr><th>항목</th><th>예상 시기</th><th>근거</th></tr>';
  for(const e of S.estimates){ if(e.from) h+=`<tr><td>${esc(e.name)}</td><td class="est">${esc(e.from)} ~ ${esc(e.to)} 시작 (중앙 ${esc(e.mid)})</td><td>${esc(e.basis)}<br>${esc(e.note||'')}</td></tr>`;
    else h+=`<tr><td>${esc(e.name)}</td><td class="est">수감자 탭 참고</td><td>${esc(e.basis)}</td></tr>`;}
  h+='</table><table style="margin-top:8px"><tr><th>수감자</th><th>최근 수감자 특정 추출</th><th class="est">다음 예상 범위</th></tr>';
  for(const s of DATA.sinners) h+=`<tr><td>${esc(s.name)}</td><td>${s.rotationHistory.slice(-3).join(', ')}</td><td class="est">${s.rotationEstimate.from} ~ ${s.rotationEstimate.to}</td></tr>`;
  h+='</table><h3>발푸르기스의 밤 역대 일정 (공식 진행 기록)</h3><table><tr><th>회차</th><th>시작</th><th>종료</th><th>직전 회차와 간격</th></tr>';
  S.walpurgisHistory.forEach((w,n)=>{h+=`<tr><td>제${w.no}회</td><td>${w.start}</td><td>${w.end}</td><td>${n?S.walpurgisIntervals[n-1]+'일':'-'}</td></tr>`});
  h+='</table><details class="more"><summary>최근 특정 추출 기록 40건 보기</summary><div><table><tr><th>배너</th><th>시작</th><th>종료</th></tr>'+S.bannerHistory.map(b=>`<tr><td>${esc(b.name)}</td><td>${b.start}</td><td>${b.end}</td></tr>`).join('')+'</table></div></details>';
  document.getElementById('schedule').innerHTML=h;
}
function renderRules(){
  const R=DATA.craftRules;
  document.getElementById('rules').innerHTML=`<h2>교환(정가)·끈 규칙</h2><p class="note">${esc(R.currencyName)}</p>
  <ul class="rules">${R.rules.map(r=>`<li>${esc(r)}</li>`).join('')}</ul><h3>끈(Thread)</h3><ul class="rules">${R.thread.map(r=>`<li>${esc(r)}</li>`).join('')}</ul>
  <p class="note">보유 끈 ${Number(document.getElementById('thread').value)||0}개 → 새 3성 1개를 4동기화까지(끈 250) 약 ${Math.floor((Number(document.getElementById('thread').value)||0)/250)}개 분량.</p>
  <p class="note">출처: ${R.sources.map(u=>`<a href="${esc(u)}" target="_blank">${esc(decodeURI(u))}</a>`).join(' · ')}</p>`;
}
function renderSources(){
  const ex=(DATA.meta.deck?[...DATA.meta.deck.sources.map(x=>({name:'전투 데이터(키워드·죄악 속성): '+x.name,url:x.url})),...DATA.meta.deck.deploySources.map(x=>({name:'출전 인원/순서: '+x.name,url:x.url}))]:[]);
  document.getElementById('sources').innerHTML='<h2>데이터 출처</h2><ul class="rules">'+[...DATA.meta.sources,...ex].map(s=>`<li><a href="${esc(s.url)}" target="_blank">${esc(s.name)}</a></li>`).join('')+'</ul><p class="note">인격 이름은 나무위키 표기(인게임 공식 한글명) 기준. 데이터 갱신은 data.json 편집으로 가능합니다.</p>';
}
function renderAll(){
  const v=VIEW_TABS.includes(st.tab)?st.tab:'';
  document.body.classList.toggle('mode-deck',v==='deck');document.body.classList.toggle('mode-builder',v==='builder');
  renderTabs();
  if(v==='deck'){renderDecks();return}
  if(v==='builder'){renderBuilder();return}
  renderSummary();renderGrid();renderSchedule();renderRules();}
document.addEventListener('click',e=>{
  const t=e.target.closest('[data-t]'); if(t){st.tab=t.dataset.t;save(LS_TAB,st.tab);history.replaceState(null,'','#'+st.tab);renderAll();window.scrollTo({top:0,behavior:'smooth'});return;}
  const p=e.target.closest('.pf[data-k]'); if(p){const b=p.parentElement.querySelector('button.own'); if(b&&!b.disabled){ownMap[b.dataset.k]=b.dataset.o!=='1';save(LS_OWN,ownMap);renderTabs();renderSummary();renderGrid();} return;}
  const o=e.target.closest('button.own'); if(o&&!o.disabled){ownMap[o.dataset.k]=o.dataset.o!=='1';save(LS_OWN,ownMap);renderTabs();renderSummary();renderGrid();return;}
  const f=e.target.closest('[data-f]'); if(f){const k=f.dataset.f,v=f.dataset.v;
    if(k==='rar'){const n=Number(v);st.rar.has(n)?st.rar.delete(n):st.rar.add(n);f.classList.toggle('on');}
    else if(k==='craft'){st.craft=!st.craft;f.classList.toggle('on');}
    else{st[k]=v;document.querySelectorAll(`[data-f="${k}"]`).forEach(x=>x.classList.toggle('on',x===f));}
    renderGrid();}
});
document.getElementById('q').addEventListener('input',e=>{st.q=e.target.value;renderGrid()});
document.getElementById('btnReset').addEventListener('click',()=>{if(confirm('보유 체크와 파편/끈 입력을 기본값(스크린샷 기준)으로 되돌릴까요?')){ownMap={};shMap={};localStorage.removeItem(LS_OWN);localStorage.removeItem(LS_SH);localStorage.removeItem(LS_TH);document.getElementById('thread').value=DATA.meta.threadDefault;renderAll();}});
(window.LIMBUS_DATA?Promise.resolve(window.LIMBUS_DATA):fetch('data.json',{cache:'no-store'}).then(r=>r.json())).then(d=>{DATA=d;
  st.tab=(decodeURIComponent(location.hash.slice(1))||load(LS_TAB,'all')); if(st.tab!=='all'&&!VIEW_TABS.includes(st.tab)&&!DATA.sinners.some(s=>s.id===st.tab))st.tab='all';
  bLoad(); deckEvents();
  const th=document.getElementById('thread');th.value=load(LS_TH,d.meta.threadDefault);th.addEventListener('input',()=>{save(LS_TH,Number(th.value));if(!VIEW_TABS.includes(st.tab))renderRules()});
  document.getElementById('asof').textContent=`데이터 기준 ${d.meta.asOf} (KST) · ${d.meta.currentSeasonName} (${d.meta.seasonStart} 시작)`;
  renderAll();renderSources();
}).catch(e=>{document.getElementById('asof').textContent='data.json을 불러오지 못했습니다. 로컬 서버(python3 -m http.server)로 열어주세요.';console.error(e)});
