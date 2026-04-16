# FuseKit Target Architecture

## Purpose

Freeze the product architecture for the next implementation phase.

FuseKit is a capability platform with two interfaces:

- `MCP` for the user-facing Codex (UFC) during build time
- `HTTP` for deployed apps during runtime

The integration/codegen pipeline remains out of scope for this phase. This
phase focuses on the already existing built-in capabilities.

## Core Model

Each FuseKit capability should be treated as a reusable platform primitive with:

- a catalog/tool definition in the database
- an MCP discovery surface for UFC
- a machine-readable manifest that tells UFC how to call FuseKit at runtime
- an HTTP execution endpoint used by the deployed app
- billing metadata used for wallet deduction

## Build-Time Flow

1. UFC connects to FuseKit via MCP.
2. UFC checks what built-in capabilities already exist.
3. UFC retrieves a capability manifest for the needed built-in capability.
4. UFC uses that manifest to generate the user’s deployed app.

## Runtime Flow

1. The deployed app calls a FuseKit HTTP execution endpoint.
2. FuseKit authenticates the caller to a FuseKit account/project token model.
3. FuseKit checks wallet balance.
4. FuseKit executes the capability.
5. FuseKit logs the execution.
6. FuseKit returns the provider result to the deployed app.

## Internal Execution Layer

FuseKit should have one shared internal execution service used by:

- MCP `tools/call`
- HTTP `/api/execute/{tool_name}`

That internal executor is responsible for:

- tool lookup
- wallet deduction and refund policy
- runtime executor lookup
- success/error logging
- consistent error shapes
