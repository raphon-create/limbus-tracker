'use strict';
/* 커뮤니티 종합 티어 + 메타 덱 + 출처·기준 모달.
   deck.js 다음, app.js 보다 먼저 로드. app.js/deck.js 전역(DATA, isOwned, craft, esc, key, rarStr, thumb, availInfo, sinnerById, findId, openInBuilder, deployN, cb, kwColor)을 실행 시점에 사용. */
const TM=()=>DATA.meta.tier||null;
const TIER_ORDER=['SS','S+','S','S-','A+','A','A-','B','C','D'];
const tierRank=i=>{const t=i&&i.tier;return t?TIER_ORDER.length-TIER_ORDER.indexOf(t.t):0};   // 클수록 높음, 미평가 0
const tierScore=i=>(i&&i.tier)?i.tier.s:0;
const tierCls=t=>t==='SS'?'tss':t[0]==='S'?'ts':t[0]==='A'?'ta':t==='B'?'tbb':t==='C'?'tc':'td';
const TREND={up:['▲','상승'],down:['▼','하락'],new:['N','신규'],flat:['',"변동 없음"]};
const MODE_KO={RR:'굴절철도',MD:'거울던전',general:'일반',story:'스토리'};
const SRC_KO=id=>({prydwen:'Prydwen',gll:'GLL',gamemeca:'게임메카',arca:'아카 투표',goni:'고니'}[id]||id);
const idByKey=k=>{const [sid,n]=k.split('|');const s=sinnerById(sid);return {s,i:findId(s,n)}};
function tierTitle(i){
  const t=i.tier; if(!t) return '커뮤니티 평가 없음';
  const m=Object.entries(t.modes||{}).map(([k,v])=>`${MODE_KO[k]} ${v.t}`).join(' · ');
  return `커뮤니티 종합 ${t.t} (${t.s}점) · ${t.n}곳${t.agree!=='단일'?' · 합의 '+t.agree:''}${t.split?' · 의견 갈림':''}${m?'\n모드별: '+m:''}${t.trend&&TREND[t.trend][0]?`\n추세 ${TREND[t.trend][1]}: ${(t.trendNote||[]).slice(0,2).join(', ')}`:''}\n${t.reason||''}\n(${TM().asOf} 기준 커뮤니티 집계·참고용)`;
}
function tierBadge(i,opt={}){
  if(!i||!i.tier) return opt.empty?'<span class="tb tn" title="커뮤니티 평가 없음">–</span>':'';
  const t=i.tier, ar=TREND[t.trend]?TREND[t.trend][0]:'';
  return `<span class="tb ${tierCls(t.t)}${opt.cls?' '+opt.cls:''}" title="${esc(tierTitle(i))}">${esc(t.t)}${ar?`<i class="tr ${t.trend}">${ar}</i>`:''}</span>`;
}
/* 대체 후보: 보유 우선 1~3개 */
function pickAlts(list,n=3){
  const L=(list||[]).map(a=>({...a,...idByKey(a.k)})).filter(a=>a.i);
  const own=L.filter(a=>isOwned(a.s,a.i)), un=L.filter(a=>!isOwned(a.s,a.i));
  return [...own,...un].slice(0,n);
}
function altHtml(list,n=3){
  const L=pickAlts(list,n); if(!L.length) return '';
  return L.map(a=>`<span class="alt${isOwned(a.s,a.i)?' own':''}" title="${esc(a.s.name+' · '+a.i.name)}${a.kw&&a.kw.length?' · 공유 키워드 '+esc(a.kw.join('·')):''}${isOwned(a.s,a.i)?' (보유)':' (미보유)'}">${esc(a.i.name)} ${tierBadge(a.i)}</span>`).join(' ');
}
function tierDetail(s,i){
  const t=i.tier, T=TM(); if(!t||!T) return '<br><b>커뮤니티 티어</b> 평가 없음 (수집한 출처에 미등재)';
  const srcName=id=>(T.sources.find(x=>x.id===id)||{}).site||id;
  const rows=t.src.map(e=>`<tr><td>${esc(SRC_KO(e.id))}</td><td>${esc(e.raw)}</td><td class="cnum">${e.s}</td><td class="nw">${(e.m||[]).map(m=>({RR:'철도',MD:'거던',general:'일반'})[m]||m).join('·')}</td><td class="cnum">${e.w}</td><td class="nw">${esc((e.d||'').slice(2))}</td><td class="snote">${esc(e.note||'')}</td></tr>`).join('');
  const modes=Object.entries(t.modes||{}).map(([k,v])=>`${MODE_KO[k]} <b>${v.t}</b>(${v.s})`).join(' · ');
  return `<br><b>커뮤니티 티어</b> ${tierBadge(i)} ${t.s}점 · 출처 ${t.n}곳 · 합의 ${esc(t.agree)}${t.n>1?` (σ ${t.sd}, 범위 ${t.range[0]}~${t.range[1]})`:''}${t.split?' · <span class="est">의견 갈림</span>':''}
   ${modes?'<br>모드별: '+modes:''}${(t.roles||[]).length?'<br>역할(출처 표기): '+esc(t.roles.join(', ')):''}
   <br>한 줄 요약: ${esc(t.reason||'-')}
   ${(t.trendNote||[]).length?`<br>추세 ${esc(TREND[t.trend]?TREND[t.trend][1]:'')}: ${esc(t.trendNote.join(' / '))}`:''}
   ${t.alts&&t.alts.length?`<br>대체 후보(같은 수감자·키워드, 보유 우선): ${altHtml(t.alts)}`:''}
   <table class="st srct"><tr><th>출처</th><th>원등급</th><th>0~100</th><th>모드</th><th>가중</th><th>기준일</th><th>메모</th></tr>${rows}</table>
   <span class="note">${esc(T.disclaimer)} · <a href="#" data-tsrc="1">출처·기준</a></span>`;
}

