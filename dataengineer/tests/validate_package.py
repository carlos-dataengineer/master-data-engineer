from pathlib import Path
import json, tomllib

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT.parent / 'VERSION'
EXPECTED_VERSION = VERSION_FILE.read_text(encoding='utf-8').strip() if VERSION_FILE.exists() else None
errors = []

for manifest in [ROOT / '.claude-plugin/plugin.json', ROOT / '.codex-plugin/plugin.json']:
    try:
        data = json.loads(manifest.read_text(encoding='utf-8'))
        assert data['name'] == 'dataengineer'
        assert EXPECTED_VERSION is None or data['version'] == EXPECTED_VERSION, f"versão {data['version']} != VERSION {EXPECTED_VERSION}"
        assert data['skills'] == './skills/'
    except Exception as exc:
        errors.append(f'{manifest}: {exc}')

skill_path = ROOT / 'skills/dataengineer/SKILL.md'
content = skill_path.read_text(encoding='utf-8')
assert content.startswith('---\nname: dataengineer\n'), 'Frontmatter/skill name is missing'
for phrase in ['Construir um pipeline do zero', 'Revisar um pipeline existente', 'Corrigir um bug']:
    if phrase.lower() not in content.lower():
        errors.append(f'Skill missing required mode phrase: {phrase}')

claude_agents = list((ROOT / 'agents').glob('*.md'))
codex_agents = list((ROOT / '.codex/agents').glob('*.toml'))
if len(claude_agents) != 8:
    errors.append(f'Expected 8 Claude agents; found {len(claude_agents)}')
if len(codex_agents) != 8:
    errors.append(f'Expected 8 Codex agents; found {len(codex_agents)}')

memory_script = ROOT / 'skills/dataengineer/scripts/contextual_memory.py'
memory_reference = ROOT / 'skills/dataengineer/references/CONTEXTUAL-LEARNING.md'
board_script = ROOT / 'skills/dataengineer/scripts/team_board.py'
panel = ROOT / 'skills/dataengineer/assets/painel.html'
for required in (board_script, panel, ROOT / 'skills/dataengineer/agents/openai.yaml'):
    if not required.is_file():
        errors.append(f'Missing {required.relative_to(ROOT)}')
if panel.is_file() and '/*__MDE_CONFIG__*/null' not in panel.read_text(encoding='utf-8'):
    errors.append('Panel config placeholder is missing')
if 'team_board.py' not in content:
    errors.append('Skill does not describe the team board protocol')
if not memory_script.is_file():
    errors.append('Contextual memory script is missing')
if not memory_reference.is_file():
    errors.append('Contextual learning reference is missing')
if 'Contextual Learning Engine' not in content:
    errors.append('Skill does not reference Contextual Learning Engine')
import py_compile
for script in (memory_script, board_script):
    if script.is_file():
        try:
            py_compile.compile(str(script), doraise=True)
        except Exception as exc:
            errors.append(f'{script.name} does not compile: {exc}')

for agent in codex_agents:
    try:
        data = tomllib.loads(agent.read_text(encoding='utf-8'))
        assert data.get('name') and data.get('description') and data.get('developer_instructions')
    except Exception as exc:
        errors.append(f'{agent}: invalid TOML or required field missing: {exc}')

if errors:
    print('FAIL')
    print('\n'.join(errors))
    raise SystemExit(1)
print('PASS: manifests, skill activation contract, 8 Claude/Codex agent profiles, contextual memory and team board artifacts are valid.')
