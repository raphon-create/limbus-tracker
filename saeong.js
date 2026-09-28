'use strict';
/* 사영전투][투전영사 탭. meta.js 다음, app.js 보다 먼저 로드.
   전역 사용: DATA, isOwned, esc, thumb, availInfo, tierBadge, tierCls, pickAlts, altHtml, idByKey, metaDeckToBuilder, openInBuilder */
const SY=()=>DATA.meta.saeong||null;
const SY_ST={permanent:['상시','ok'],ended:['종료','off']};
function syDeckState(dk){
  const core=dk.core.map(k=>({k,...idByKey(k)})).filter(x=>x.i);
  const own=core.filter(x=>isOwned(x.s,x.i)), miss=core.filter(x=>!isOwned(x.s,x.i));
  miss.forEach(x=>{x.a=availInfo(x.s,x.i);x.alt=pickAlts(dk.alts[x.k],5).find(a=>isOwned(a.s,a.i))||null;
    x.altWhy=x.alt?((dk.alts[x.k].find(a=>a.k===x.alt.s.id+'|'+x.alt.i.name)||{}).why||[]):[]});
  const coreSin=new Set(core.map(x=>x.s.id));
  const fl=[...new Set([...(dk.flex||[]),...(dk.bench||[])])].map(k=>({k,...idByKey(k)})).filter(x=>x.i);
  const flexOwn=fl.filter(x=>isOwned(x.s,x.i)&&(!coreSin.has(x.s.id)||miss.some(m=>m.s.id===x.s.id)));
  // 판정: 미보유 핵심 자리를 (1) 출처가 든 유동 인격(다른 수감자, 보유) (2) 같은 수감자 보유 대체(덱 키워드 공유/출처 언급)로 메울 수 있는지
  const fillers=flexOwn.filter(x=>!coreSin.has(x.s.id)), fillSin=new Set();
  fillers.forEach(x=>fillSin.add(x.s.id));
  const goodAlt=m=>m.alt&&m.altWhy.some(w=>w.startsWith('출처')||w.startsWith('덱 키워드'));
  const covered=Math.min(miss.length,fillSin.size+miss.filter(goodAlt).length);
  const ratio=own.length/core.length;
  const verdict=!miss.length?['가능','ok']:(ratio>=0.7&&covered>=miss.length)?['대체로 가능','mid']:(ratio>=0.5)?['일부 부족','mid']:['부족','bad'];
  const flexCraft=fl.filter(x=>!isOwned(x.s,x.i)&&availInfo(x.s,x.i).craft&&!coreSin.has(x.s.id));
  return {core,own,miss,flexOwn,flexCraft,verdict};
}
function syDeckCard(st,dk){
  const S=syDeckState(dk), full=!S.miss.length;
  const src=SY().sources, sname=id=>{const s=src.find(x=>x.id===id);return s?s:{site:id,date:''}};
  const miss=S.miss.map(x=>`<span class="mm${x.a.craft?' cr':''}" title="${esc(x.s.name+' · '+x.i.name+' — '+x.a.t)}"><b>${esc(x.s.name)}</b> ${esc(x.i.name)}${x.a.craft?' <b class="crm">제작 가능</b>':''}</span>`).join(', ');
  const subs=S.miss.filter(x=>x.alt).map(x=>`<span title="${esc(x.altWhy.join(' · '))}">${esc(x.i.name)} → <b>${esc(x.alt.i.name)}</b></span>`);
  const flexOwn=S.flexOwn.slice(0,4).map(x=>`${esc(x.s.name)} ${esc(x.i.name)}`);
  const egos=(dk.egos||[]).filter(e=>e.need==='필수'||e.need==='권장'||e.need==='하드 권장');
  const main=dk.sources.slice(0,2).map(id=>{const s=sname(id);return `${esc(s.site.split(' · ')[0])} ${esc(s.date)}`}).join(' · ');
  const conf=dk.stale?'<span class="syc off">오래됨</span>':`<span class="syc ${dk.confidence==='높음'?'ok':dk.confidence==='보통'?'mid':'bad'}" title="출처 신뢰도">${esc(dk.confidence)}</span>`;
  return `<div class="mdk syk${full?' full':''}">
    <div class="mdh"><b class="mdn">${esc(dk.name)}</b><span class="mdm">${dk.phases.map(n=>n+'페').join('·')} · ${esc(dk.role)}</span>
      <span class="mdo ${full?'off':'est'}" title="핵심 인격 보유 수 (이 브라우저 보유 체크 기준)">보유 ${S.own.length}/${S.core.length}</span></div>
    <div class="mdt">${S.core.map(x=>thumb(x.s,x.i,{label:false,cls:'mini'})).join('')}</div>
    <div class="mdl"><span class="syv ${S.verdict[1]}">${S.verdict[0]}</span> ${S.miss.length?`<span class="lb">없음</span> ${miss}`:'핵심 인격 모두 보유'}</div>
    ${subs.length?`<div class="mdl sub"><span class="lb">대체</span> ${subs.join(', ')}</div>`:(S.miss.length?'<div class="mdl sub"><span class="lb">대체</span> 같은 수감자 보유 후보 없음</div>':'')}
    ${S.miss.length&&(flexOwn.length||S.flexCraft.length)?`<div class="mdl sub"><span class="lb">유동</span> ${flexOwn.length?'보유 '+flexOwn.join(', '):''}${S.flexCraft.length?`${flexOwn.length?' · ':''}${S.flexCraft.map(x=>`${esc(x.s.name)} ${esc(x.i.name)} <b class="crm">제작 가능</b>`).join(', ')}`:''}</div>`:''}
    ${egos.length?`<div class="mdl sub"><span class="lb">E.G.O</span> ${egos.map(e=>`${esc(e.n)}<i class="egn">${esc(e.need)}</i>`).join(', ')}</div>`:''}
    <div class="mdl sub"><span class="lb">출처</span> ${main}${dk.sources.length>2?` 외 ${dk.sources.length-2}`:''} ${conf}</div>
    <div class="mdb"><button class="btn sm" data-sydk="${esc(st.id)}|${esc(dk.id)}">빌더로 ▶</button>
    <details class="more mdd"><summary>세부</summary><div>
      <b>핵심</b>: ${S.core.map(x=>`${esc(x.s.name)} ${esc(x.i.name)} ${tierBadge(x.i)}${isOwned(x.s,x.i)?'':' <span class="est">미보유</span>'}`).join(' · ')}
      ${(dk.flex||[]).length?`<br><b>유동(출처 언급)</b>: ${dk.flex.map(k=>idByKey(k)).filter(x=>x.i).map(x=>`${esc(x.s.name)} ${esc(x.i.name)}${isOwned(x.s,x.i)?' ✓':' <span class="note">미보유</span>'}`).join(' · ')}`:''}
      ${S.miss.map(x=>`<br><b>${esc(x.s.name)} 자리 대체</b>: ${altHtml(dk.alts[x.k])||'없음'}${x.altWhy.length?` <span class="note">(${esc(x.altWhy.join(' · '))})</span>`:''}`).join('')}
      ${(dk.egos||[]).length?`<br><b>E.G.O</b> (보유 여부는 미추적): ${dk.egos.map(e=>`${esc(e.n)} [${esc(e.need)}] — ${esc(e.why)}`).join(' / ')}`:''}
      ${dk.turns?`<br><b>턴</b>: ${esc(dk.turns)}`:''}
      ${dk.benchNote?`<br><b>메모</b>: ${esc(dk.benchNote)}`:''}
      ${(dk.unmatched||[]).length?`<br><span class="est">미확인</span>: ${dk.unmatched.map(esc).join(' / ')}`:''}
      <br><b>근거</b><ul class="rules">${dk.evidence.map(t=>`<li>${esc(t)}</li>`).join('')}</ul>
      출처: ${dk.sources.map(id=>{const s=sname(id);return s.url?`<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.site)}</a> (${esc(s.date)})`:esc(s.site)}).join(' · ')}
      <br><span class="note">핵심 평균 ${tierBadgeT(dk.t)} ${dk.s}점 = 일반 커뮤니티 티어 평균(사영전투 전용 평가 아님)</span>
    </div></details></div>
  </div>`;
}
function tierBadgeT(t){return `<span class="tb ${tierCls(t)}">${esc(t)}</span>`}
function syPhaseRow(p){
  const fav=[...p.fav.kw,...p.fav.sin,...p.fav.fac].join('·');
  return `<div class="syp"><div class="syph"><b>${p.n}페</b> <span class="sys">${esc(p.shade)}</span> <span class="syf" title="이 페이즈에서 피해 보너스를 받는 키워드·죄악 속성·소속">접대 ${esc(fav)}</span></div>
    <div class="mdl">${esc(p.gimmick)}</div>
    <details class="more"><summary>효과·팁</summary><div class="mdl">${esc(p.effect)}<br>${esc(p.tip)}</div></details></div>`;
}
function syStageVerdict(st){
  // 페이즈별 가장 보유율 높은 덱
  return st.phases.map(p=>{const L=st.decks.filter(d=>d.phases.includes(p.n)).map(d=>({d,S:syDeckState(d)}));
    if(!L.length) return '';
    const rank={ok:0,mid:1,bad:2};
    L.sort((a,b)=>rank[a.S.verdict[1]]-rank[b.S.verdict[1]]||(b.S.own.length/b.S.core.length)-(a.S.own.length/a.S.core.length));
    const b=L[0];
    return `<span class="syvb ${b.S.verdict[1]}">${p.n}페 ${esc(b.d.name)} ${b.S.own.length}/${b.S.core.length} · ${b.S.verdict[0]}</span>`}).join(' ');
}
function syStage(st){
  const [lab,cls]=SY_ST[st.status]||['',''];
  return `<section class="panel sy${st.status==='ended'?' syend':''}">
    <h2>${esc(st.name)} <span class="syst ${cls}">${lab}${st.since?' · '+esc(st.since)+'~':''}${st.period?' · '+esc(st.period):''}</span>
      <span class="note">${esc(st.fullReward)}</span></h2>
    <p class="sysum">${esc(st.summary)}</p>
    <div class="syverd"><span class="lb">내 보유 판정</span> ${syStageVerdict(st)}</div>
    <div class="sypg">${st.phases.map(syPhaseRow).join('')}</div>
    <div class="mdgrid">${st.decks.map(d=>syDeckCard(st,d)).join('')}</div>
    <details class="more"><summary>전투 정보·하드 고난</summary><div class="mdl">보스: ${esc(st.boss)} · ${esc(st.event)} · 개방: ${esc(st.unlock)}<br>${esc(st.hard)}
      <br>보상 턴 기준: 노말 ${st.rewardTurns.normal.join('/')}턴 · 하드 ${st.rewardTurns.hard.join('/')}턴
      <ul class="rules">${st.notes.map(t=>`<li>${esc(t)}</li>`).join('')}</ul></div></details>
  </section>`;
}
function renderSaeong(){
  const el=document.getElementById('saeongView'); const M=SY(); if(!el) return;
  if(!M){el.innerHTML='<section class="panel"><p class="note">사영전투 데이터 없음 (tools/update_helpers.py merge-saeong)</p></section>';return}
  const cur=M.stages.filter(s=>s.status!=='ended'), end=M.stages.filter(s=>s.status==='ended');
  el.innerHTML=`<section class="panel syhead"><h2>사영전투][투전영사 <span class="note">Reflectrial · 커뮤니티 공략 요약 · ${esc(M.__meta__.asOf)} 기준 · 참고용</span> <a href="#" class="srcl" data-sysrc="1">출처·기준</a></h2>
    <p class="sysum">현재 플레이 가능 ${cur.length}개(상시) · 편성 최대 3개(각 12턴, 인격 재사용 불가) · 하드 18턴 이하가 최고 보상. 보유 x/y = 덱 핵심 인격 중 보유 수.</p>
    <details class="more"><summary>콘텐츠 규칙</summary><div class="mdl">${esc(M.__meta__.what)}<ul class="rules">${M.__meta__.rules.map(t=>`<li>${esc(t)}</li>`).join('')}</ul></div></details></section>
    ${cur.map(syStage).join('')}
    ${end.length?`<details class="panel syold"><summary><b>종료된 사영전투</b> <span class="note">복각 후 상시화 예정 · 참고용 (${end.map(s=>esc(s.name)).join(', ')})</span></summary>${end.map(syStage).join('')}</details>`:''}`;
}
function syToBuilder(st,dk){
  // 출전 순서: 보유 핵심 → 출처 유동 인격(보유) → 미보유 핵심 수감자의 보유 대체 → 나머지(덱 키워드·티어순)
  const picks={}, order=[], used=new Set(), put=(s,i)=>{picks[s.id]=i.name;order.push(s.id);used.add(s.id)};
  const core=dk.core.map(k=>({k,...idByKey(k)})).filter(x=>x.i);
  core.filter(x=>isOwned(x.s,x.i)).forEach(x=>{if(!used.has(x.s.id))put(x.s,x.i)});
  const coreSin=new Set(core.map(x=>x.s.id));
  [...new Set([...(dk.flex||[]),...(dk.bench||[])])].map(k=>idByKey(k)).filter(x=>x.i&&isOwned(x.s,x.i)&&!coreSin.has(x.s.id)).forEach(x=>{if(!used.has(x.s.id))put(x.s,x.i)});
  core.filter(x=>!isOwned(x.s,x.i)&&!used.has(x.s.id)).forEach(x=>{const a=pickAlts(dk.alts[x.k],5).find(a=>isOwned(a.s,a.i)); if(a)put(a.s,a.i)});
  const rest=DATA.sinners.filter(s=>!used.has(s.id)).map(s=>{const o=s.identities.filter(i=>isOwned(s,i)&&!i.upcoming&&(cb(i).kw||[]).some(k=>dk.kw.includes(k))).sort((a,b)=>tierScore(b)-tierScore(a));return {s,i:o[0]||null}});
  rest.sort((a,b)=>tierScore(b.i)-tierScore(a.i));
  for(const r of rest){order.push(r.s.id); picks[r.s.id]=r.i?r.i.name:defaultPick(r.s)}
  return {name:`사영 ${st.name.split(' · ').pop()} · ${dk.name}`,order,picks,from:'사영전투 · '+st.name+' · '+dk.name};
}
function openSySrc(){
  const M=SY(); if(!M) return; const T=M.__meta__;
  let d=document.getElementById('sySrc'); if(!d){d=document.createElement('dialog');d.id='sySrc';d.className='tsrcdlg';document.body.appendChild(d)}
  d.innerHTML=`<div class="dlg"><div class="dlgh"><h2>사영전투 출처·기준</h2><button class="ghost" data-syclose="1">닫기 ✕</button></div>
   <p class="note">${esc(T.disclaimer)}</p><p class="mdl">${esc(T.what)}</p>
   <h3>기준</h3><ul class="rules">${T.method.map(t=>`<li>${esc(t)}</li>`).join('')}</ul>
   <h3>사용한 출처 (${M.sources.length})</h3>
   <table class="st"><tr><th>출처</th><th>기준일</th><th>종류</th><th>대상</th><th>내용</th></tr>
   ${M.sources.map(s=>`<tr><td><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.site)}</a><br><span class="note">${esc(s.title)}</span></td><td class="nw">${esc(s.date)}${s.fresh===false?' <span class="est">컷오프 이전</span>':''}<br><span class="note">${esc(s.dateNote)}</span></td><td>${esc({wiki:'위키',guide:'공략 기사',post:'커뮤니티 글',video:'영상'}[s.type]||s.type)}</td><td>${s.stages.map(id=>esc((M.stages.find(x=>x.id===id)||{}).name||id)).join('<br>')}</td><td class="snote">${esc(s.note)}</td></tr>`).join('')}</table>
   <h3>제외한 출처 (${M.excluded.length})</h3><ul class="rules">${M.excluded.map(x=>`<li>${x.url?`<a href="${esc(x.url)}" target="_blank" rel="noopener">${esc(x.site)}</a>`:esc(x.site)} (${esc(x.date)}) — ${esc(x.reason)}</li>`).join('')}</ul></div>`;
  if(d.showModal) d.showModal(); else d.setAttribute('open','');
}
function syFind(v){const [a,b]=v.split('|');const M=SY();const st=M&&M.stages.find(s=>s.id===a);const dk=st&&st.decks.find(x=>x.id===b);return st&&dk?{st,dk}:null}
document.addEventListener('click',e=>{
  const a=e.target.closest('[data-sysrc]'); if(a){e.preventDefault();openSySrc();return}
  const c=e.target.closest('[data-syclose]'); if(c){const d=document.getElementById('sySrc');d.close?d.close():d.removeAttribute('open');return}
  if(e.target.id==='sySrc'){e.target.close&&e.target.close();return}
  const b=e.target.closest('[data-sydk]'); if(b){const f=syFind(b.dataset.sydk); if(f) openInBuilder(syToBuilder(f.st,f.dk)); return}
});
document.addEventListener('change',e=>{
  if(e.target.id==='bSy'&&e.target.value){const f=syFind(e.target.value); if(f) openInBuilder(syToBuilder(f.st,f.dk));}
});
