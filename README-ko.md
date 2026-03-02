<div align="center">

# ai-api-lint

**OpenAPI 스펙을 위한 AI 친화적 API linter**

API 스펙의 LLM/에이전트 가독성을 분석하고,
AI-readiness 점수를 매기고, 자동 수정하고, HTML 리포트로 공유하세요.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

[English](README.md) · 한국어

</div>

---

## 왜 필요한가요?

LLM 에이전트가 API를 tool-use로 호출하는 일이 점점 많아지고 있습니다. 하지만 대부분의 OpenAPI 스펙은 사람을 위해 작성된 것이지, AI를 위한 것이 아닙니다:

- **description 누락** — 에이전트가 *언제* 이 엔드포인트를 호출해야 하는지 모릅니다
- **에러 응답 없음** — 에이전트가 실패를 처리할 수 없습니다
- **모호한 파라미터** — 에이전트가 잘못된 값을 보냅니다
- **스키마 타입 없음** — 에이전트가 잘못된 형식으로 요청합니다

**ai-api-lint**는 스펙을 0~100점으로 채점하고, 7개 카테고리 30개 이상의 규칙으로 정확히 뭘 고쳐야 하는지 알려줍니다. 가장 흔한 문제는 **자동 수정**까지 가능합니다.

### 실제 사례

프로덕션 커머스 API (1,083개 operation)에 ai-api-lint를 실행한 결과:

```
Score: 71.2 / Fair
4,195 findings (1,058 errors, 2,570 warnings, 567 info)

주요 문제:
  AI042  4xx 에러 응답 없음            1,058 ops
  AI013  description에 사용법 힌트 없음  1,045 ops
  AI034  requestBody에 description 없음   449 ops
```

`--fix` 적용 후: **71.2 → 85+ (Good)**, 3,500건 이상 자동 해결.

## 설치

```bash
pip install ai-api-lint

# 선택: YAML 지원
pip install ai-api-lint[yaml]
```

## 빠른 시작

```bash
# 스펙 분석
ai-api-lint openapi.json

# 출력 예시:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
#  POST /users  •  createUser
#   ✗ AI042  4xx 클라이언트 에러 응답이 정의되지 않았습니다.
#   ⚠ AI034  Request body에 'description'이 없습니다.
#   ⚠ AI014  파라미터 'name'에 description이 없습니다.
#
#  Overall Score: 71.2 / Fair
#  42 operations, 156 findings (12 errors, 98 warnings, 46 info)
```

## 사용법

### Lint (검사)

```bash
# 기본 검사
ai-api-lint openapi.json

# JSON 출력 (CI/CD 파이프라인용)
ai-api-lint openapi.json --format json

# 점수 기준 미달 시 CI 실패
ai-api-lint openapi.json --min-score 70

# 심각도 필터
ai-api-lint openapi.json --severity warning   # 에러 + 경고만
ai-api-lint openapi.json --severity error     # 에러만

# 전체 규칙 목록 확인
ai-api-lint --list-rules
```

### 자동 수정 (Auto-Fix)

`--fix` 플래그로 스펙의 일반적인 문제를 자동 수정합니다:

```bash
# 수정 후 결과 표시
ai-api-lint openapi.json --fix

# 수정된 스펙을 새 파일로 저장
ai-api-lint openapi.json --fix --output fixed.json

# 안전한 수정만 적용 (Level 1 — 추측 없음)
ai-api-lint openapi.json --fix --level 1

# 실제 수정 없이 미리보기
ai-api-lint openapi.json --fix --dry-run
```

#### 수정 레벨

| 레벨 | 이름 | 동작 | 예시 |
|------|------|------|------|
| **1** | 안전 (Safe) | 누락된 보일러플레이트 데이터만 추가 | `"400": {"description": "Bad Request"}` |
| **2** | 추론 (Inferred) | method/path/tags 기반으로 내용 생성 | `"summary": "GET /users (accounts)"` |

Level 1은 항상 안전합니다 — 기존 데이터를 변경하지 않고, 빈칸만 채웁니다.
Level 2는 패턴 기반으로 추측합니다. commit 전에 결과를 검토하세요.

#### 14개 내장 Fixer

영향도 순서(일반적으로 해결되는 건수)로 정렬:

