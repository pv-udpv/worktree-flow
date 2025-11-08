# Worktree Flow

**Advanced Git worktree workflow management with unified FastAPI core, auto-generated Typer CLI, and MCP server integration.**

[![CI](https://github.com/pv-udpv/worktree-flow/workflows/test/badge.svg)](https://github.com/pv-udpv/worktree-flow/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

## ✨ Features

- 🏗️ **Unified Architecture** — FastAPI core → auto-generated Typer CLI + MCP server
- 🌳 **Hierarchical Worktrees** — Epic → Feature → Sub-issue structure with guardrails
- 🔌 **Provider Abstraction** — GitHub, Linear, Jira, GitLab support
- 🔗 **Universal Bindings** — Link Perplexity, AI chats, Slack threads
- 🛡️ **Smart Guardrails** — Automated validation, depth limits, sync checks
- 🤖 **AI Integration** — MCP server for Cline/Copilot/Cursor
- 📊 **Visualization** — Tree view, status tracking, hierarchy graphs
- ⚡ **Token-Optimized** — Lightweight context for AI agents (96% reduction)

## 🚀 Quick Start

### Installation

```bash
# Install with uv (recommended)
uv pip install worktree-flow

# Or with pip
pip install worktree-flow
```

### Initialize Repository

```bash
# Convert existing repo to bare + worktree structure
worktree init /path/to/your/repo

# Or start fresh
git clone --bare <repo-url> my-project/.bare
cd my-project
echo "gitdir: ./.bare" > .git
worktree init .
```

### Create Worktree from Issue

```bash
# GitHub (default)
worktree create issue 7

# Linear
worktree create issue DEV-123 --provider linear

# With research context
worktree bind perplexity issue-7 thread-abc123
```

## 📐 Architecture

### Unified API-First Design

```
Pydantic Models (Single Source of Truth)
    ↓
FastAPI Core (Business Logic + REST API)
    ↓
    ├─→ Typer CLI (auto-generated)
    ├─→ MCP Server (auto-exposed)
    └─→ Web UI (optional)
```

### Provider Pattern

- **Issue Providers**: GitHub, Linear, Jira, GitLab
- **PR Providers**: GitHub PRs, GitLab MRs
- **Git Providers**: GitHub, GitLab, Local
- **Chat Providers**: Copilot, Cline, Cursor
- **Research Providers**: Perplexity, Slack, Notion

## 📚 Documentation

- [Quick Start Guide](docs/quickstart.md)
- [Architecture Overview](docs/architecture.md)
- [Workflow Examples](docs/workflows.md)
- [Provider Guide](docs/providers.md)
- [API Reference](docs/api.md)
- [MCP Integration](docs/mcp.md)

## 💡 Usage Examples

### Simple Workflow

```bash
# Create from issue
worktree create issue 8
cd issue-8

# Work, commit
git add .
git commit -m "fix: resolve timeout"

# Create PR
worktree pr create

# After merge, cleanup
worktree remove issue-8
```

### Epic Workflow (Hierarchical)

```bash
# Create epic
worktree create epic 7

# Create features under epic
worktree create feature 7.1 epic-7
worktree create feature 7.2 epic-7
worktree create feature 7.3 epic-7

# Work in parallel
cd feat-7-1 && # work here
cd ../feat-7-2 && # work here

# Merge features → epic
cd feat-7-1 && worktree merge up
cd ../feat-7-2 && worktree merge up

# Finally: epic → main
cd ../epic-7 && worktree pr create
```

### FastAPI Server

```bash
# Start API server
worktree-api --port 8000 --reload

# Access:
# - API: http://localhost:8000
# - Docs: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
```

### MCP Server (AI Agents)

```json
// Cline MCP settings
{
  "worktree": {
    "command": "worktree-mcp",
    "env": {
      "GITHUB_TOKEN": "ghp_...",
      "WORKTREE_DEFAULT_REPO": "/path/to/repo"
    }
  }
}
```

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md)

## 📄 License

MIT © 2025 Pavel Vavilov

## 🙏 Acknowledgments

- Inspired by modern Git workflows and AI-assisted development
- Built with FastAPI, Typer, and MCP
- Provider pattern inspired by Terraform and Pulumi
