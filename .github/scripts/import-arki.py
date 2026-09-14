#!/usr/bin/env python3
"""Import the reviewed ARKI bundle without rewriting remote history.

Run prepare, then the project's tests, then finish. Only the pinned, SHA-256
verified snapshot is accepted. No archive paths are extracted and no secrets
are needed by this script. Authentication is supplied by GitHub Actions.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BUNDLE = Path('ARKI_Project_v1.7_git.bundle')
BUNDLE_SHA256 = 'ada39d2d62ab33dbab0e8d3eac79c46ea6413027244010b2dc71c1ef529d0fca'
SOURCE_COMMIT = '4b8d7b0a1d9a214158f69ae0088ebac8cf2f1d61'
SOURCE_REF = 'refs/remotes/arki-import/main'
SOURCE_COUNT = 188


def git(*args: str) -> str:
    return subprocess.check_output(['git', *args], text=True).strip()


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def source_tree() -> dict[str, tuple[str, str]]:
    raw = subprocess.check_output(['git', 'ls-tree', '-rz', SOURCE_COMMIT])
    result = {}
    for entry in raw.split(b'\0'):
        if not entry:
            continue
        meta, name = entry.decode('utf-8').split('\t', 1)
        mode, kind, sha = meta.split()
        require(kind == 'blob' and mode in ('100644', '100755'), 'Unsupported tree entry')
        require(not name.startswith('/') and '..' not in Path(name).parts, 'Unsafe path')
        result[name] = (mode, sha)
    require(len(result) == SOURCE_COUNT, 'Unexpected source file count')
    return result


def verify_imported_files() -> None:
    expected = source_tree()
    raw = subprocess.check_output(['git', 'ls-files', '--stage', '-z'])
    actual = {}
    for entry in raw.split(b'\0'):
        if not entry:
            continue
        meta, name = entry.decode('utf-8').split('\t', 1)
        mode, sha, stage = meta.split()
        require(stage == '0', 'Unresolved merge conflict')
        actual[name] = (mode, sha)
    for name, item in expected.items():
        require(actual.get(name) == item, f'Source file changed or missing: {name}')
    run('git', 'diff', '--exit-code', '--', *sorted(expected))


def prepare() -> None:
    require(BUNDLE.is_file(), f'Upload {BUNDLE.name} to the repository root first')
    require(hashlib.sha256(BUNDLE.read_bytes()).hexdigest() == BUNDLE_SHA256,
            'Bundle SHA-256 mismatch; refusing import')
    require(not Path('app').exists(), 'An app already exists; refusing to overwrite it')
    require(not git('status', '--porcelain'), 'Working tree must be clean')
    run('git', 'bundle', 'verify', str(BUNDLE))
    run('git', 'fetch', '--no-tags', str(BUNDLE.resolve()), f'refs/heads/main:{SOURCE_REF}')
    require(git('rev-parse', SOURCE_REF) == SOURCE_COMMIT, 'Unexpected bundle commit')
    files = source_tree()
    current = set(git('ls-files').splitlines())
    require(not current.intersection(files), 'Existing files overlap the imported project')
    run('git', 'merge', '--no-commit', '--no-ff', '--allow-unrelated-histories', SOURCE_REF)
    run('git', 'rm', '--force', '--', str(BUNDLE))
    verify_imported_files()
    print(f'Prepared {SOURCE_COUNT} source files. Run npm test and npm run test:web before finish.')


def finish() -> None:
    require(git('rev-parse', 'MERGE_HEAD') == SOURCE_COMMIT, 'Expected import merge is not active')
    verify_imported_files()
    report = {
        'source_commit': SOURCE_COMMIT,
        'bundle_sha256': BUNDLE_SHA256,
        'source_files': SOURCE_COUNT,
        'imported_at_utc': datetime.now(timezone.utc).isoformat(),
        'source_blobs_match': True,
        'checks': ['npm test', 'npm run test:web'],
        'check_result': 'passed before commit',
        'note': 'Source import only; no hosting deployment or family-data synchronization.'
    }
    Path('docs/GITHUB_IMPORT.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    Path('README.md').write_text('''# ARKI — Nordic 1.7

**Основной проект импортирован.** Сохранены все 188 файлов подготовленного
снимка и его исходный коммит `4b8d7b0a1d9a214158f69ae0088ebac8cf2f1d61`.
Импорт прошёл проверки `npm test` и `npm run test:web` перед коммитом.

## Быстрый запуск

Нужен Node.js 22.16 или новее. На Windows запустите
`START_ARKI_WINDOWS.cmd`, либо выполните:

```sh
cd app
npm run build
npm run demo
```

Откройте `http://127.0.0.1:8080` на том же компьютере.

## Где продолжать разработку

- Актуальный интерфейс, логика и стили: `app/web/src/`.
- Изображения: `app/web/assets/`.
- Сборка: `app/web/build.mjs`, шаблон: `app/web/index.html`.
- Сохранённый закрытый серверный пилот: `app/pilot/`.
- Правила разработки: [AGENTS.md](AGENTS.md).
- Полная инструкция: [README_RU.md](README_RU.md).
- Отчёт импорта: [docs/GITHUB_IMPORT.json](docs/GITHUB_IMPORT.json).

HTML является результатом сборки, не единственным исходником проекта.

## Текущие ограничения

Публикация сайта не выполнялась. Nordic-клиент сохраняет данные в браузере;
его семейная серверная синхронизация ещё не подключена. Закрытый пилот
работает отдельно и допускает только вымышленные тестовые данные.
Автоматические цены магазинов и подтверждённое партнёрство с K-ryhmä
отсутствуют. Примерные цены отделены от личных записей пользователя.
Не добавляйте ключи, базы, приглашения и рабочие .env-файлы в Git.

Исходные отчёты и README_RU.md сохранены без правок и описывают состояние
до отправки в GitHub. Этот README и отчёт импорта фиксируют новую отправку.
''', encoding='utf-8')
    run('git', 'add', 'README.md', 'docs/GITHUB_IMPORT.json')
    run('git', 'commit', '-m', 'Import verified ARKI Nordic 1.7 project and preserve source history')
    print(git('rev-parse', 'HEAD'))


if __name__ == '__main__':
    try:
        require(len(sys.argv) == 2 and sys.argv[1] in ('prepare', 'finish'),
                'Usage: python3 .github/scripts/import-arki.py prepare|finish')
        {'prepare': prepare, 'finish': finish}[sys.argv[1]]()
    except (RuntimeError, OSError, subprocess.CalledProcessError) as exc:
        print(f'ARKI import failed: {exc}', file=sys.stderr)
        raise SystemExit(1)
