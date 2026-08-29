# dwg-engine

Generate real **DWG** files with **no paid CAD** — a Claude Code plugin.

The DWG format is closed, so nothing open writes it cleanly on its own. This
packages the pieces that do into one Docker image and exposes them as MCP tools:

- **[ezdxf](https://ezdxf.mozman.at/)** builds the drawing as DXF (open, well supported).
- **ODA File Converter** (free, from the Open Design Alliance) converts DXF → DWG,
  driven headless under `xvfb`.

The host installs **nothing but Docker**. Every native library lives in the image.

## Why not just use a CAD?

nanoCAD / AutoCAD / BricsCAD write DWG but are paid. LibreDWG (open) *reads*
modern DWG well but its *writer* is R2000-only and rejects common DXF, so it is
not viable for delivery. The free path that actually works end to end is
ezdxf → ODA File Converter, which is what this image bakes in.

## Install (as a plugin)

```
/plugin marketplace add Rixmerz/claude-plugins
/plugin install dwg-engine@rixmerz
```

First tool call builds the Docker image (~2–4 min, one time).

## Tools

| Tool | Does |
|---|---|
| `dxf_to_dwg(dxf_path, dwg_path, version=ACAD2018)` | Convert a DXF to DWG. Absolute paths. |
| `demo(dwg_path)` | Build a sample drawing and convert it, to prove the engine works. |

Paths are absolute on your machine; the plugin mounts `$HOME` into the container 1:1.

## Use the CLI directly

```
docker build -t dwg-engine:0.1 .
docker run --rm -v "$PWD:/work" dwg-engine:0.1 to-dwg /work/plan.dxf /work/plan.dwg
```

## Roadmap

- Read path (LibreDWG `dwg2dxf`) built into the image, for a DWG viewer/canvas.
- RIDAA skills + a specialized subagent that draft Chilean sanitary plans → DWG.
- A canvas editor that opens a DWG and edits text and basic entities.

## License

MIT (this repo). The ODA File Converter is downloaded at build time under ODA's
own free license terms; it is not redistributed here.
