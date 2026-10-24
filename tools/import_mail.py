"""Local Gmail Takeout review utility. Run with Python 3: python tools/import_mail.py"""
import mailbox, email.policy, email.parser, re, json, hashlib, tkinter as tk
from tkinter import filedialog, messagebox, ttk
from html import unescape
from concurrent.futures import ThreadPoolExecutor

RULES = [
 ('confirmation', r'thank you for applying|application (?:has been )?received|candidature (?:a bien été |bien )?reçue|accusons réception de votre candidature'),
 ('rejection', r'not (?:been )?selected|will not be (?:moving|proceeding)|unsuccessful|candidature.{0,60}pas retenue|ne donnerons pas suite'),
 ('interview', r'invite you.{0,60}interview|invitation.{0,40}entretien|schedule.{0,40}interview'),
 ('assessment', r'(?:complete|take|invitation).{0,50}(?:assessment|technical test)|test technique|évaluation technique'),
 ('application', r'your application|votre candidature|application (?:id|reference)|référence.{0,20}candidature'),
]

def text_of(msg):
 parts=[]
 for p in msg.walk():
  if p.get_content_disposition()=='attachment' or p.get_content_type() not in ('text/plain','text/html'): continue
  raw=p.get_payload(decode=True) or b''
  try: text=raw.decode(p.get_content_charset() or 'utf-8',errors='replace')
  except LookupError: text=raw.decode('utf-8',errors='replace')
  if p.get_content_type()=='text/html':
   text=re.sub(r'<(script|style)\b[^>]*>.*?</\1>', '',text,flags=re.S|re.I)
   text=unescape(re.sub('<[^>]+>',' ',text))
  parts.append((p.get_content_type(),text))
 plain=[t for kind,t in parts if kind=='text/plain']
 text='\n'.join(plain or [t for _,t in parts])
 text=re.split(r'(?im)^\s*(?:On .+wrote:|Le .+écrit\s*:|-----Original Message-----)',text)[0]
 return '\n'.join(l for l in text.splitlines() if not l.lstrip().startswith('>'))

def scan(path):
 box=mailbox.mbox(path, factory=lambda f:email.parser.BytesParser(policy=email.policy.default).parse(f))
 rows=[]; seen=set(); relevant_ids=set()
 try:
  for msg in box:
   subject=str(msg.get('Subject','')); sender=str(msg.get('From',''))
   body=text_of(msg); mid=str(msg.get('Message-ID','')).strip()
   key=mid or hashlib.sha256((sender+subject+body).encode()).hexdigest()
   if key in seen: continue
   seen.add(key); hay=subject+'\n'+body
   matches=[name for name,pattern in RULES if re.search(pattern,hay,re.I|re.S)]
   bulk=bool(re.search(r'jobs you might like|job alert|alerte emploi|offres qui pourraient',hay,re.I))
   sender_hint=bool(re.search(r'careers|recruitment|recrutement|greenhouse|workday|lever\.co',sender,re.I))
   route='Relevant' if matches and not (bulk and matches==['application']) else 'Review' if sender_hint or matches else 'Skipped'
   if route=='Relevant' and mid: relevant_ids.add(mid)
   rows.append(dict(subject=subject,sender=sender,body=body[:30000],id=key,refs=str(msg.get('References',''))+' '+str(msg.get('In-Reply-To','')),route=route,evidence=', '.join(matches) or ('Recruitment sender' if sender_hint else 'No rule matched')))
  for r in rows:
   if r['route']=='Skipped' and any(x in relevant_ids for x in r['refs'].split()):r.update(route='Review',evidence='Reply in relevant thread')
 finally:box.close()
 return rows

