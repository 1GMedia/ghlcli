"""Local MCP server inventory helpers."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class McpServer:
    name: str
    path: str
    available: bool
    command: str | None


@dataclass(frozen=True)
class McpTool:
    server: str
    name: str
    file: str
    line: int
    summary: str


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "upstreams").exists() or (parent / "setup.py").exists():
            return parent
    return Path.cwd()


def open_ghl_mcp_path() -> Path:
    return _repo_root() / "upstreams" / "open-ghl-mcp"


def list_servers() -> list[McpServer]:
    path = open_ghl_mcp_path()
    return [
        McpServer(
            name="open-ghl-mcp",
            path=str(path),
            available=path.exists(),
            command=f"uv run --directory {path} python -m src.main" if path.exists() else None,
        )
    ]


def _has_mcp_tool_decorator(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for decorator in node.decorator_list:
        text = ast.unparse(decorator)
        if text == "mcp.tool()" or text.endswith(".tool()"):
            return True
    return False


def list_tools(server: str = "open-ghl-mcp") -> list[McpTool]:
    if server != "open-ghl-mcp":
        raise ValueError(f"Unknown MCP server: {server}")
    root = open_ghl_mcp_path()
    tools_dir = root / "src" / "mcp" / "tools"
    if not tools_dir.exists():
        return []

    tools: list[McpTool] = []
    for path in sorted(tools_dir.glob("*.py")):
        try:
            module = ast.parse(path.read_text())
        except SyntaxError:
            continue
        for node in ast.walk(module):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _has_mcp_tool_decorator(node):
                tools.append(
                    McpTool(
                        server=server,
                        name=node.name,
                        file=str(path.relative_to(root)),
                        line=node.lineno,
                        summary=ast.get_docstring(node) or "",
                    )
                )
    return tools
