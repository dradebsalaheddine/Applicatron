"""JSON-lines worker; UI/main process own file selection and cancellation."""
import sys,json,time,re,mailbox,email.policy,email.parser,hashlib
from pathlib import Path
from import_mail import text_of,RULES
from mail_analysis import extract
from model_backends import LocalModel,MODELS,FOLDERS

def emit(kind,**data):print(json.dumps(dict(type=kind,**data),ensure_ascii=False),flush=True)
def main():
 req=json.loads(sys.stdin.readline());root=Path(req['models']);root.mkdir(parents=True,exist_ok=True)
 if req['action']=='download':
  from huggingface_hub import snapshot_download
  name=req['model'];emit('progress',stage='Downloading '+name,detail='The first download can take several minutes. Cancel stops the download; completed files are reused.')
  snapshot_download(MODELS[name],local_dir=root/FOLDERS[name],ignore_patterns=['*.gguf','*.onnx','*.h5','*.msgpack','*.bin'])
  (root/FOLDERS[name]/'.ready').write_text('ready');emit('done');return
 from import_report import write_report
 engines={};rows=[];seen=set();threads=set();start=time.perf_counter();qwen_calls=0;mini_calls=0
 def engine(name):
  if name not in engines:
   emit('progress',stage='Loading '+name,detail='Loading local weights…')
   # Keep lightweight screening on CPU; only one optional large model is selected.
   engines[name]=LocalModel(name,root,'CPU' if name=='MiniLM' else req.get('device','Auto'))
  return engines[name]
 box=mailbox.mbox(req['path'],factory=lambda f:email.parser.BytesParser(policy=email.policy.default).parse(f),create=False)
 try:
  for count,msg in enumerate(box,1):
   subject=str(msg.get('Subject',''));sender=str(msg.get('From',''));body=text_of(msg);text=subject+'\n'+body
   mid=str(msg.get('Message-ID','')).strip();key=mid or hashlib.sha256(text.encode()).hexdigest()
   if key in seen:continue
   seen.add(key);refs=str(msg.get('References',''))+' '+str(msg.get('In-Reply-To',''))
   hits=[k for k,p in RULES if re.search(p,text,re.I|re.S)]
   sender_hint=bool(re.search('careers|recruitment|recrutement|greenhouse|workday|lever.co',sender,re.I))
   linked=any(x in threads for x in refs.split())
   candidate=extract(subject,body,sender);semantic=None;route='Skipped';label='uncertain'
   if hits or sender_hint or linked:
    route='Review';label=next((k for k in ['rejection','interview','assessment','confirmation'] if k in hits),'uncertain')
    clear=label!='uncertain'
    # MiniLM receives uncertain rule candidates only. Unknown unrelated messages never reach a large model.
    if not clear and req.get('mini'):
     emit('progress',stage='MiniLM screening',count=count,qwen=qwen_calls,mini=mini_calls)
     semantic=engine('MiniLM').screen(text);mini_calls+=1
     if semantic['label']=='unrelated' and not semantic['uncertain'] and not linked:route='Skipped'
     else:label=semantic['label'] if not semantic['uncertain'] else 'uncertain'
    unresolved=not candidate['company'] or not candidate['role'] or candidate['conflict'] or label=='uncertain'
    if route!='Skipped' and unresolved and req.get('large') in ('Qwen3','SmolLM3'):
     emit('progress',stage=req['large']+' extraction',count=count,qwen=qwen_calls,mini=mini_calls)
     # Preserve subject and bounded latest-message passage; never feed the whole archive.
     semantic=engine(req['large']).screen(text[:7000]);qwen_calls+=1
     for field in ('company','role'):
      if not candidate[field] and not candidate['conflict'] and semantic.get(field):candidate[field]=semantic[field]
     if semantic.get('evidence'):candidate['evidence'].append(semantic['evidence'])
     if semantic['label']!='uncertain':label=semantic['label']
    if mid:threads.add(mid)
   row=dict(id=key,subject=subject,sender=sender,body=body[:30000],refs=refs,route=route,evidence=', '.join(hits) or ('Sender/thread hint' if sender_hint or linked else 'No recruitment evidence'),candidate=candidate,semantic=semantic,label=label)
   rows.append(row)
   if route!='Skipped':emit('row',row=row)
   if count%20==0 or route!='Skipped':emit('progress',stage='Rules screening',count=count,qwen=qwen_calls,mini=mini_calls,seconds=round(time.perf_counter()-start,1))
  write_report(rows,req['report'],'Layered: rules → MiniLM → '+str(req.get('large') or 'review'),time.perf_counter()-start)
  emit('done',count=len(rows),report=req['report'],qwen=qwen_calls,mini=mini_calls)
 finally:box.close()
if __name__=='__main__':
 try:main()
 except Exception as e:emit('error',message=str(e));sys.exit(1)
