// smart_analysis_web.js — JS port for Vercel typing-test.tsx
// Standalone, no deps.  Copy into myportfolio/src/lib/smartAnalysis.ts or import as ES module.
// Mirrors python/smart_analysis.py logic.

export const KEY_POS = {};
function addRow(chars, y, x0, dx=1){
  chars.forEach((ch,i)=>{
    KEY_POS[ch]=[x0+i*dx, y];
    if(/[a-z]/.test(ch)) KEY_POS[ch.toUpperCase()]=[x0+i*dx, y];
  });
}
addRow("`1234567890-=".split(""),0,0);
addRow("qwertyuiop[]\\".split(""),1,0.5);
addRow("asdfghjkl;'".split(""),2,0.75);
addRow("zxcvbnm,./".split(""),3,1.25);
KEY_POS[" "] = [5.5,4.0];

const BASE_TO_SHIFT = {'`':'~','1':'!','2':'@','3':'#','4':'$','5':'%','6':'^','7':'&','8':'*','9':'(','0':')','-':'_','=':'+','[':'{',']':'}','\\':'|',';':':',"'":'"',',':'<','.':'>','/':'?'};
const SHIFT_TO_BASE = Object.fromEntries(Object.entries(BASE_TO_SHIFT).map(([k,v])=>[v,k]));

export function distance(a,b){
  if(!a||!b) return 9.9;
  const pa=KEY_POS[a[0]]||KEY_POS[a[0].toLowerCase()];
  const pb=KEY_POS[b[0]]||KEY_POS[b[0].toLowerCase()];
  if(!pa||!pb) return 9.9;
  return Math.hypot(pa[0]-pb[0], pa[1]-pb[1]);
}
export function isAdjacent(a,b){
  if(!a||!b) return false;
  if(a.toLowerCase()===b.toLowerCase()) return false;
  return distance(a,b) <= 1.42;
}

export function classifySingle(exp, typed, prev="", next=""){
  if(exp===typed) return {category:"correct", reason:"", suggestion:""};
  if(exp.toLowerCase()===typed.toLowerCase() && exp!==typed){
    if(exp[0]===exp[0].toUpperCase() && typed[0]===typed[0].toLowerCase())
      return {category:"shift_case", reason:`Missed Shift for '${exp}' (typed '${typed}')`, suggestion:`Hold Shift for '${exp}'`};
    return {category:"shift_case", reason:`Accidental Shift '${typed}' vs '${exp}' — Caps Lock?`, suggestion:`Release Shift for '${exp}'`};
  }
  if(SHIFT_TO_BASE[exp]===typed) return {category:"shift_symbol", reason:`Expected '${exp}' (Shift+'${typed}') but typed '${typed}'`, suggestion:`Shift+'${typed}' → '${exp}'`};
  if(SHIFT_TO_BASE[typed]===exp) return {category:"shift_symbol", reason:`Expected '${exp}' but typed shifted '${typed}'`, suggestion:`Release Shift`};
  if(BASE_TO_SHIFT[exp]===typed) return {category:"shift_symbol", reason:`Expected '${exp}' but held Shift → '${typed}'`, suggestion:`Don't hold Shift`};
  if(BASE_TO_SHIFT[typed]===exp) return {category:"shift_symbol", reason:`Expected '${exp}' but typed base '${typed}'`, suggestion:`Hold Shift`};
  if(isAdjacent(exp,typed)){
    const d=distance(exp,typed);
    return {category:"adjacent_key", reason:`'${typed}' next to '${exp}' on QWERTY (dist ${d.toFixed(1)}) — fat-finger`, suggestion:`Slow on '${exp}'`, distance:d};
  }
  if(prev===exp||next===exp) return {category:"double_letter", reason:`Double-letter near '${exp}' — rhythm slip`, suggestion:`Drill double '${exp.toLowerCase()}'`};
  return {category:"other", reason:`Typed '${typed}' vs '${exp}' — reading / similar-word error`, suggestion:`Practice words with '${exp}'`};
}

