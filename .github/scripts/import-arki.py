#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

BUNDLE=Path('ARKI_Project_v2.0_git.bundle')
BUNDLE_SHA256='d4fbef1223c2bfe91a9d3809ce9977ec04b10d0a097e3725b94ff13c1110df90'
SOURCE_COMMIT='c57919e8181ee27698e16f8c4427b35904b06b8a'
SOURCE_REF='refs/remotes/arki-import/main'
SOURCE_COUNT=195

def git(*args): return subprocess.check_output(['git',*args],text=True).strip()
def run(*args): subprocess.run(args,check=True)
def require(ok,msg):
    if not ok: raise RuntimeError(msg)

def source_tree():
    raw=subprocess.check_output(['git','ls-tree','-rz','-r',SOURCE_COMMIT]);out={}
    for entry in raw.split(b'\0'):
        if not entry: continue
        meta,name=entry.decode().split('\t',1);mode,kind,sha=meta.split()
        require(kind=='blob' and mode in ('100644','100755'),'Unsupported tree entry')
        require(not name.startswith('/') and '..' not in Path(name).parts,'Unsafe path')
        out[name]=(mode,sha)
    require(len(out)==SOURCE_COUNT,'Unexpected source file count')
    return out

def verify_files():
    expected=source_tree();actual={}
    raw=subprocess.check_output(['git','ls-files','--stage','-z'])
    for entry in raw.split(b'\0'):
        if not entry: continue
        meta,name=entry.decode().split('\t',1);mode,sha,stage=meta.split()
        require(stage=='0','Unresolved merge conflict');actual[name]=(mode,sha)
    for name,item in expected.items(): require(actual.get(name)==item,f'Source changed or missing: {name}')
    run('git','diff','--exit-code','--',*sorted(expected))

def prepare():
    require(BUNDLE.is_file(),f'Upload {BUNDLE.name} to repository root first')
    require(hashlib.sha256(BUNDLE.read_bytes()).hexdigest()==BUNDLE_SHA256,'Bundle SHA-256 mismatch')
    require(not Path('app').exists(),'An app already exists; refusing overwrite')
    require(not git('status','--porcelain'),'Working tree must be clean')
    run('git','bundle','verify',str(BUNDLE))
    run('git','fetch','--no-tags',str(BUNDLE.resolve()),f'refs/heads/main:{SOURCE_REF}')
    require(git('rev-parse',SOURCE_REF)==SOURCE_COMMIT,'Unexpected bundle commit')
    require(not set(git('ls-files').splitlines()).intersection(source_tree()),'Existing files overlap import')
    run('git','merge','--no-commit','--no-ff','--allow-unrelated-histories',SOURCE_REF)
    run('git','rm','--force','--',str(BUNDLE));verify_files()

def finish():
    require(git('rev-parse','MERGE_HEAD')==SOURCE_COMMIT,'Expected import merge is not active');verify_files()
    report={'version':'2.0.0','source_commit':SOURCE_COMMIT,'bundle_sha256':BUNDLE_SHA256,'source_files':SOURCE_COUNT,'imported_at_utc':datetime.now(timezone.utc).isoformat(),'source_blobs_match':True,'checks':['npm test','npm run test:web'],'check_result':'passed before commit','note':'Source import only; no hosting deployment, live retailer feeds or household-data synchronization.'}
    Path('docs/GITHUB_IMPORT.json').write_text(json.dumps(report,indent=2)+'\n')
    Path('README.md').write_text('''# ARKI — Nordic 2.0 Result Hub\n\nОсновной проект импортирован. Проверенный snapshot: `c57919e8181ee27698e16f8c4427b35904b06b8a`.\n\n## Быстрый запуск\n\n```sh\ncd app\nnpm run build\nnpm run demo\n```\n\nОткройте `http://127.0.0.1:8080`.\n\n## ARKI 2.0\n\nGuided onboarding ведёт через профиль, магазины, дни готовки, бюджет, предпочтения, кухню и pantry. После генерации открывается Result Hub: блюда недели, корзина и Real Cost выбранных магазинов. Блюдо можно заменить прямо в результате; Planner v4, shopping list и store ranking пересчитываются сразу.\n\nОсновные исходники: `app/web/src/`; готовый HTML в `app/web/dist/` — результат сборки. Карта/GPS: `nearby.js`; цены и Real Cost: `pricing.js` и `commerce-ui.js`; Result Hub/onboarding: `app.js` и `onboarding.css`.\n\nЖивые retailer feeds, production-hosting и семейная server sync Nordic-клиента не подключены. Demo prices остаются вымышленными. Возможный K-ryhmä pilot не является подтверждённым партнёрством.\n''')
    run('git','add','README.md','docs/GITHUB_IMPORT.json');run('git','commit','-m','Import verified ARKI Nordic 2.0 result hub');print(git('rev-parse','HEAD'))

if __name__=='__main__':
    try:
        require(len(sys.argv)==2 and sys.argv[1] in ('prepare','finish'),'Usage: import-arki.py prepare|finish')
        {'prepare':prepare,'finish':finish}[sys.argv[1]]()
    except (RuntimeError,OSError,subprocess.CalledProcessError) as exc:
        print(f'ARKI import failed: {exc}',file=sys.stderr);raise SystemExit(1)
