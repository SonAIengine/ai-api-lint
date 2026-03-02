<div align="center">

# ai-api-lint

**AI-friendly API linter for OpenAPI specifications**

Analyze your API specs for LLM/agent readability.
Get an AI-readiness score, auto-fix common issues, and generate shareable HTML reports.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

English · [한국어](README-ko.md)

</div>

---

## Why?

LLM agents are increasingly calling APIs via tool-use. But most OpenAPI specs were written for human developers, not AI:

- **Missing descriptions** — the agent doesn't know *when* to call the endpoint
- **No error responses** — the agent can't handle failures gracefully
- **Vague parameters** — the agent guesses wrong values
- **No schema types** — the agent sends malformed requests

**ai-api-lint** scores your spec from 0–100 and tells you exactly what to fix, organized by 7 categories across 30+ rules. It can even **auto-fix** the most common problems.

### Real-World Example

We ran ai-api-lint on a production commerce API (1,083 operations):

```
Score: 71.2 / Fair
4,195 findings (1,058 errors, 2,570 warnings, 567 info)

Top issues:
  AI042  No 4xx error response          1,058 ops
  AI013  No usage hint in description   1,045 ops
  AI034  Request body no description      449 ops
```

After `--fix`: **71.2 → 85+ (Good)**, with 3,500+ issues auto-resolved.

## Install

```bash
pip install ai-api-lint

# Optional: YAML support
pip install ai-api-lint[yaml]
```

## Quick Start

```bash
# Analyze your spec
ai-api-lint openapi.json

# Output example:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
#  POST /users  •  createUser
#   ✗ AI042  No 4xx client error response defined.
#   ⚠ AI034  Request body has no 'description'.
#   ⚠ AI014  Parameter 'name' has no description.
#
#  Overall Score: 71.2 / Fair
#  42 operations, 156 findings (12 errors, 98 warnings, 46 info)
```

## Usage

### Lint

```bash
# Basic
ai-api-lint openapi.json

# JSON output (for CI/CD pipelines)
ai-api-lint openapi.json --format json

# Fail CI if score is below threshold
ai-api-lint openapi.json --min-score 70

# Filter by severity
ai-api-lint openapi.json --severity warning   # errors + warnings only
ai-api-lint openapi.json --severity error     # errors only

# List all available rules
ai-api-lint --list-rules
```

### Auto-Fix

The `--fix` flag automatically resolves common issues in your spec:

```bash
# Fix and show results (stdout)
ai-api-lint openapi.json --fix

# Save the fixed spec to a new file
ai-api-lint openapi.json --fix --output fixed.json

# Only apply safe fixes (Level 1 — no guessing)
ai-api-lint openapi.json --fix --level 1

# Preview what would be fixed, without modifying anything
ai-api-lint openapi.json --fix --dry-run
```

#### Fix Levels

| Level | Name | What it does | Example |
|-------|------|-------------|---------|
| **1** | Safe | Adds missing boilerplate data only | `"400": {"description": "Bad Request"}` |
| **2** | Inferred | Generates content from method/path/tags | `"summary": "GET /users (accounts)"` |

Level 1 is always safe — it never changes existing data, only fills in gaps.
Level 2 makes educated guesses based on patterns. Review the output before committing.

#### 14 Built-in Fixers

Ordered by typical impact (number of issues resolved):

