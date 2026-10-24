import html,json
from datetime import datetime
from pathlib import Path

def write_report(rows,path,model,seconds):
 esc=lambda s:html.escape(str(s))
 cards=[]
 for r in rows:
  cards.append('<article><h2>'+esc(r['subject'])+'</h2><p>'+esc(r['sender'])+' · '+esc(r['route'])+'</p><p>Rules: '+esc(r['evidence'])+'</p><pre>'+esc(json.dumps({'extraction':r['candidate'],'model':r['semantic']},ensure_ascii=False,indent=2))+'</pre></article>')
 document='<!doctype html><html lang="en"><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'"><title>Applicatron import review</title><style>body{font:15px system-ui;max-width:1000px;margin:40px auto;padding:20px;color:#24382e}article{border-top:1px solid #ccc;padding:16px 0}h2{font-size:17px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f5f1;padding:12px}@media print{article{break-inside:avoid}}</style><h1>Applicatron import review</h1><p>'+esc(datetime.now().isoformat(timespec='seconds'))+' · '+esc(model)+' · '+str(len(rows))+' messages · '+str(round(seconds,2))+' seconds</p><p>Private report. Suggestions require review; similarity scores are not probabilities. Use browser Print → Save as PDF if needed.</p>'+''.join(cards)+'</html>'
 Path(path).write_text(document,encoding='utf-8')
