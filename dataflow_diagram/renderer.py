import sys
from .models import DiagramLayout, NodeLayout, PortLayout
from .layout import PORT_RADIUS, TITLE_HEIGHT

# ── Colours (presentation attributes only — no <style> block) ────────────────
C_CANVAS = "#0f172a"  # slate-900
C_CARD = "#1e293b"  # slate-800
C_CARD_BORDER = "#334155"  # slate-700
C_TITLE_FN = "#3b82f6"  # blue-500      — function nodes
C_TITLE_DM = "#7c3aed"  # violet-700    — datamodel nodes
C_TITLE_CFG = "#0d9488"  # teal-600      — config nodes
C_TITLE_LIB = "#ea580c"  # orange-600    — library/external nodes (not written by you)
C_INPUT_DOT = "#3b82f6"  # blue-500
C_INTERNAL_DOT = "#C19552"  # amber-gold    — internal/dependency ports
C_OUTPUT_DOT = "#10b981"  # emerald-500
C_EXCEPTION_DOT = "#dc2626"  # red-600       — exception ports
C_PORT_NAME = "#94a3b8"  # slate-400
C_PORT_TYPE = "#cbd5e1"  # slate-300
C_DEFAULT = "#475569"  # slate-600
C_DIVIDER = "#334155"
C_EDGE = "#64748b"  # slate-500
C_TITLE_TEXT = "#ffffff"
C_DIAGRAM_TTL = "#e2e8f0"  # slate-200


def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _trunc(text: str, max_chars: int = 20) -> str:
    return text if len(text) <= max_chars else text[: max_chars - 1] + "…"


def _r(n: float) -> str:
    return f"{n:.1f}"


# ── <defs> ────────────────────────────────────────────────────────────────────


def _defs() -> list[str]:
    return [
        "  <defs>",
        "    <filter id='shadow' x='-10%' y='-10%' width='120%' height='130%'>",
        "      <feDropShadow dx='0' dy='4' stdDeviation='6' flood-color='#000000' flood-opacity='0.4'/>",
        "    </filter>",
        "    <marker id='arrow' viewBox='0 0 10 6' refX='9' refY='3'",
        "            markerWidth='8' markerHeight='6' orient='auto'>",
        f"      <path d='M 0 0 L 10 3 L 0 6 Z' fill='{C_EDGE}'/>",
        "    </marker>",
        "  </defs>",
    ]


# ── Edge ──────────────────────────────────────────────────────────────────────


def _edge(x1: float, y1: float, x2: float, y2: float) -> str:
    dx = x2 - x1
    offset = max(abs(dx) * 0.5, 80.0)
    cp1x, cp1y = x1 + offset, y1
    cp2x, cp2y = x2 - offset, y2
    d = f"M {_r(x1)} {_r(y1)} C {_r(cp1x)} {_r(cp1y)}, {_r(cp2x)} {_r(cp2y)}, {_r(x2)} {_r(y2)}"
    return (
        f"  <path d='{d}' fill='none'"
        f" stroke='{C_EDGE}' stroke-width='2'"
        f" marker-end='url(#arrow)'/>"
    )


# ── Node card ─────────────────────────────────────────────────────────────────


def _title_color(node_type: str) -> str:
    return {
        "datamodel": C_TITLE_DM,
        "config": C_TITLE_CFG,
        "library": C_TITLE_LIB,
    }.get(node_type, C_TITLE_FN)


def _node_card(nl: NodeLayout) -> list[str]:
    lines = []
    x, y, w, h = nl.x, nl.y, nl.width, nl.height
    title_color = _title_color(nl.spec.node_type)

    lines.append("  <g>")

    # card body
    lines.append(
        f"    <rect x='{_r(x)}' y='{_r(y)}' width='{_r(w)}' height='{_r(h)}'"
        f" rx='8' ry='8' fill='{C_CARD}' stroke='{C_CARD_BORDER}' stroke-width='1.5'"
        f" filter='url(#shadow)'/>"
    )

    # title bar (rounded top, flat bottom via overlay rect)
    lines.append(
        f"    <rect x='{_r(x)}' y='{_r(y)}' width='{_r(w)}' height='{_r(TITLE_HEIGHT)}'"
        f" rx='8' ry='8' fill='{title_color}'/>"
    )
    lines.append(
        f"    <rect x='{_r(x)}' y='{_r(y + 20)}' width='{_r(w)}' height='16' fill='{title_color}'/>"
    )

    # title text (with async badge if applicable)
    title_x = x + w / 2
    title_y = y + TITLE_HEIGHT / 2
    name_text = _esc(nl.spec.name)
    if nl.spec.async_fn:
        name_text = f"async  {name_text}"
    lines.append(
        f"    <text x='{_r(title_x)}' y='{_r(title_y)}'"
        f" text-anchor='middle' dominant-baseline='middle'"
        f" fill='{C_TITLE_TEXT}' font-weight='600' font-size='12'>"
        f"{name_text}</text>"
    )

    # horizontal divider under title
    lines.append(
        f"    <line x1='{_r(x)}' y1='{_r(y + TITLE_HEIGHT)}'"
        f" x2='{_r(x + w)}' y2='{_r(y + TITLE_HEIGHT)}'"
        f" stroke='{C_DIVIDER}' stroke-width='1'/>"
    )

    # vertical centre divider (dashed) — for function and library nodes
    if nl.spec.node_type in ("function", "library"):
        mid_x = x + w / 2
        lines.append(
            f"    <line x1='{_r(mid_x)}' y1='{_r(y + TITLE_HEIGHT)}'"
            f" x2='{_r(mid_x)}' y2='{_r(y + h)}'"
            f" stroke='{C_DIVIDER}' stroke-width='0.5' stroke-dasharray='3,3'/>"
        )

    # input port rows
    for pl in nl.input_ports:
        _port_row(lines, pl, side="input", card_x=x, card_w=w)

    # output port rows
    for pl in nl.output_ports:
        _port_row(lines, pl, side="output", card_x=x, card_w=w)

    # exception port rows
    for pl in nl.exception_ports:
        _port_row(lines, pl, side="exception", card_x=x, card_w=w)

    lines.append("  </g>")
    return lines


