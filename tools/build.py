"""Build with a Holly source checkout and emit an import-only ZIP."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import zipfile

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--framework',type=Path,default=root.parent/'framework')
parser.add_argument('--zip',type=Path,default=root.parent/'exports/医学科学素养Ⅱ_Holly_20261107.zip')
args=parser.parse_args()
sys.path.insert(0,str(args.framework.resolve()/'src'))
os.chdir(root)
from ginkgo.bank import Bank
from ginkgo.core import main_generator
bank=Bank(root)
main_generator(with_json=True)
site=root/'site'
manifest=json.loads((site/'holly/manifest.json').read_text(encoding='utf-8'))
assert {v['path'] for v in manifest['versions']}=={p for b in manifest['bundles'] for p in b['versions']}
paths=['holly/manifest.json']+[f"holly/{b['path']}" for b in manifest['bundles']]
paths.extend(p.relative_to(site).as_posix() for p in (site/'holly/assets').rglob('*') if p.is_file())
index=json.loads((site/'index.json').read_text(encoding='utf-8'))
(root/'index.json').write_bytes(json.dumps({'website':index['website']},ensure_ascii=False,separators=(',',':')).encode())
for rel in paths:
    dst=root/rel;dst.parent.mkdir(parents=True,exist_ok=True)
    data=(site/rel).read_bytes()
    if rel=='holly/manifest.json':data=data.replace(b'\r\n',b'\n')
    dst.write_bytes(data)
for bundle in manifest['bundles']:
    data=(root/'holly'/bundle['path']).read_bytes()
    assert hashlib.sha256(data).hexdigest()==bundle['sha256']
    assert b'\n' not in data and b'\r' not in data,'Keep bundles native-HTTP compatible'
args.zip.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(args.zip,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for rel in ['index.json']+sorted(paths):z.write(root/rel,rel)
digest=hashlib.sha256(args.zip.read_bytes()).hexdigest()
args.zip.with_suffix('.sha256').write_text(f'{digest}  {args.zip.name}\n',encoding='utf-8')
print(json.dumps({'papers':len(manifest['exams']),'versions':len(manifest['versions']),'zip':str(args.zip),'bytes':args.zip.stat().st_size,'sha256':digest},ensure_ascii=False))