def main():
 root=tk.Tk();root.title('Applicatron — local email review');root.geometry('1100x760')
 rows=[];approved=[];pool=ThreadPoolExecutor(max_workers=1)
 status=tk.StringVar(value='Choose the .mbox file inside your extracted Gmail Takeout archive.')
 ttk.Label(root,textvariable=status).pack(fill='x',padx=12,pady=8)
 bar=ttk.Frame(root);bar.pack(fill='x')
 tree=ttk.Treeview(root,columns=('route','subject'),show='headings',height=12);tree.heading('route',text='Screening');tree.heading('subject',text='Subject');tree.column('subject',width=800);tree.pack(fill='both',expand=True)
 preview=tk.Text(root,height=10,wrap='word');preview.pack(fill='both',expand=True)
 fields={}
 form=ttk.Frame(root);form.pack(fill='x')
 for i,name in enumerate(('company','role','applied','status')):
  ttk.Label(form,text=name).grid(row=0,column=i)
  v=tk.StringVar(value='Applied' if name=='status' else '');fields[name]=v
  if name=='status':ttk.Combobox(form,textvariable=v,values=['Applied','In progress','Interview','Offer','Rejected','Withdrawn'],state='readonly').grid(row=1,column=i)
  else:ttk.Entry(form,textvariable=v,width=30).grid(row=1,column=i)
 def selected(event=None):
  ids=tree.selection()
  if not ids:return
  r=rows[int(ids[0])];preview.delete('1.0','end');preview.insert('end',r['sender']+'\nEvidence: '+r['evidence']+'\n\n'+r['body'])
  for k,v in fields.items():v.set('Applied' if k=='status' else '')
 tree.bind('<<TreeviewSelect>>',selected)
 def choose():
  path=filedialog.askopenfilename(filetypes=[('Mailbox','*.mbox'),('All files','*')])
  if not path:return
  status.set('Scanning locally… Large archives may take several minutes.');button.config(state='disabled')
  future=pool.submit(scan,path)
  def poll():
   if not future.done():root.after(150,poll);return
   button.config(state='normal')
   try: result=future.result()
   except Exception as e:messagebox.showerror('Import failed',str(e));return
   rows[:]=result;tree.delete(*tree.get_children())
   for i,r in enumerate(rows):tree.insert('', 'end',iid=str(i),values=(r['route'],r['subject']))
   status.set(f'{len(rows)} unique messages; {sum(r["route"]=="Relevant" for r in rows)} relevant; {sum(r["route"]=="Review" for r in rows)} need review. Select an email and confirm application details.')
  root.after(150,poll)
 def approve():
  if not tree.selection():return
  data={k:v.get().strip() for k,v in fields.items()}
  if not data['company'] or not data['role']:messagebox.showerror('Missing details','Company and role are required.');return
  if data['applied']:
   import datetime
   try:datetime.date.fromisoformat(data['applied'])
   except ValueError:messagebox.showerror('Date','Use YYYY-MM-DD or leave empty.');return
  r=rows[int(tree.selection()[0])]
  match=next((a for a in approved if a['company'].casefold()==data['company'].casefold() and a['role'].casefold()==data['role'].casefold()),None)
  if match:
   if not messagebox.askyesno('Existing record','Update the previously approved company/role record?'):return
   match.update({k:v for k,v in data.items() if v})
  else:approved.append(dict(data,id='mail-'+hashlib.sha256((data['company']+data['role']).encode()).hexdigest()[:20],location='',url='',windowDays='',windowEnd='',followUp='',notes='Reviewed email: '+r['subject']))
  status.set(f'{len(approved)} applications approved for export.')
 def export():
  if not approved:return
  path=filedialog.asksaveasfilename(defaultextension='.json',initialfile='applications-reviewed.json')
  if path:
   with open(path,'w',encoding='utf-8') as f:json.dump({'version':1,'applications':approved},f,ensure_ascii=False,indent=2)
   status.set('Exported. In Applicatron, use Import backup. Import replaces its current list; export a backup first.')
 button=ttk.Button(bar,text='Open Takeout .mbox',command=choose);button.pack(side='left',padx=8)
 ttk.Button(bar,text='Approve application / update',command=approve).pack(side='left')
 ttk.Button(bar,text='Export approved JSON',command=export).pack(side='left',padx=8)
 root.mainloop();pool.shutdown(wait=False,cancel_futures=True)
if __name__=='__main__':main()
