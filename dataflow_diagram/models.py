from dataclasses import dataclass, field


# ── Raw spec (from JSON) ──────────────────────────────────────────────────────


@dataclass
class Port:
    name: str
    type: str
    default: str | None = None
    internal: bool = False


@dataclass
class ExceptionPort:
    name: str  # exception class name, e.g. "ValueError"


@dataclass
class NodeSpec:
    id: str
    name: str
    column: int
    node_type: str = "function"  # "function" | "datamodel" | "config" | "library"
    async_fn: bool = False
    inputs: list[Port] = field(default_factory=list)
    outputs: list[Port] = field(default_factory=list)
    exceptions: list[ExceptionPort] = field(default_factory=list)


@dataclass
class EdgeSpec:
    from_node: str
    from_port: str
    to_node: str
    to_port: str


@dataclass
class DiagramSpec:
    title: str
    nodes: list[NodeSpec] = field(default_factory=list)
    edges: list[EdgeSpec] = field(default_factory=list)


# ── Layout-enriched (computed by layout.py) ───────────────────────────────────


@dataclass
class PortLayout:
    port: Port
    cx: float  # absolute x of port dot centre
    cy: float  # absolute y of port dot centre
    side: str  # "input" | "output" | "exception"


@dataclass
class NodeLayout:
    spec: NodeSpec
    x: float
    y: float
    width: float
    height: float
    input_ports: list[PortLayout] = field(default_factory=list)
    output_ports: list[PortLayout] = field(default_factory=list)
    exception_ports: list[PortLayout] = field(default_factory=list)


@dataclass
class DiagramLayout:
    spec: DiagramSpec
    nodes: list[NodeLayout] = field(default_factory=list)
    canvas_width: float = 0
    canvas_height: float = 0

    def get_node(self, node_id: str) -> NodeLayout | None:
        return next((n for n in self.nodes if n.spec.id == node_id), None)

    def get_output_port(self, node_id: str, port_name: str) -> PortLayout | None:
        node = self.get_node(node_id)
        if node:
            return next(
                (p for p in node.output_ports if p.port.name == port_name), None
            )
        return None

    def get_input_port(self, node_id: str, port_name: str) -> PortLayout | None:
        node = self.get_node(node_id)
        if node:
            return next((p for p in node.input_ports if p.port.name == port_name), None)
        return None
