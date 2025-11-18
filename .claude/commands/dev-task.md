# Development Task Command

You are working on the ComfyUI MCP server project with strict architectural patterns and workflows. Follow these rules EXACTLY:

## 🎯 MANDATORY MCP Server Usage

### 1. Epic Tasks MCP (`mcp__epic-tasks__*`) - ALWAYS USE FOR:
- Parsing epics: `mcp__epic-tasks__parse_epic_file`
- Validating epic format: `mcp__epic-tasks__validate_epic_format`
- Analyzing dependencies: `mcp__epic-tasks__analyze_dependencies`
- Getting metrics: `mcp__epic-tasks__get_epic_metrics`
- Creating GitHub issues: `mcp__epic-tasks__create_github_issues`

### 2. RAG MCP (`mcp__rag-mcp__*`) - ALWAYS USE FOR:
- Searching documentation: `mcp__rag-mcp__search(query="...", top_k=5)`
- Finding existing patterns before implementing new features
- Checking consistency with established code

**CRITICAL**: NEVER use Read tool when RAG MCP can search indexed docs. Only Read NEW files that aren't indexed yet.

## 📋 MANDATORY Workflow (DO NOT SKIP STEPS)

### Before Starting ANY Task:
1. ✅ **Search RAG**: `mcp__rag-mcp__search(query="relevant pattern", top_k=5)`
2. ✅ **Create TodoWrite list**: Track all sub-tasks
3. ✅ **Ask questions**: Use AskUserQuestion if anything is unclear

### During Implementation:
1. ✅ **Write pytest test FIRST** (TDD - Red/Green/Refactor)
2. ✅ **Implement in src/comfyui_mcp/** following epic-tasks pattern
3. ✅ **Follow Pydantic models** for all data structures
4. ✅ **Run tests**: `pytest tests/ -v --cov` (must pass 100%)
5. ✅ **Type check**: `mypy src/` (strict mode, 0 errors)
6. ✅ **Lint**: `ruff check src/ tests/` (0 errors)
7. ✅ **Format**: `ruff format src/ tests/`
8. ✅ **Update TodoWrite**: Mark tasks complete as you go

### After Implementation:
1. ✅ **Verify test coverage**: 80%+ required
2. ✅ **Update documentation**: Add docstrings, update README if needed
3. ✅ **Update RAG index**: `mcp__rag-mcp__index_document` for new docs
4. ✅ **Create feature branch**: `git checkout -b feature/issue-XX-description`
5. ✅ **Commit changes**: Include 🤖 Generated with Claude Code
6. ✅ **Push branch**: `git push -u origin feature/issue-XX-description`
7. ✅ **Create Pull Request**: Use `gh pr create` with comprehensive description

## 🏗️ Architecture Rules (NEVER VIOLATE)

### Python Package Structure (Follow epic-tasks pattern)
- ✅ ALL code in `src/comfyui_mcp/`
- ✅ Tests mirror structure in `tests/`
- ✅ Use `pyproject.toml` for all configuration
- ✅ Follow PEP 518 (src-layout pattern)

### Pydantic Models
- ✅ ALL data structures as Pydantic models in `models.py`
- ✅ Strict type hints everywhere
- ✅ Use `from __future__ import annotations` for forward refs
- ✅ Validation logic in model validators

### MCP Server Pattern
- ✅ `server.py`: MCP server implementation
- ✅ `comfyui_client.py`: ComfyUI API client wrapper
- ✅ Clear separation of concerns
- ✅ Async/await for all I/O operations

### Coding Style
- ✅ XML/docstring documentation on all public methods/classes
- ✅ Type hints on ALL functions and methods
- ✅ Use descriptive variable names
- ✅ Follow PEP 8 (enforced by ruff)
- ✅ Max line length: 88 (Black style)

## 📏 Code Reference Format

When referencing code, ALWAYS use: `file_path:line_number`

Example: "The workflow submission logic is in `src/comfyui_mcp/comfyui_client.py:45`"

## 🧪 Testing Requirements

### Before ANY commit:
```bash
# 1. Run all tests with coverage (MUST PASS)
cd C:\programming\comfyui-mcp
pytest tests/ -v --cov=comfyui_mcp --cov-report=term-missing

# 2. Type checking (0 ERRORS)
mypy src/

# 3. Linting (0 ERRORS)
ruff check src/ tests/

# 4. Format check
ruff format --check src/ tests/

# 5. Build check
pip install -e .
```

## 🚫 Common Mistakes to AVOID

1. ❌ **Reading files when RAG has them indexed**
   - Don't: `Read("docs/ARCHITECTURE.md")`
   - Do: `mcp__rag-mcp__search(query="architecture patterns")`

2. ❌ **Forgetting TodoWrite**
   - Create todo list at start, update as you go

3. ❌ **Skipping type hints**
   - ALL functions need type hints, no exceptions

4. ❌ **Not writing tests first**
   - TDD is mandatory: Write test → Fail → Implement → Pass

5. ❌ **Importing from wrong locations**
   - Always import from `comfyui_mcp.module`, never relative imports outside package

## 📊 Quality Metrics

- **Test Coverage**: 80%+ required
- **Type Check**: 0 errors (mypy strict mode)
- **Lint Errors**: 0
- **Format**: ruff format compliant

## 🎮 Project Paths

- **Project Root**: `C:\programming\comfyui-mcp`
- **Source Code**: `C:\programming\comfyui-mcp\src\comfyui_mcp`
- **Tests**: `C:\programming\comfyui-mcp\tests`
- **Epic Files**: `C:\programming\comfyui-mcp\epics`
- **Documentation**: `C:\programming\comfyui-mcp\CLAUDE.md`

## 📝 Reference Projects

- **epic-tasks**: `C:\programming\epic-tasks` (follow this structure)
- **godot-mcp**: `C:\programming\godot-mcp` (MCP server pattern reference)

## 🔄 Standard Task Flow

```
1. User provides task (or GitHub issue #XX)
   ↓
2. mcp__rag-mcp__search for similar patterns
   ↓
3. TodoWrite to plan tasks
   ↓
4. Write pytest unit tests (RED)
   ↓
5. Implement in src/comfyui_mcp/ (GREEN)
   ↓
6. pytest tests/ (MUST PASS)
   ↓
7. mypy src/ (0 ERRORS)
   ↓
8. ruff check src/ tests/ (0 ERRORS)
   ↓
9. ruff format src/ tests/
   ↓
10. Update documentation/docstrings
   ↓
11. mcp__rag-mcp__index_document for new docs
   ↓
12. Mark TodoWrite complete
   ↓
13. Create feature branch (git checkout -b feature/issue-XX-description)
   ↓
14. Commit changes with proper format
   ↓
15. Push branch (git push -u origin feature/issue-XX-description)
   ↓
16. Create Pull Request (gh pr create)
```

## 🎯 GitHub Issue Integration

When working on a GitHub issue, reference it properly:
- Branch name: `feature/issue-XX-short-description`
- Commit message: `feat(module): description (fixes #XX)`
- PR title: `[Issue #XX] Feature: Description`

---

**Now, based on this workflow and these rules, here is the actual task:**

{{prompt}}
