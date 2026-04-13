from .models import DiagramSpec, DiagramLayout, NodeLayout, NodeSpec, Port, PortLayout

# ── Layout constants ──────────────────────────────────────────────────────────

CARD_WIDTH = 220
TITLE_HEIGHT = 36
PORT_ROW_HEIGHT = 28
CARD_PADDING_TOP = 12
CARD_PADDING_BTM = 12
PORT_RADIUS = 6

COLUMN_GAP = 140
COLUMN_MARGIN_X = 60
ROW_GAP = 40
ROW_MARGIN_Y = 60
CANVAS_PADDING = 40

MIN_CHARS_FOR_EXPAND = 30  # title chars before card width expands
CHAR_WIDTH_EST = 7  # monospace estimate at 12px


def _card_width(node: NodeSpec) -> float:
    """Expand card width to fit title and port labels — left and right computed independently."""
    title_needed = len(node.name) * CHAR_WIDTH_EST + 20

    dot_offset = PORT_RADIUS + 8  # 14px: dot radius + gap before label text
    padding = 16  # breathing room at card edge

    if node.node_type == "function":
        # Left side: inputs only
        max_in = max((len(p.name) + 2 + len(p.type) for p in node.inputs), default=0)
        # Right side: outputs + exception labels
        max_out = max(
            [len(p.name) + 2 + len(p.type) for p in node.outputs]
            + [len("raises ") + len(e.name) for e in node.exceptions],
            default=0,
        )

        left_needed = (dot_offset + max_in * CHAR_WIDTH_EST + padding) if max_in else 0
        right_needed = (
            (dot_offset + max_out * CHAR_WIDTH_EST + padding) if max_out else 0
        )
        port_needed = left_needed + right_needed
    else:
        # datamodel/config: inputs on left, outputs on right — compute independently
        in_chars: int = max(
            (len(p.name) + 2 + len(p.type) for p in node.inputs), default=0
        )
        out_chars: int = max(
            (len(p.name) + 2 + len(p.type) for p in node.outputs), default=0
        )
        left_needed = (
            (dot_offset + in_chars * CHAR_WIDTH_EST + padding) if in_chars else 0
        )
        right_needed = (
            (dot_offset + out_chars * CHAR_WIDTH_EST + padding) if out_chars else 0
        )
        port_needed = left_needed + right_needed

    return float(max(title_needed, port_needed, 80))


def _card_height(num_rows: int) -> float:
    return float(
        TITLE_HEIGHT + CARD_PADDING_TOP + num_rows * PORT_ROW_HEIGHT + CARD_PADDING_BTM
    )


def compute_layout(spec: DiagramSpec) -> DiagramLayout:
    # ── 1. Group nodes by column ──────────────────────────────────────────────
    columns: dict[int, list] = {}
    for node in spec.nodes:
        columns.setdefault(node.column, []).append(node)

    # ── 2. Compute x position for each column ─────────────────────────────────
    sorted_cols = sorted(columns.keys())
    col_x: dict[int, float] = {}
    x = float(COLUMN_MARGIN_X)
    for col in sorted_cols:
        col_x[col] = x
        # max card width in this column
        max_w = max(_card_width(n) for n in columns[col])
        x += max_w + COLUMN_GAP

    # ── 3. Compute layout for each node ──────────────────────────────────────
    node_layouts: list[NodeLayout] = []
    col_cursor_y: dict[int, float] = {c: float(ROW_MARGIN_Y) for c in sorted_cols}

    # preserve original node order within each column
    node_order = {n.id: i for i, n in enumerate(spec.nodes)}
    for col in sorted_cols:
        col_nodes = sorted(columns[col], key=lambda n: node_order[n.id])
        for node in col_nodes:
            nx = col_x[col]
            ny = col_cursor_y[col]
            nw = _card_width(node)
            num_rows = max(
                len(node.inputs) + len(node.outputs) + len(node.exceptions), 1
            )
            nh = _card_height(num_rows)

            # port dot coordinates — outputs after inputs, exceptions after outputs
            def _port_y(k: int) -> float:
                return (
                    ny
                    + TITLE_HEIGHT
                    + CARD_PADDING_TOP
                    + k * PORT_ROW_HEIGHT
                    + PORT_ROW_HEIGHT / 2
                )

            input_ports = [
                PortLayout(port=p, cx=nx, cy=_port_y(k), side="input")
                for k, p in enumerate(node.inputs)
            ]
            output_ports = [
                PortLayout(
                    port=p, cx=nx + nw, cy=_port_y(len(node.inputs) + k), side="output"
                )
                for k, p in enumerate(node.outputs)
            ]
            exc_offset = len(node.inputs) + len(node.outputs)
            exception_ports = [
                PortLayout(
                    port=Port(name=e.name, type="exception"),
                    cx=nx + nw,
                    cy=_port_y(exc_offset + k),
                    side="exception",
                )
                for k, e in enumerate(node.exceptions)
            ]

            node_layouts.append(
                NodeLayout(
                    spec=node,
                    x=nx,
                    y=ny,
                    width=nw,
                    height=nh,
                    input_ports=input_ports,
                    output_ports=output_ports,
                    exception_ports=exception_ports,
                )
            )
            col_cursor_y[col] = ny + nh + ROW_GAP

    # ── 4. Canvas dimensions ─────────────────────────────────────────────────
    canvas_w = max(nl.x + nl.width for nl in node_layouts) + CANVAS_PADDING
    canvas_h = max(nl.y + nl.height for nl in node_layouts) + CANVAS_PADDING

    layout = DiagramLayout(
        spec=spec, nodes=node_layouts, canvas_width=canvas_w, canvas_height=canvas_h
    )
    return layout