/* ---------- 메타 덱 ---------- */
function metaDeckState(dk){
  const core=dk.core.map(k=>({k,...idByKey(k)})).filter(x=>x.i);
  const own=core.filter(x=>isOwned(x.s,x.i)), miss=core.filter(x=>!isOwned(x.s,x.i));
  miss.forEach(x=>{x.a=availInfo(x.s,x.i);x.alt=pickAlts(dk.alts[x.k],3).find(a=>isOwned(a.s,a.i))||null});
  return {core,own,miss};
}
function metaDeckCard(dk){
  const S=metaDeckState(dk), full=!S.miss.length;
  const miss=S.miss.map(x=>`<span class="mm${x.a.craft?' cr':''}" title="${esc(x.s.name+' · '+x.i.name+' — '+x.a.t)}"><b>${esc(x.s.name)}</b> ${esc(x.i.name)}${x.a.craft?' <b class="crm">제작 가능</b>':''}</span>`).join(', ');
  const subs=S.miss.filter(x=>x.alt).map(x=>`${esc(x.i.name)} → ${esc(x.alt.i.name)}`);
  const thumbs=S.core.map(x=>thumb(x.s,x.i,{label:false,cls:'mini'})).join('');
  const flex=dk.flex.map(k=>idByKey(k)).filter(x=>x.i);
  const ds=(TM().deckSources||[]);
  return `<div class="mdk${full?' full':''}">
    <div class="mdh"><b class="mdn">${esc(dk.name)}</b> <span class="tb ${tierCls(dk.t)}" title="덱 티어 ${esc(dk.t)}: 핵심 인격 커뮤니티 종합 점수 평균 ${dk.s} (${esc(TM().asOf)} 기준·참고용)">${esc(dk.t)}</span><span class="mdm">${dk.modes.map(m=>MODE_KO[m]||m).join('·')}</span>
      <span class="mdo ${full?'off':'est'}">보유 ${S.own.length}/${S.core.length}</span></div>
    <div class="mdt">${thumbs}</div>
    ${S.miss.length?`<div class="mdl"><span class="lb">없음</span> ${miss}</div>`:'<div class="mdl off">핵심 인격 모두 보유</div>'}
    ${subs.length?`<div class="mdl sub"><span class="lb">대체</span> ${subs.join(', ')}</div>`:(S.miss.length?'<div class="mdl sub"><span class="lb">대체</span> 보유 중인 같은 수감자·키워드 후보 없음</div>':'')}
    <div class="mdb"><button class="btn sm" data-mdk="${esc(dk.id)}">빌더로 ▶</button>
    <details class="more mdd"><summary>세부</summary><div>
      <b>핵심</b>: ${S.core.map(x=>`${esc(x.s.name)} ${esc(x.i.name)} ${tierBadge(x.i)}${isOwned(x.s,x.i)?'':' <span class="est">미보유</span>'}`).join(' · ')}
      <br><b>유동(flex)</b>: ${flex.map(x=>`${esc(x.s.name)} ${esc(x.i.name)} ${tierBadge(x.i)}${isOwned(x.s,x.i)?'':' <span class="note">미보유</span>'}`).join(' · ')||'-'}
      ${S.miss.map(x=>`<br><b>${esc(x.s.name)} 자리 대체</b>: ${altHtml(dk.alts[x.k])||'없음'}`).join('')}
      <br><b>근거</b><ul class="rules">${dk.evidence.map(t=>`<li>${esc(t)}</li>`).join('')}</ul>
      ${dk.confidence?`<span class="est">구성 신뢰도 ${esc(dk.confidence)}: ${esc(dk.confidenceNote||'')}</span><br>`:''}
      출처: ${dk.sources.map(id=>{const d=ds.find(x=>x.id===id);return d?`${esc(d.site)} (${esc(d.date)})`:esc(id)}).join(' · ')} · 덱 티어 = 핵심 인격 종합 점수 평균 ${dk.s}
    </div></details></div>
  </div>`;
}
function metaDeckSection(){
  const T=TM(), L=DATA.meta.metaDecks||[]; if(!T||!L.length) return '';
  return `<section class="panel mdeck"><h2>메타 덱 <span class="note">커뮤니티 종합 · ${esc(T.asOf)} 기준 · 참고용</span> <a href="#" class="srcl" data-tsrc="1">출처·기준</a></h2>
   <div class="mdgrid">${L.map(metaDeckCard).join('')}</div>
   <p class="note">보유 x/y = 핵심 인격 중 보유 수 · “제작 가능” = 지금 파편으로 교환 가능 · 대체 = 같은 수감자·덱 키워드 인격 중 보유한 최고 티어(출처가 언급한 유동 인격 우선)</p></section>`;
}
function metaDeckToBuilder(dk){
  const picks={}, order=[], used=new Set();
  for(const k of dk.core){const {s,i}=idByKey(k); if(!s||used.has(s.id)) continue;
    const alt=isOwned(s,i)?null:(pickAlts(dk.alts[k],3).find(a=>isOwned(a.s,a.i))||null);
    picks[s.id]=(alt?alt.i:i).name; order.push(s.id); used.add(s.id);}
  for(const k of dk.flex){const {s,i}=idByKey(k); if(!s||used.has(s.id)||!isOwned(s,i)) continue; picks[s.id]=i.name; order.push(s.id); used.add(s.id);}
  const rest=DATA.sinners.filter(s=>!used.has(s.id)).map(s=>{const o=s.identities.filter(i=>isOwned(s,i)&&!i.upcoming&&(cb(i).kw||[]).some(k=>dk.kw.includes(k))).sort((a,b)=>tierScore(b)-tierScore(a));return {s,i:o[0]||null}});
  rest.sort((a,b)=>tierScore(b.i)-tierScore(a.i));
  for(const r of rest){order.push(r.s.id); picks[r.s.id]=r.i?r.i.name:defaultPick(r.s)}
  return {name:dk.name,order,picks,from:'메타 덱 · '+dk.name};
}
function teamTier(list){
  const r=list.filter(i=>i&&i.tier); if(!r.length) return null;
  const s=r.reduce((a,i)=>a+i.tier.s,0);
  const avg=s/r.length; const B=TM().bands; const t=(B.find(([lim])=>avg>=lim)||[0,'D'])[1];
  return {avg:Math.round(avg*10)/10,t,n:r.length,total:Math.round(s)};
}

