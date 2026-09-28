import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tablelib import *
import sys
sys.stdout.reconfigure(encoding='utf-8')
p=ROOT/'vendor/fusion/megaten-fusion-tool-master/src/app/p5/data'
sk=json.loads((p/'skill-data.json').read_text());sk.update(json.loads((p/'roy-skill-data.json').read_text()))
ss=segments((ROOT/'input/SC-NAME.TBL').read_bytes()); ns=names(ss,1)
for key,s in sk.items():
 i=int(key)
 if i<len(ns):
  print(i,decode(ns[i]),json.dumps(s,ensure_ascii=False))
