# Dataflow Diagram — JSON Conventions

A dataflow diagram is a **roadmap for coding**. Logic flow must be correct. Naming and wording can be approximate — fix them when the implementation is written.

---

## 1. The Main Function Is the Title, Not a Node

The outermost function being documented = the diagram title. Its sub-calls = the nodes.

**Example:** documenting `run_ai_verdict` → title is `"AI Verdict — run_ai_verdict flow"`. `run_ai_verdict` is NOT a node.

This matches the `cli_main` example: `__main__` is the title, its sub-calls (`parse_args`, `read_text`, etc.) are the nodes.

---

## 2. Thinking Order for Building JSON

After Gherkin and component extraction (Nouns, Verbs), build the JSON in this order:

1. **Main function** → set as diagram title
2. **Config node** → raw parameters from the main function's scope that flow to sub-calls. Name it `"{main_function} — inputs"`. List outputs short-range-first (see §5).
3. **Library nodes** → external dependencies not written by you: DB calls, LLM clients, `json.loads`, `Path.read_text`, etc.
4. **Internal function nodes** → functions you wrote that are called by the main function.
5. **Datamodel nodes** → Pydantic models or data structures that package data.
6. **Assign columns** → in strict call-dependency order (see §3).
7. **Stack same-column nodes** → to keep the diagram compact (see §4).
8. **List ports** → all inputs, outputs, exceptions per node (see §5 and §6).

---

## 3. Column Ordering Rule — Most Critical

Nodes must be ordered left-to-right by **call dependency**:

> If function A calls function B to get a result, B appears in a **lower column number** (to the left of A).

Independent nodes (neither depends on the other's output) can share the same column.

**Anti-pattern to avoid:** placing A before B even though A needs B's output. The arrow points left-to-right and looks plausible — but it is logically reversed. B must always appear left of A.

---

## 4. Column Stacking Rule

To keep diagrams compact (not too wide), stack related nodes vertically within the same column:

- **Datamodel nodes** belong in the **same column** as the node whose output they package, placed **below** it.
- **Independent nodes** called at the same logical stage belong in the same column.

**Example:** `_build_judge_prompt` (function) produces `messages`; `LLMRequest` (datamodel) packages those messages into a request object. Both go in column 1 — function on top, datamodel below.

**Example:** `Message (score update)` (datamodel) produces a `Message` object; `db.commit` (library) writes it. Both go in the same column — datamodel on top, library below.

Do NOT give every node its own column — this produces diagrams that are too wide to read when embedded in dev notes.

---

## 5. Port Ordering Rule

When listing **outputs** on a node, order them so that **shorter-range connections come first** (top) and **longer-range connections come last** (bottom). This minimizes visual edge crossings.

**Example:** a config node sends 3 values to column 1 and 1 value to column 4. List the 3 column-1 values first, then the column-4 value last.

---

## 6. Node Type Guide

| Node type   | Header color | When to use |
|-------------|--------------|-------------|
| `function`  | Blue         | Functions YOU wrote with real logic or behavior |
| `datamodel` | Violet       | Pydantic models or data structures that package data |
| `config`    | Teal         | Parameter scope of the main function — raw inputs that flow to sub-calls |
| `library`   | Orange       | External dependencies not written by you: DB clients, LLM clients, stdlib |

---

## 7. Exception Placement Rule

Exceptions belong on the node that **actually raises them**:

| Node type   | Valid exceptions |
|-------------|-----------------|
| `function`  | Logic errors from your own code |
| `library`   | External failures: `DBWriteError`, `LLMCallError`, network errors |
| `datamodel` | `ValidationError` only (Pydantic schema validation) — never DB or LLM errors |
| `config`    | Never — config nodes have no behavior |

---

## 8. Diagram File Naming and Embedding

### Naming rule

Diagram files live in `docs/diagrams/`. Use a date prefix matching the dev note the diagram belongs to, followed by a descriptive name.

- ✅ `20260416_llm_service.svg`, `20260409_ai_verdict.svg`
- ❌ `ai_verdict.svg` — no date prefix makes it ambiguous when multiple diagrams accumulate

Each diagram produces two files: `.json` (source) and `.svg` (rendered output).

### Embedding in dev notes

Every dev note with a diagram section must embed the SVG inline using a markdown image reference. Place it immediately after the JSON/SVG path lines, before the "Flow:" description:

```markdown
JSON: `docs/diagrams/20260416_llm_service.json`
SVG: `docs/diagrams/20260416_llm_service.svg`

![LLM Service Dataflow](../../docs/diagrams/20260416_llm_service.svg)

Flow: ...
```

The relative path `../../docs/diagrams/` assumes the dev note lives in `archive/development_notes/`.

---

## 9. Common Anti-Patterns

| Anti-pattern | Why it's wrong | Fix |
|---|---|---|
| Orchestrator with forwarded-input outputs | Implies the orchestrator *computes* those values — it doesn't | Use a `config` node for the parameter scope |
| `DBWriteError` on a datamodel node | Datamodels don't write to the DB | Move it to the library node that calls `db.commit` |
| Backwards call order | Arrow looks valid but dependency is reversed | B must appear to the LEFT of A if A needs B's output |
| Every node in its own column | Produces diagrams too wide to embed in dev notes | Stack related nodes (especially datamodels) in the same column |
