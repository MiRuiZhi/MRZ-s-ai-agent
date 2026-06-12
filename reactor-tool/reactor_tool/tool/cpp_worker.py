from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict

from reactor_tool.model.protocal import CppWorkerRequest


async def run_cpp_worker_request(body: CppWorkerRequest) -> Dict[str, Any]:
    worker_bin = Path(os.getenv("CPP_WORKER_BIN", "/usr/local/bin/reactor-cpp-worker"))
    if not worker_bin.is_file():
        return {
            "success": False,
            "exitCode": -1,
            "timedOut": False,
            "stdout": "",
            "stderr": f"C++ worker binary not found: {worker_bin}",
            "files": [],
        }
    process = await asyncio.create_subprocess_exec(
        str(worker_bin),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    payload = json.dumps(body.model_dump(by_alias=True), ensure_ascii=False).encode("utf-8")
    stdout, stderr = await process.communicate(payload)
    if process.returncode != 0 and not stdout:
        return {
            "success": False,
            "exitCode": process.returncode,
            "timedOut": False,
            "stdout": "",
            "stderr": stderr.decode("utf-8", errors="replace"),
            "files": [],
        }
    try:
        return json.loads(stdout.decode("utf-8"))
    except Exception:
        return {
            "success": False,
            "exitCode": process.returncode,
            "timedOut": False,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "files": [],
        }
