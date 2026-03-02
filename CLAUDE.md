# ai-api-lint 개발 가이드

## 프로젝트 개요
AI/LLM 에이전트 친화적 API linter. OpenAPI spec을 분석하여 AI-readiness 점수 제공.

## 개발 환경

### 필수 도구
```bash
poetry install --with dev
```

### Lint & Format
```bash
poetry run ruff check .
poetry run ruff format --check .
poetry run ruff format .
```

### 테스트
```bash
poetry run pytest tests/ -v
poetry run pytest tests/ -q
```

## 코드 규칙

### ruff 설정
```toml
[tool.ruff]
target-version = "py310"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.ruff.lint.per-file-ignores]
"ai_api_lint/rules/*.py" = ["N801"]     # AI001_RuleName convention
"ai_api_lint/report.py" = ["E501"]      # HTML template strings
"ai_api_lint/fixer/fixers.py" = ["N801"] # FixAI042 naming convention
```

### Rule 작성 패턴
```python
class AI0XX_RuleName(Rule):
    rule_id = "AI0XX"
    category = RuleCategory.DESCRIPTION
    severity = Severity.WARNING
    short_description = "..."

    def check(self, ctx: OperationContext) -> list[Finding]:
        ...
        return [self._finding(ctx, "message", suggestion="...")]
```

### Fixer 작성 패턴
```python
class FixAI0XX(Fixer):
    rule_id = "AI0XX"
    level = 1  # 1=safe, 2=inferred

    def fix(self, spec: dict, finding: Finding) -> bool:
        op = _get_operation(spec, finding.path, finding.method)
        if op is None:
            return False
        # ... in-place mutation ...
        return True

    def description(self) -> str:
        return "What this fixer does"
```

## 커밋 규칙
- 한글 커밋 메시지
- `git -c user.name="SonAIengine" -c user.email="sonsj97@gmail.com" commit`
- 커밋 전: `poetry run ruff check .` + `poetry run ruff format --check .` + `poetry run pytest tests/ -q`

## 주요 파일 구조
```
ai_api_lint/
  cli.py              # CLI 진입점 (--fix, --format html, --output 등)
  engine.py            # RuleEngine — rule 등록, lint 실행
  models.py            # Finding, LintReport, FixResult, FixRecord
  scorer.py            # 점수 계산 (penalty 기반)
  formatter.py         # terminal/json 출력 포맷
  loader.py            # spec 로딩 + $ref 해석
  report.py            # HTML 리포트 생성 (single-file, CSS/JS 인라인)
  rules/
    base.py            # Rule ABC, RuleCategory enum
    __init__.py        # create_default_engine() — 30+ 규칙 등록
    description.py     # AI010~AI015
    parameters.py      # AI020~AI023
    request_body.py    # AI030~AI034
    response.py        # AI040~AI044
    path_design.py     # AI050~AI053
    operation_id.py    # AI001~AI005
    mcp_readiness.py   # AI060~AI064
  fixer/
    base.py            # Fixer ABC (rule_id, level, fix(), description())
    engine.py          # FixEngine (level 필터, dry-run 지원)
    fixers.py          # 14개 fixer 구현 (FixAI001~FixAI053)
    __init__.py        # create_default_fixers()
```

## CLI 사용법
```bash
# 기본 lint
ai-api-lint spec.json

# Auto-fix
ai-api-lint spec.json --fix --output fixed.json
ai-api-lint spec.json --fix --level 1          # L1만
ai-api-lint spec.json --fix --dry-run          # 미리보기

# HTML 리포트
ai-api-lint spec.json --format html --output report.html
ai-api-lint spec.json --fix --format html --output report.html
```
