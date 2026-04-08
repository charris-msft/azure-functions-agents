import importlib.util
import inspect
import json
import logging
import os
import sys
import tempfile
from typing import Callable, List, Optional

from copilot import define_tool
from pydantic import BaseModel, Field

from .config import get_app_root


def discover_tools() -> List[Callable]:
    """
    Dynamically discover and load tools from the `tools` folder.
    """
    tools: List[Callable] = []
    project_src_dir = str(get_app_root())
    tools_dir = os.path.join(project_src_dir, "tools")

    # Add tools dir to sys.path so tool modules can import shared helpers
    # (e.g. _patterns.py, _utils.py — files prefixed with _ that are skipped
    # during tool registration but may be imported by tool modules)
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)

    print(f"[Tool Discovery] Looking for tools in: {tools_dir}")
    print(f"[Tool Discovery] Directory exists: {os.path.exists(tools_dir)}")

    if not os.path.exists(tools_dir):
        print(f"[Tool Discovery] WARNING: Tools directory not found: {tools_dir}")
        return tools

    files = [f for f in os.listdir(tools_dir) if f.endswith(".py") and not f.startswith("_")]
    print(f"[Tool Discovery] Python files found: {files}")

    for filename in files:
        filepath = os.path.join(tools_dir, filename)
        module_name = filename[:-3]
        print(f"[Tool Discovery] Loading module: {module_name} from {filepath}")
        try:
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            if spec is None or spec.loader is None:
                print(f"[Tool Discovery] ERROR: Could not create spec for {filename}")
                continue

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            members = inspect.getmembers(module, inspect.isfunction)
            local_functions = [
                (name, obj)
                for name, obj in members
                if obj.__module__ == module_name and not name.startswith("_")
            ]
            print(f"[Tool Discovery] Local functions in {filename}: {[m[0] for m in local_functions]}")

            for name, obj in local_functions:
                description = (obj.__doc__ or f"Tool: {name}").strip()
                tools.append(define_tool(description=description)(obj))
                print(f"[Tool Discovery] Loaded: {name}")
                print(f"[Tool Discovery]   Description: {description}")
                break
        except Exception as e:
            import traceback

            print(f"[Tool Discovery] ERROR loading {filename}: {e}")
            traceback.print_exc()
            logging.error(f"Failed to load tool from {filename}: {e}")

    return tools


# ---------------------------------------------------------------------------
# Built-in tools (always available, shipped with the library)
# ---------------------------------------------------------------------------

# Directories the agent is allowed to read from.
_ALLOWED_READ_DIRS = [
    os.path.normpath(tempfile.gettempdir()),
]


class ReadFileParams(BaseModel):
    path: str = Field(description="Absolute path to the file to read")
    start_line: Optional[int] = Field(default=None, description="1-based start line number. If omitted, reads from the beginning.")
    end_line: Optional[int] = Field(default=None, description="1-based end line number (inclusive). If omitted, reads to the end.")


# This tool is needed because for security reasons, we disabled Copilot's built-in file reading capability that allows reading any file on disk.
# Often Copilot writes long tool output to files and the agent needs a way to read it back.
@define_tool(description=(
    "Read a file from the host system by absolute path. Optionally specify"
    " start_line and end_line (1-based, inclusive) to read a portion of the file.\n"
    "\n"
    "IMPORTANT: This reads files on the local system, such as tool call results"
    " that are too long."
))
async def read_file(params: ReadFileParams) -> str:
    requested = os.path.normpath(params.path)

    allowed = any(
        requested.startswith(d + os.sep) or requested == d
        for d in _ALLOWED_READ_DIRS
    )
    if not allowed:
        return json.dumps({"error": "Access denied: path is not in an allowed directory"})

    if not os.path.isfile(requested):
        return json.dumps({"error": f"File not found: {params.path}"})

    with open(requested, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    total = len(lines)
    start = (params.start_line or 1) - 1
    end = params.end_line or total

    start = max(0, min(start, total))
    end = max(start, min(end, total))

    selected = lines[start:end]
    content = "".join(selected)

    return json.dumps({
        "total_lines": total,
        "start_line": start + 1,
        "end_line": end,
        "content": content,
    })


_BUILTIN_TOOLS = [read_file]

_REGISTERED_TOOLS_CACHE = discover_tools() + _BUILTIN_TOOLS
