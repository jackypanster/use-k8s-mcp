# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Build and Run
- **Run main application**: `uv run python src/main.py`
- **Run scanner**: `uv run python src/k8s_scanner.py discover` (tool discovery)
- **Run full scan**: `uv run python src/k8s_scanner.py full-scan --cluster <cluster-name>`

### Environment Setup
- **Install dependencies**: `uv sync`
- **Check environment**: `uv run python script/check-scan-env.py`

### Cache Management
- **Query cache**: `uv run python script/query-cache-db.py`
- **Verify scan status**: `uv run python script/verify-scan-status.py`

## Architecture

### Core Components
- **Main Application**: `src/main.py` (LLM Agent for K8s management)
- **Scanner**: `src/k8s_scanner.py` (MCP tool discovery and cluster scanning)
- **Cache**: SQLite database at `data/k8s_cache.db`

### Workflows
1. **Tool Discovery**: Loads MCP tools and caches them.
2. **Cluster Scanning**: Uses MCP tools to scan and cache cluster resources.
3. **User Interaction**: Processes natural language requests via LLM Agent.

### Key Files
- **LLM Config**: `src/llm_config.py`
- **Cache Manager**: `src/cache/cache_manager.py`
- **Scanner Core**: `src/scanner/cluster_scanner.py`