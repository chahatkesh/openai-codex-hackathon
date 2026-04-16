# Hackathon Video Flow

Use this diagram for the 20-30 second architecture moment in the submission
video. It compresses `docs/flow.md` into the critical story: Codex discovers
capabilities through MCP, FuseKit executes and bills live tools, and missing
APIs become new tools through a Codex-powered integration loop.

```mermaid
flowchart TD
    A[Developer asks for outcome] --> B[Codex plans, writes code, and calls tools]
    B -->|MCP discovery and execution| C[FuseKit MCP server]
    C --> D{Tool in catalog?}

    D -->|Yes| E[Wallet check and credit deduction]
    E --> F[Execute live API tool]
    F --> G[Result returns to Codex]
    G --> H[Email, SMS, or data delivered]

    D -->|Missing| I[TOOL_NOT_FOUND]
    I --> J[Create integration job]
    J --> K[Codex reads API docs]
    K --> L[Codex generates wrapper]
    L --> M[Codex tests, fixes, and retries]
    M --> N[Publish new MCP tool]
    N --> C

    B --> O[Not possible without Codex]
    O --> K

    C --> P[Developer experience: one MCP URL, one wallet, no glue code]

    classDef codexStyle fill:#0f9f6e,color:#ffffff,stroke:#064e3b,stroke-width:2px;
    classDef mcpStyle fill:#111827,color:#ffffff,stroke:#38bdf8,stroke-width:2px;
    classDef pipelineStyle fill:#f59e0b,color:#111827,stroke:#92400e,stroke-width:2px;
    classDef successStyle fill:#ecfdf5,color:#064e3b,stroke:#10b981,stroke-width:2px;
    classDef dxStyle fill:#fff7ed,color:#7c2d12,stroke:#fb923c,stroke-width:2px;

    class B,O,K,L,M codexStyle;
    class C mcpStyle;
    class I,J pipelineStyle;
    class H,N successStyle;
    class P dxStyle;
```

## 25-Second Voiceover

"A developer asks for an outcome. Codex plans it, then asks FuseKit over MCP
what tools exist. If a tool is live, FuseKit checks the wallet and executes it.
If it is missing, the gap becomes an integration job. This is the Codex-only
part: it reads docs, writes code, tests, fixes errors, and publishes a new MCP
tool. Next time, that API is instant: no keys, no glue code, no context switch."

## Screen Emphasis

- Open on `Developer prompt -> Codex -> MCP server`.
- Pause on `Tool in catalog?` to show the product insight: capability gaps are
  handled inside the agent workflow.
- Zoom into `Codex integration loop` and say "this is not a script; Codex is
  doing real engineering work."
- End on `Living catalog grows` and `Developer experience`: every successful
  integration becomes reusable infrastructure.