export function analyzeText(target, typed, wordPool=null){
  if(!target) return {errors:0, accuracy:100};
  const n=target.length, m=typed.length;
  const total={}, mistake={}, cat={}, detailed=[], wordErrors=[];
  const minLen=Math.min(n,m);
  let i=0;
  while(i<minLen){
    const exp=target[i], got=typed[i];
    const low=exp.toLowerCase();
    if(exp!=="\n"&&exp!==" ") total[low]=(total[low]||0)+1;
    if(exp!==got){
      if(i+1<minLen && target[i]===typed[i+1] && target[i+1]===typed[i]){
        cat["transposition"]=(cat["transposition"]||0)+1;
        detailed.push({pos:i, expected:exp+target[i+1], typed:got+typed[i+1], category:"transposition", reason:`Swapped '${exp+target[i+1]}' → '${got+typed[i+1]}'`, suggestion:`Drill '${exp+target[i+1]}'`});
        mistake[low]=(mistake[low]||0)+1;
        mistake[target[i+1].toLowerCase()]=(mistake[target[i+1].toLowerCase()]||0)+1;
        i+=2; continue;
      } else {
        const prev=i>0?target[i-1]:"", nxt=i+1<n?target[i+1]:"";
        const cls=classifySingle(exp,got,prev,nxt);
        cat[cls.category]=(cat[cls.category]||0)+1;
        mistake[low]=(mistake[low]||0)+1;
        detailed.push({pos:i, expected:exp, typed:got, category:cls.category, reason:cls.reason, suggestion:cls.suggestion});
      }
    }
    i++;
  }
  if(m<n){ for(let j=m;j<n;j++){ const exp=target[j]; if(exp==="\n"||exp===" ")continue; const low=exp.toLowerCase(); mistake[low]=(mistake[low]||0)+1; total[low]=(total[low]||0)+1; cat["omission"]=(cat["omission"]||0)+1; detailed.push({pos:j, expected:exp, typed:"(missing)", category:"omission", reason:`Missing '${exp}'`}); } }
  else if(m>n){ for(let j=n;j<m;j++){ const got=typed[j]; if(got==="\n"||got===" ")continue; cat["insertion"]=(cat["insertion"]||0)+1; detailed.push({pos:j, expected:"(none)", typed:got, category:"insertion", reason:`Extra '${got}'`}); } }
  const mistakeChars=Object.values(mistake).reduce((a,b)=>a+b,0);
  const accuracy=Math.max(0,(n-mistakeChars)/Math.max(1,n)*100);
  // worst letters
  const letterStats={};
  for(const ch in total){ const tot=total[ch], mis=mistake[ch]||0; letterStats[ch]={total:tot, mistakes:mis, accuracy:(tot-mis)/tot*100, error_rate:mis/Math.max(1,tot)}; }
  for(const ch in mistake) if(!letterStats[ch]) letterStats[ch]={total:0, mistakes:mistake[ch], accuracy:0, error_rate:1};
  const worst=Object.entries(letterStats).filter(([,s])=>s.mistakes>0).sort((a,b)=>(b[1].error_rate - a[1].error_rate) || (b[1].mistakes - a[1].mistakes)).slice(0,7);
  // suggestions (simplified)
  const sugg=[];
  if(worst.length===0) sugg.push("Perfect! No weak letters.");
  else {
    sugg.push(`Focus: ${worst.slice(0,3).map(([ch])=>"'"+ch+"'").join(", ")} are weakest.`);
    if((cat["adjacent_key"]||0)>=2) sugg.push(`${cat["adjacent_key"]} adjacent-key slips — precise finger!`);
    if(cat["shift_case"]) sugg.push("Shift/Caps errors — check Caps Lock / opposite-hand Shift.");
    if(cat["shift_symbol"]) sugg.push("Symbol Shift errors — Shift+base for symbols.");
    if(cat["transposition"]) sugg.push("Transpositions — rhythm on bigrams.");
  }
  return {total_chars:n, errors:detailed.length, mistakeChars, accuracy, letterStats, worstLetters:worst, categoryCounts:cat, detailed, suggestions:sugg, summary: mistakeChars===0?"Perfect":`${detailed.length} errors, ${accuracy.toFixed(1)}%`, heat: Object.fromEntries(Object.entries(letterStats).map(([k,v])=>[k,v.error_rate]))};
}

// For typing-test.tsx usage:
//   import {analyzeText} from "./smart_analysis_web.js"
//   const report = analyzeText(target, typed)
//   // report.worstLetters, report.categoryCounts, report.suggestions