| Fixer | Rule | Level | What it does | Typical impact |
|-------|------|-------|-------------|----------------|
| FixAI042 | AI042 | L1 | Add `400: Bad Request` when no 4xx response | ~1,000 ops |
| FixAI034 | AI034 | L2 | Generate requestBody description from operationId/summary | ~450 ops |
| FixAI031 | AI031 | L1 | Add empty `properties: {}` to schema | ~430 ops |
| FixAI014 | AI014 | L2 | Generate parameter description from name + type | ~370 ops |
| FixAI022 | AI022 | L1 | Add `schema: {type: string}` to untyped params | ~320 ops |
| FixAI010 | AI010 | L2 | Generate summary from `METHOD /path (tags)` | ~200 ops |
| FixAI041 | AI041 | L1 | Add `{type: object}` schema to success response | ~190 ops |
| FixAI032 | AI032 | L1 | Add empty `required: []` array to schema | ~120 ops |
| FixAI043 | AI043 | L1 | Add status-text description to error responses | ~95 ops |
| FixAI053 | AI053 | L1 | Add tag from first meaningful path segment | ~87 ops |
| FixAI011 | AI011 | L2 | Augment short descriptions with path/method info | ~63 ops |
| FixAI001 | AI001 | L2 | Generate `operationId` as `{method}_{path_slug}` | varies |
| FixAI033 | AI033 | L1 | Add `application/json` content type to requestBody | ~10 ops |
| FixAI040 | AI040 | L1 | Add `200: OK` or `201: Created` when no 2xx | ~5 ops |

### HTML Report

Generate a self-contained, single-file HTML report — no external dependencies, easy to share with your team:

```bash
# Generate report
ai-api-lint openapi.json --format html --output report.html

# Generate report with fix results included
ai-api-lint openapi.json --fix --format html --output report.html

# Open in browser
open report.html
```

#### What's in the report:

| Section | Description |
|---------|-------------|
| **Score gauge** | Overall score (0–100) with letter grade and SVG arc |
| **Category bars** | Finding count per category (Description, Response, etc.) |
| **Severity donut** | Error / Warning / Info distribution |
| **Top 10 rules** | Most frequently violated rules |
| **Operation table** | Collapsible details for each endpoint with its findings |
| **Fix results** | Applied/skipped counts (when `--fix` is used) |

Features:
- Dark/light theme (auto-detects `prefers-color-scheme`)
- Print-friendly CSS
- Zero external dependencies (all CSS/SVG inline)

## Rules

30+ rules across 7 categories, each with a severity level:

| Category | Rules | Severity | What it checks |
|----------|-------|----------|---------------|
| **Operation ID** | AI001-AI005 | ERROR/WARNING | Presence, format (camelCase), length, special chars, uniqueness |
| **Description** | AI010-AI015 | ERROR/WARNING/INFO | Presence, min length (30 chars), no path repetition, usage hints, param descriptions, enum docs |
| **Parameters** | AI020-AI023 | WARNING/ERROR | ID source hints, max required count (≤7), schema type presence, complex param examples |
| **Request Body** | AI030-AI034 | ERROR/WARNING/INFO | Mutation body presence, properties, required fields, JSON content type, description |
| **Response** | AI040-AI044 | ERROR/WARNING/INFO | 2xx presence, success schema, 4xx presence, error descriptions, specific status codes |
| **Path Design** | AI050-AI053 | WARNING/INFO | No verbs in paths, depth ≤4, consistent naming style, tags |
| **MCP Readiness** | AI060-AI064 | WARNING | Python reserved words, max params, operation count, verb patterns, security scheme |

### Scoring

```
Score = 100 - (total_penalty / operation_count)

Penalties:  ERROR = 20,  WARNING = 8,  INFO = 2

Grades:  ≥90 Excellent  |  ≥75 Good  |  ≥60 Fair  |  ≥40 Poor  |  <40 Critical
```

## CI/CD Integration

```yaml
# GitHub Actions example
- name: Lint API spec
  run: |
    pip install ai-api-lint
    ai-api-lint openapi.json --min-score 75 --severity warning
```

Exit codes:
- `0` — all clear (no errors or warnings)
- `1` — warnings found
- `2` — errors found or score below `--min-score`
- `3` — spec loading failed

## Development

```bash
git clone https://github.com/SonAIengine/ai-api-lint.git
cd ai-api-lint
poetry install --with dev

# Test
poetry run pytest tests/ -v

# Lint
poetry run ruff check .
poetry run ruff format --check .
```

## License

[MIT](LICENSE)
