# AGENTS.md - Testing Skills Collection

## Project Overview

AI Agent Testing Skills Collection for iFlow CLI. 11 skills for software testing lifecycle.

**Tech Stack**: Python 3.10+, Playwright, pandas, openpyxl, python-docx

---

## Build/Lint/Test Commands

### Setup
```bash
pip install pandas openpyxl python-docx playwright
playwright install chromium
```

### Validation (Test Suite)
```bash
# Validate single test case
python testcase-generator/scripts/validate.py --single "test-case/ITEM/POINT.md"

# Validate entire directory
python testcase-generator/scripts/validate.py "test-case/"

# Check duplicates
python testcase-generator/scripts/validate.py "test-case/" --check-duplicates
```

### Export Commands
```bash
# To Excel
python testcase-generator/scripts/to_excel.py "test-case/" -o "export.xlsx"

# To XMind
python testcase-generator/scripts/testcase_to_xmind.py "test-case/"

# Effort estimation
python test-effort-estimator/scripts/generate_excel.py
```

### Skill Evaluation
```bash
python skill-creator/scripts/run_eval.py
python skill-creator/scripts/quick_validate.py
```

### Web Testing
```bash
python webapp-testing/scripts/with_server.py --server "npm run dev" --port 5173 -- python test.py
```

---

## Code Style Guidelines

### Python

**Imports**: Standard → third-party → local, blank lines between groups
```python
import os
import sys

import pandas as pd
from openpyxl import Workbook

from . import local_module
```

**Formatting**: 4 spaces, max 120 chars per line
```python
# Good
result = func(arg1, arg2,
              arg3=default)

# Bad
result = func(arg1, arg2, arg3=default)
```

**Types**: Use type hints for function signatures
```python
def process(path: str) -> dict[str, Any]:
    ...
```

**Naming**:
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private: `_leading_underscore`

**Error Handling**: Always catch specific exceptions
```python
try:
    result = risky()
except ValueError as e:
    logger.error(f"Invalid: {e}")
    raise
```

### SKILL.md Format

Required YAML frontmatter:
```yaml
---
name: skill-name
description: When to trigger and what it does
---
```

### Test Case Format (v0.2)

```markdown
## [P0] Test case title
[Test type] Function
[Precondition] User logged in
[Steps] 1. Open page. 2. Click button.
[Expected] 1. Show success message.
```

**Priority**: P0 > P1 > P2 > P3

**Test Types (12)**: 功能, 兼容性, 易用性, 性能, 稳定性, 安全性, 可靠性, 效果(AI类), 效果(硬件器件类), 可维护性, 可移植性, 埋点

---

## Directory Structure

```
skill-name/
├── SKILL.md           # Required: definition + YAML frontmatter
├── references/       # Optional: documentation
├── scripts/           # Optional: Python utilities
├── templates/         # Optional: templates
├── assets/            # Optional: resources
└── examples/         # Optional: examples
```

---

## Key Skills

| Skill | Purpose | Commands |
|-------|---------|----------|
| `testcase-generator` | Generate test cases | validate.py, to_excel.py |
| `testcase-planner` | Create test plans | parse_plan.py |
| `requirements-analyzer` | Extract from Excel/PDF/PNG | - |
| `analyze-requirements` | Orchestrate requirements | - |
| `agent-browser` | Browser automation | npx agent-browser |
| `webapp-testing` | Playwright testing | with_server.py |
| `skill-creator` | Create/evaluate skills | run_eval.py |
| `test-effort-estimator` | Estimate effort | generate_excel.py |
| `lanhu-design` | Lanhu/Axure prototypes | MCP Server |

---

## Environment Variables

- `LANHU_COOKIE`: Blue Lake auth (`.claude/settings.json`)
- `AGENT_BROWSER_*`: Browser automation settings

---

## Workflow

```
Requirements → Test Planning → Case Gen → Execution
(requirements-analyzer) (testcase-planner) (testcase-generator) (webapp-testing)
```

**Last Updated**: 2026-03-25
