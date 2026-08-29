#!/usr/bin/env python3
"""Minimal stdio MCP server for the DWG engine (stdlib only, no SDK).

Newline-delimited JSON-RPC 2.0 over stdin/stdout, MCP 2024-11-05. Exposes the
DWG write path (DXF -> DWG via the bundled ODA File Converter) as tools. Paths
are absolute on the host filesystem, which the plugin mounts 1:1 into the
container, so a tool gets a host path and it is valid inside here.
"""
import json
import os
import subprocess
import sys
import tempfile

TOOLS = [
    {
        "name": "dxf_to_dwg",
        "description": (
            "Convert a DXF file to DWG using the bundled ODA File Converter. "
            "Give absolute paths. version defaults to ACAD2018."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "dxf_path": {"type": "string", "description": "Absolute path to the input .dxf"},
                "dwg_path": {"type": "string", "description": "Absolute path for the output .dwg"},
                "version": {
                    "type": "string",
                    "description": "ACAD2018 | ACAD2013 | ACAD2010 | ACAD2007 | ACAD2000",
                    "default": "ACAD2018",
                },
            },
            "required": ["dxf_path", "dwg_path"],
        },
    },
    {
        "name": "demo",
        "description": (
            "Generate a tiny sample drawing with ezdxf and convert it to DWG, to "
            "prove the engine works end to end. Writes to dwg_path (absolute)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "dwg_path": {"type": "string", "description": "Absolute path for the sample .dwg"},
            },
            "required": ["dwg_path"],
        },
    },
]


def _convert(dxf: str, dwg: str, version: str = "ACAD2018") -> str:
    subprocess.run(
        ["python3", "/engine/dwgconv", "to-dwg", dxf, dwg, version],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    return dwg


def _demo(dwg: str) -> str:
    import ezdxf

    doc = ezdxf.new("R2018")
    msp = doc.modelspace()
    msp.add_line((0, 0), (100, 50))
    msp.add_circle((50, 25), 20)
    msp.add_text("dwg-engine OK", height=5).set_placement((0, -15))
    with tempfile.TemporaryDirectory() as d:
        dxf = os.path.join(d, "sample.dxf")
        doc.saveas(dxf)
        return _convert(dxf, dwg)


def _call(name: str, args: dict) -> str:
    if name == "dxf_to_dwg":
        return "Wrote DWG: " + _convert(args["dxf_path"], args["dwg_path"], args.get("version", "ACAD2018"))
    if name == "demo":
        return "Sample DWG written: " + _demo(args["dwg_path"])
    raise ValueError(f"unknown tool: {name}")


def _send(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        mid, method = msg.get("id"), msg.get("method")
        if method == "initialize":
            _send({"jsonrpc": "2.0", "id": mid, "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "dwg-engine", "version": "0.1.0"},
            }})
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            _send({"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}})
        elif method == "tools/call":
            p = msg.get("params", {})
            try:
                text = _call(p.get("name"), p.get("arguments", {}))
                _send({"jsonrpc": "2.0", "id": mid, "result": {"content": [{"type": "text", "text": text}]}})
            except subprocess.CalledProcessError as e:
                out = (e.stdout or b"").decode(errors="replace")[-800:]
                _send({"jsonrpc": "2.0", "id": mid, "result": {
                    "content": [{"type": "text", "text": f"conversion failed:\n{out}"}], "isError": True}})
            except Exception as e:  # noqa: BLE001 - surface any tool error to the client
                _send({"jsonrpc": "2.0", "id": mid, "result": {
                    "content": [{"type": "text", "text": f"error: {e}"}], "isError": True}})
        elif mid is not None:
            _send({"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not found: {method}"}})


if __name__ == "__main__":
    main()
