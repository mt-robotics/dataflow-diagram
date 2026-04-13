import argparse
import json
import sys
from pathlib import Path

from dataflow_diagram.models import DiagramSpec, NodeSpec, Port, ExceptionPort, EdgeSpec
from dataflow_diagram.layout import compute_layout
from dataflow_diagram.renderer import render_svg


def parse_spec(data: dict) -> DiagramSpec:
    nodes = [
        NodeSpec(
            id=n["id"],
            name=n["name"],
            column=n["column"],
            node_type=n.get("node_type", "function"),
            async_fn=n.get("async", False),
            inputs=[
                Port(p["name"], p["type"], p.get("default"), p.get("internal", False))
                for p in n.get("inputs", [])
            ],
            outputs=[
                Port(p["name"], p["type"], p.get("default"), p.get("internal", False))
                for p in n.get("outputs", [])
            ],
            exceptions=[ExceptionPort(e["name"]) for e in n.get("exceptions", [])],
        )
        for n in data["nodes"]
    ]
    edges = [
        EdgeSpec(e["from_node"], e["from_port"], e["to_node"], e["to_port"])
        for e in data.get("edges", [])
    ]
    return DiagramSpec(
        title=data.get("title", "Dataflow Diagram"), nodes=nodes, edges=edges
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m dataflow_diagram",
        description="Generate an SVG dataflow diagram from a JSON spec file.",
    )
    parser.add_argument("input", type=Path, help="Path to the JSON spec file")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output SVG path (default: same name as input with .svg extension)",
    )
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: {args.input} not found", file=sys.stderr)
        sys.exit(1)

    data = json.loads(args.input.read_text())
    spec = parse_spec(data)
    layout = compute_layout(spec)
    svg = render_svg(layout)

    output_path = args.output or args.input.with_suffix(".svg")
    output_path.write_text(svg)
    print(f"Written: {output_path}  ({len(svg):,} bytes)")


if __name__ == "__main__":
    main()