/* ---------- 출처·기준 모달 ---------- */
function openTierSrc(){
  const T=TM(); if(!T) return;
  let d=document.getElementById('tierSrc');
  if(!d){d=document.createElement('dialog');d.id='tierSrc';document.body.appendChild(d)}
  d.innerHTML=`<div class="dlg"><div class="dlgh"><h2>커뮤니티 티어 출처·기준</h2><button class="ghost" data-tclose="1">닫기 ✕</button></div>
   <p class="note">${esc(T.disclaimer)} · 현재 시즌 ${T.season} (${esc(T.seasonStart)} 시작)</p>
   <h3>신선도 컷오프: ${esc(T.cutoff)} 이후 갱신</h3><p class="note">${esc(T.cutoffWhy)}</p>
   <h3>점수 방식</h3><ul class="rules">${T.method.map(t=>`<li>${esc(t)}</li>`).join('')}</ul>
   <h3>사용한 티어 출처 (${T.sources.length})</h3>
   <table class="st"><tr><th>출처</th><th>기준일</th><th>모드</th><th>범위</th><th>등급→점수</th><th>가중</th><th>인격 수</th></tr>
   ${T.sources.map(s=>`<tr><td><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.site)}</a><br><span class="note">${esc(s.region)} · ${esc(s.title)}</span></td><td>${esc(s.date)}<br><span class="note">${esc(s.dateNote)}</span></td><td>${s.modes.map(m=>MODE_KO[m]||m).join('·')}<br><span class="note">${esc(s.modeNote)}</span></td><td>${esc(s.season)}</td><td class="snote">${Object.entries(s.norm).map(([k,v])=>`${esc(k)}=${v}`).join(' ')}</td><td class="cnum">${s.weight}</td><td class="cnum">${s.count}</td></tr>`).join('')}</table>
   <h3>메타 덱 출처</h3><ul class="rules">${(T.deckSources||[]).map(s=>`<li>${s.url?`<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.site)}</a>`:esc(s.site)} (${esc(s.date)}) — ${esc(s.note)}${s.posts?'<br>'+s.posts.map(p=>`<a href="${esc(p.url)}" target="_blank" rel="noopener">${esc(p.date)} ${esc(p.title)}</a>`).join(' · '):''}</li>`).join('')}</ul>
   <h3>제외·축소한 출처 (${(T.excluded||[]).length})</h3><ul class="rules">${(T.excluded||[]).map(x=>`<li>${x.url?`<a href="${esc(x.url)}" target="_blank" rel="noopener">${esc(x.site)}</a>`:esc(x.site)} (${esc(x.date)}) — ${esc(x.reason)}</li>`).join('')}</ul></div>`;
  if(d.showModal) d.showModal(); else d.setAttribute('open','');
}
document.addEventListener('click',e=>{
  const a=e.target.closest('[data-tsrc]'); if(a){e.preventDefault();openTierSrc();return}
  const c=e.target.closest('[data-tclose]'); if(c){const d=document.getElementById('tierSrc');d.close?d.close():d.removeAttribute('open');return}
  if(e.target.id==='tierSrc'){e.target.close&&e.target.close();return}
  const m=e.target.closest('[data-mdk]'); if(m){const dk=(DATA.meta.metaDecks||[]).find(x=>x.id===m.dataset.mdk); if(dk) openInBuilder(metaDeckToBuilder(dk)); return}
});
document.addEventListener('change',e=>{
  if(e.target.id==='bMeta'&&e.target.value){const dk=(DATA.meta.metaDecks||[]).find(x=>x.id===e.target.value); if(dk) openInBuilder(metaDeckToBuilder(dk));}
});