| Fixer | 규칙 | 레벨 | 동작 | 예상 영향 |
|-------|------|------|------|----------|
| FixAI042 | AI042 | L1 | 4xx 응답 없으면 `400: Bad Request` 추가 | ~1,000 ops |
| FixAI034 | AI034 | L2 | operationId/summary에서 requestBody description 생성 | ~450 ops |
| FixAI031 | AI031 | L1 | schema에 빈 `properties: {}` 추가 | ~430 ops |
| FixAI014 | AI014 | L2 | name + type에서 파라미터 description 생성 | ~370 ops |
| FixAI022 | AI022 | L1 | 타입 없는 파라미터에 `schema: {type: string}` 추가 | ~320 ops |
| FixAI010 | AI010 | L2 | `METHOD /path (tags)` 패턴으로 summary 생성 | ~200 ops |
| FixAI041 | AI041 | L1 | 성공 응답에 `{type: object}` schema 추가 | ~190 ops |
| FixAI032 | AI032 | L1 | schema에 빈 `required: []` 배열 추가 | ~120 ops |
| FixAI043 | AI043 | L1 | 에러 응답에 상태 코드 기반 description 추가 | ~95 ops |
| FixAI053 | AI053 | L1 | 첫 번째 의미 있는 path segment를 tag으로 추가 | ~87 ops |
| FixAI011 | AI011 | L2 | 짧은 description에 path/method 정보 보강 | ~63 ops |
| FixAI001 | AI001 | L2 | `{method}_{path_slug}` 형식으로 operationId 생성 | 케이스별 |
| FixAI033 | AI033 | L1 | requestBody에 `application/json` content type 추가 | ~10 ops |
| FixAI040 | AI040 | L1 | 2xx 없으면 `200: OK` 또는 `201: Created` 추가 | ~5 ops |

### HTML 리포트

외부 의존성 없는 단일 파일 HTML 리포트를 생성합니다 — 팀에 쉽게 공유할 수 있습니다:

```bash
# 리포트 생성
ai-api-lint openapi.json --format html --output report.html

# 수정 결과 포함 리포트 생성
ai-api-lint openapi.json --fix --format html --output report.html

# 브라우저에서 열기
open report.html
```

#### 리포트 구성

| 섹션 | 설명 |
|------|------|
| **점수 게이지** | 0~100 점수 + 등급 (SVG arc) |
| **카테고리 바** | 카테고리별 finding 건수 (Description, Response 등) |
| **심각도 도넛** | Error / Warning / Info 분포 |
| **Top 10 규칙** | 가장 많이 위반된 규칙 |
| **Operation 테이블** | 엔드포인트별 finding 접이식 상세 |
| **수정 결과** | 적용/건너뜀 건수 (`--fix` 사용 시) |

특징:
- 다크/라이트 테마 (시스템 `prefers-color-scheme` 자동 감지)
- 인쇄 친화적 CSS
- 외부 의존성 제로 (모든 CSS/SVG 인라인)

## 규칙

7개 카테고리, 30개 이상의 규칙 — 각각 심각도 레벨 포함:

| 카테고리 | 규칙 | 심각도 | 검사 내용 |
|----------|------|--------|----------|
| **Operation ID** | AI001-AI005 | ERROR/WARNING | 존재 여부, 형식 (camelCase), 길이, 특수문자, 중복 |
| **Description** | AI010-AI015 | ERROR/WARNING/INFO | 존재 여부, 최소 길이 (30자), path 반복 금지, 사용 힌트, 파라미터 설명, enum 문서화 |
| **Parameters** | AI020-AI023 | WARNING/ERROR | ID 출처 힌트, 필수 파라미터 수 (≤7), 스키마 타입, 복합 파라미터 예시 |
| **Request Body** | AI030-AI034 | ERROR/WARNING/INFO | 뮤테이션 body 존재, properties, required, JSON content type, description |
| **Response** | AI040-AI044 | ERROR/WARNING/INFO | 2xx 존재, 성공 스키마, 4xx 존재, 에러 description, 구체적 상태 코드 |
| **Path Design** | AI050-AI053 | WARNING/INFO | path에 동사 금지, 깊이 ≤4, 일관된 네이밍, tags |
| **MCP Readiness** | AI060-AI064 | WARNING | Python 예약어, 최대 파라미터 수, operation 수, 동사 패턴, security scheme |

### 점수 계산

```
Score = 100 - (total_penalty / operation_count)

감점:  ERROR = 20,  WARNING = 8,  INFO = 2

등급:  ≥90 Excellent  |  ≥75 Good  |  ≥60 Fair  |  ≥40 Poor  |  <40 Critical
```

## CI/CD 연동

```yaml
# GitHub Actions 예시
- name: API 스펙 검사
  run: |
    pip install ai-api-lint
    ai-api-lint openapi.json --min-score 75 --severity warning
```

종료 코드:
- `0` — 문제 없음 (에러/경고 없음)
- `1` — 경고 있음
- `2` — 에러 있음 또는 `--min-score` 미달
- `3` — 스펙 로딩 실패

## 개발

```bash
git clone https://github.com/SonAIengine/ai-api-lint.git
cd ai-api-lint
poetry install --with dev

# 테스트
poetry run pytest tests/ -v

# Lint
poetry run ruff check .
poetry run ruff format --check .
```

## 라이선스

[MIT](LICENSE)