def _port_row(
    lines: list[str], pl: PortLayout, side: str, card_x: float, card_w: float
) -> None:
    cx, cy = pl.cx, pl.cy
    if side == "exception":
        dot_color = C_EXCEPTION_DOT
    elif side == "output":
        dot_color = C_OUTPUT_DOT
    elif pl.port.internal:
        dot_color = C_INTERNAL_DOT
    else:
        dot_color = C_INPUT_DOT
    has_default = pl.port.default is not None

    # port dot
    lines.append(
        f"    <circle cx='{_r(cx)}' cy='{_r(cy)}' r='{PORT_RADIUS}'"
        f" fill='{dot_color}' stroke='{C_CARD}' stroke-width='2'/>"
    )

    # label position and alignment
    if side == "input":
        lx = cx + PORT_RADIUS + 8
        anchor = "start"
    else:  # output or exception — both on the right edge
        lx = cx - PORT_RADIUS - 8
        anchor = "end"

    # port name + type on one line
    name_text = _esc(pl.port.name)
    label_y = cy - (5 if has_default else 0)

    if side == "exception":
        # show only the exception class name — no type suffix needed
        lines.append(
            f"    <text x='{_r(lx)}' y='{_r(label_y)}'"
            f" text-anchor='{anchor}' dominant-baseline='middle'"
            f" fill='{C_EXCEPTION_DOT}' font-size='11'>"
            f"raises {name_text}</text>"
        )
    else:
        type_text = _esc(pl.port.type)
        if type_text:
            label = f"{name_text}: <tspan fill='{C_PORT_TYPE}'>{type_text}</tspan>"
        else:
            label = name_text
        lines.append(
            f"    <text x='{_r(lx)}' y='{_r(label_y)}'"
            f" text-anchor='{anchor}' dominant-baseline='middle'"
            f" fill='{C_PORT_NAME}' font-size='11'>"
            f"{label}</text>"
        )

    # default value line
    if has_default:
        default_text = _esc(_trunc(str(pl.port.default)))
        lines.append(
            f"    <text x='{_r(lx)}' y='{_r(cy + 10)}'"
            f" text-anchor='{anchor}' dominant-baseline='middle'"
            f" fill='{C_DEFAULT}' font-size='10'>"
            f"= {default_text}</text>"
        )


# ── Main render entry point ───────────────────────────────────────────────────


def render_svg(layout: DiagramLayout) -> str:
    W, H = layout.canvas_width, layout.canvas_height
    lines: list[str] = []

    # SVG open tag
    lines.append(
        f"<svg xmlns='http://www.w3.org/2000/svg'"
        f" width='{_r(W)}' height='{_r(H)}'"
        f" viewBox='0 0 {_r(W)} {_r(H)}'"
        f" font-family=\"'JetBrains Mono','Fira Code',monospace\""
        f" font-size='12'>"
    )
    lines.append(f"  <title>{_esc(layout.spec.title)}</title>")

    # defs
    lines.extend(_defs())

    # canvas background
    lines.append(f"  <rect width='{_r(W)}' height='{_r(H)}' fill='{C_CANVAS}'/>")

    # diagram title
    lines.append(
        f"  <text x='{_r(W / 2)}' y='30'"
        f" text-anchor='middle' dominant-baseline='middle'"
        f" fill='{C_DIAGRAM_TTL}' font-size='14' font-weight='600'>"
        f"{_esc(layout.spec.title)}</text>"
    )

    # ── edges first (appear under cards) ─────────────────────────────────────
    for edge in layout.spec.edges:
        src = layout.get_output_port(edge.from_node, edge.from_port)
        dst = layout.get_input_port(edge.to_node, edge.to_port)
        if src and dst:
            lines.append(_edge(src.cx, src.cy, dst.cx, dst.cy))
        else:
            missing = []
            if not src:
                missing.append(
                    f"output port '{edge.from_port}' on node '{edge.from_node}'"
                )
            if not dst:
                missing.append(f"input port '{edge.to_port}' on node '{edge.to_node}'")
            msg = "WARNING: edge skipped — not found: " + ", ".join(missing)
            print(msg, file=sys.stderr)
            lines.append(f"  <!-- {msg} -->")

    # ── node cards ────────────────────────────────────────────────────────────
    for nl in layout.nodes:
        lines.extend(_node_card(nl))

    lines.append("</svg>")
    return "\n".join(lines)
