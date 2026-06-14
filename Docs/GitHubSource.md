# Kapruka MCP — GitHub Source

Official open-source MCP server that wraps the Kapruka.com REST API for LLMs and MCP clients.

**Repository:** [github.com/kapruka/mcp](https://github.com/kapruka/mcp)  
**Clone:** `https://github.com/kapruka/mcp.git`

## About

Python MCP server exposing Kapruka tools: product search, categories, delivery quoting, guest checkout, and order tracking.

**Public endpoint (no setup):** `https://mcp.kapruka.com/mcp`  
**Docs:** [mcp.kapruka.com](https://mcp.kapruka.com)

## Local setup

```bash
# 1. Clone
git clone https://github.com/kapruka/mcp.git
cd mcp

# 2. Virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install
pip install -e ".[dev]"

# 4. Configure
cp .env.example .env
# Edit .env with Kapruka API URL and key (for self-hosted only)
```

## Running

```bash
# Streamable HTTP (default port 8000)
python cli.py server

# stdio transport (MCP Inspector)
python cli.py server --stdio

# Health-check Kapruka REST API
python cli.py ping

# List registered MCP tools
python cli.py tools
```

## MCP Inspector

```bash
npx @modelcontextprotocol/inspector python cli.py server --stdio
```

## Project structure

```
src/
  server.py        # FastMCP server entry point
  tools/           # One module per tool group (products, orders, …)
  api/
    client.py      # Async httpx client + error handling
  config/
    settings.py    # Env-based configuration
tests/             # pytest test suite
cli.py             # Developer CLI
```

## Tests

```bash
pytest
```
