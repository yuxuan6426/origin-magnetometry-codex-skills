"""Refresh explicit skill and complete-repository delivery allowlists."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {'.git','.venv','runs','.local','__pycache__','build','dist'}


def public_files(directory):
    return sorted(p for p in directory.rglob('*') if p.is_file()
                  and not any(part in EXCLUDED or part.endswith('.egg-info') for part in p.relative_to(directory).parts)
                  and p.suffix not in {'.pyc','.zip'} and not p.name.startswith('.env'))


def main():
    skill = ROOT / 'skills/origin-mpms-import'
    files = [p.relative_to(skill).as_posix() for p in public_files(skill) if p.name != 'delivery.json']
    requirements = [
        {'id':'complete-repository','kind':'host','handling':'Keep this skill inside the complete repository/plugin, including root scripts, cases and third_party. A folder-only skill export provides conversion helpers but not the repository-owned Origin pipeline.'},
        {'id':'python-runtime','kind':'rebuild','handling':'Run the repository scripts/bootstrap.ps1 with Python 3.13.9 on Windows x64; requirements-win64.lock.txt pins the validated native environment. Conversion-only uses requirements.txt.'},
        {'id':'origin-desktop','kind':'host','handling':'Provide licensed, activated Origin/OriginPro. Native validation is measured on OriginPro 2026 10.30018; doctor never connects to it.'},
        {'id':'origin-mcp','kind':'bundle','handling':'The complete repository includes third_party/origin-mcp at ddab4420ccc7d17c056285b3b75191b1b81e48e5 with upstream MIT/NOTICE and a byte-level provenance manifest.'},
        {'id':'input-and-mass','kind':'input','handling':'Supply an MPMS3 measurement DAT and explicitly confirmed sample mass in mg, or raw emu. Named cases use their catalog settings.'},
        {'id':'owned-session','kind':'configure','handling':'The adapter generates a private per-run loopback endpoint and authenticated handshake; no shared session or token is used.'},
        {'id':'other-origin-versions','kind':'unsupported','handling':'Origin 2018-2025, non-Windows native plotting, independent machines and clean operating systems have not been hardware validated.'},
    ]
    version = json.loads((ROOT / 'plugin.json').read_text(encoding='utf-8'))['version']
    (skill / 'delivery.json').write_text(json.dumps({'schema_version':1,'name':'origin-mpms-import','version':version,
                                                  'files':files,'requirements':requirements},indent=2)+'\n',encoding='utf-8')
    records = [{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
               for p in public_files(ROOT) if p.name not in {'repository-delivery.json','SHA256SUMS','SHA256SUMS.txt'}]
    (ROOT / 'repository-delivery.json').write_text(json.dumps({'schema_version':1,'name':'origin-magnetometry-codex-skills','version':version,
                                                              'files':records,'requirements':requirements},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'skill_files':len(files),'repository_files':len(records)}))


if __name__ == '__main__':
    main()
