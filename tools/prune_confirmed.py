"""Remove only old local media with durable Instagram publication receipts.
A two-part story is retained until both parts have confirmed receipts.
Never rewrites Git history or deletes scripts, queues, receipts or future media.
"""
import argparse,json,re,subprocess
from pathlib import Path
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[1]


def candidates(root=ROOT,now=None):
 root=Path(root);now=now or datetime.now(timezone.utc)
 ledger=root/'conteudo/publicados.json'
 if not ledger.exists():return []
 confirmed={}
 for item in json.loads(ledger.read_text()):
  if item.get('ensaio') or item.get('dry_run'):continue
  if not (item.get('instagram_media_id') or item.get('media_id')):continue
  try:
   stamp=datetime.fromisoformat(item.get('publicado_em') or item['quando'])
   if stamp.tzinfo is None:continue
  except (KeyError,ValueError,TypeError):continue
  if now-stamp>=timedelta(days=7):confirmed[str(item['id'])]=stamp
 result=[]
 for ident in confirmed:
  if not re.fullmatch(r'(?:ep\d+-p[12]|EP-\d+)',ident):continue
  pair=re.fullmatch(r'(ep\d+)-p[12]',ident)
  if pair and not all(pair[1]+'-p'+n in confirmed for n in ('1','2')):continue
  for suffix in ('.mp4','-story.mp4','-capa.jpg','.hash','-render.json','.production.json'):
   file=root/'reels'/(ident+suffix)
   if file.is_file():result.append(file)
 return sorted(set(result))

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');a=ap.parse_args()
 files=candidates()
 if a.apply:
  for file in files:file.unlink()
 print(json.dumps({'eligible':len(files),'removed':len(files) if a.apply else 0}))
