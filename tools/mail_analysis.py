"""Conservative candidate extraction and optional on-device semantic screening."""
import re
from pathlib import Path
PATTERNS = [
 r'(?:application|applied|applying)\s+for\s+(?:the\s+)?(?P<role>[^\n.!?]{2,100}?)\s+at\s+(?P<company>[^\n.!?;,]{2,80})',
 r'applying\s+to\s+(?P<company>[^\n.!?]{2,80}?)\s+for\s+(?:the\s+)?(?P<role>[^\n.!?]{2,100}?)(?:\s+(?:position|role)|[.!?\n]|$)',
 r'(?:candidature|postulé)\s+(?:au poste de|pour le poste de)\s+(?P<role>[^\n.!?]{2,100}?)\s+chez\s+(?P<company>[^\n.!?;,]{2,80})',
 r'(?:role of|position of|poste de)\s+(?P<role>[^\n.!?;,]{2,100})',
]
INTERMEDIARIES={'linkedin','workday','greenhouse','indeed','lever','smartrecruiters','talentsoft'}
JOB_WORDS=r'analyst|engineer|intern|consultant|manager|developer|officer|specialist|assistant|ingénieur|stagiaire|stage|analyste|développeur|responsable|technicien|auditeur'
def _legacy_extract(subject, body, sender=''):
 candidates=[]
 for source,text in [('subject',subject),('body',body)]:
  for pattern in PATTERNS:
   for m in re.finditer(pattern,text,re.I):
    d={k:re.sub(r'\s+',' ',v).strip(' \"“”') for k,v in m.groupdict().items() if v}
    if 'role' in d:d['role']=re.split(r'\s+(?:at|chez)\s+',d['role'],flags=re.I)[0]
    if 'role' in d and not re.search(JOB_WORDS,d['role'],re.I):continue
    company=d.get('company','')
    if company.casefold() in INTERMEDIARIES or re.search(r'@|https?://|\b\d{1,2}:\d{2}\b',company):d.pop('company',None)
    if company and re.search(r'\b(?:we|you|your|our|on|with)\b',company,re.I):d.pop('company',None)
    d.update(evidence=m.group(0),source=source);candidates.append(d)
 # Delimited subject candidates require job vocabulary and application context.
 if re.search(r'application|candidature',subject,re.I):
  chunks=re.split(r'\s+[—–|]\s+|\s+-\s+',subject)
  if len(chunks)>=3 and re.search(JOB_WORDS,chunks[1],re.I) and chunks[0].casefold() not in INTERMEDIARIES:
   candidates.append(dict(company=chunks[0].strip(),role=chunks[1].strip(),source='subject',evidence=subject))
 result={'company':'','role':'','evidence':[],'conflict':False}
 for field in ('company','role'):
  values={c[field].casefold():c[field] for c in candidates if c.get(field)}
  if len(values)==1:result[field]=next(iter(values.values()))
  elif len(values)>1:result['conflict']=True
 result['evidence']=[c['evidence'] for c in candidates]
 return result

EXAMPLES={
 'confirmation':['We received your application for this position.','Nous avons bien reçu votre candidature.'],
 'rejection':['We will not proceed with your application.','Votre candidature n’a pas été retenue.'],
 'interview':['We invite you to an interview for this role.','Nous vous proposons un entretien de recrutement.'],
 'assessment':['Please complete this technical assessment for your application.','Veuillez réaliser ce test technique de recrutement.'],
 'unrelated':['Here are new jobs you might like.','Découvrez nos offres et notre newsletter.','Your order has shipped.','Your account security code.']}
class MiniLMScreener:
 def __init__(self, model_path, device="cpu"):
  from sentence_transformers import SentenceTransformer
  self.model=SentenceTransformer(str(model_path),local_files_only=True,device=device)
  self.labels=[label for label,examples in EXAMPLES.items() for _ in examples]
  self.prototypes=self.model.encode([s for examples in EXAMPLES.values() for s in examples],normalize_embeddings=True)
 def screen(self,text):
  # Sentence-sized windows avoid silently discarding the end of long messages.
  chunks=re.findall(r'.{1,600}(?:\s|$)',text,flags=re.S) or [text]
  embeddings=self.model.encode(chunks[:100],normalize_embeddings=True,batch_size=16)
  scores=embeddings @ self.prototypes.T
  ranked=sorted(((label,float(scores[:,[i for i,l in enumerate(self.labels) if l==label]].max())) for label in EXAMPLES),key=lambda x:x[1],reverse=True)
  label,score=ranked[0];margin=score-ranked[1][1]
  # Heuristic thresholds, not calibrated confidence probabilities. Never auto-apply.
  return {'label':label,'similarity':round(score,3),'margin':round(margin,3),'uncertain':score<.55 or margin<.08,'truncated':len(chunks)>100}



def recruitment_hint(subject, body=''):
 return bool(re.search(r'candidature|demande de stage|stage pfe|application|recruitment|recrutement|interview|entretien|pre.sales|received your project|technical (?:test|assessment)', subject+'\n'+body, re.I))

def obvious_bulk(subject):
 return bool(re.search(r'jobs matching your criteria|job alert|nouvelles offres|nouvelles opportunit|others are hiring|accepted your invitation|wants to connect|recently posted|security alert|newsletter|password reset|reset your password',subject,re.I))

def extract(subject, body, sender=''):
 from html import unescape
 def clean(t):return re.sub(r'[ \t]+',' ',unescape(t).replace('\u200b','').replace('\u202f',' ').replace('\xa0',' ')).strip()
 subject,body=clean(subject),clean(body)
 result=_legacy_extract(subject,body,sender)
 def employer(v):return 1<len(v)<=150 and not re.search(r'candidature|application|poste|stage|received|thank|https?://|@',v,re.I) and v.lower() not in INTERMEDIARIES
 if not employer(result['company']):result['company']=''
 companies=[]
 for pattern in [r'^(.{2,100}?)\s+[—–-]\s+(?:Votre candidature|Your application)',r'^Candidature (.{2,100}?) reçue',r'\[([^]\n]+)\]$']:
  m=re.search(pattern,subject,re.I)
  if m and employer(m[1].strip()):companies.append(m[1].strip())
 if len(set(companies))==1:
  result['company']=companies[0];result['evidence'].append(subject)
 # Subject fields are bounded by the subject itself; commas belong to role names.
 m=re.search(r'(?:poste (?:de\s+)?|position of\s+|role of\s+)(.+)$',subject,re.I)
 if m:
  role=m[1].strip(' \"“”');role=re.sub(r'\s+chez\s+.*$','',role,flags=re.I)
  if re.search(JOB_WORDS,role,re.I) and len(role)<=250:
   result['role']=role;result['evidence'].append(subject)
 result['role']=re.sub(r'\s+(?:position|role)$','',result['role'],flags=re.I)
 return result
