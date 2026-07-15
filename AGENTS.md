# Agent System Documentation

This repository uses the **Google Agent Development Kit (ADK)** to build intelligent agents that control a Minecraft bot. The system bridges Python and Node.js ecosystems to leverage the powerful **Mineflayer** library for Minecraft interactions while keeping the agent logic in Python.

The ADK documentation supports the `/llms.txt` standard for context discovery.

## Core Technologies

*   **Google ADK**: Framework for creating, managing, and running agents.
    *   [ADK /llms.txt Documentation](https://google.github.io/adk-docs/llms.txt)
*   **Mineflayer**: A robust Node.js library for creating Minecraft bots.
    *   [Mineflayer API Documentation](https://github.com/PrismarineJS/mineflayer/blob/master/docs/api.md)
*   **JSPyBridge**: A bridge that allows Python to interoperate with Node.js, enabling the use of Mineflayer directly within Python code.
    *   [JSPyBridge Repository](https://github.com/extremeheat/JSPyBridge)

## Architecture

The project separates the **Minecraft transport layer** (`mineflayer/`) from the **agent logic** (`orchestrators/` + `llm_agents/`). The transport layer owns the bot connection, tools, events, and the action queue; the orchestrators own the ADK session/runner and drive the LLM agents.

```
main.py
  └─ Client (mineflayer/client.py)
       ├─ Tools            (mineflayer/tools/)      — bot capabilities exposed to agents
       ├─ Events           (mineflayer/events/)     — bot event handlers
       ├─ ActionProcessor  (mineflayer/action_processor.py) — async action + event queue
       └─ MultiAgentOrchestrator (orchestrators/)
            ├─ AgentStateMachine (orchestrators/state_machine.py)
            ├─ ADK Runner + InMemorySessionService
            └─ LLM agents (llm_agents/)
                 ├─ TaskCoordinator  (create_task_coordinator) — routes requests
                 └─ ComplexAgent     — Planner + Action LoopAgent
```

### 1. The Client (`mineflayer/client.py`)
The `Client` class is the main entry point for the Minecraft connection. It uses `JSPyBridge` (`javascript` module) to:
*   Instantiate the Mineflayer bot (`mineflayer.createBot`).
*   Manage connection states (`STATE_IDLE`, `STATE_CONNECTING`, `STATE_CONNECTED`, `STATE_DISCONNECTED`) and run a `_heartbeat_loop` that flips to `DISCONNECTED` when the JS bridge becomes unresponsive.
*   Wire up `Events`, `Tools`, the `ActionProcessor`, and the `MultiAgentOrchestrator`.
*   Optionally initialize `prismarine-viewer` (`_reassure_viewer`, port 3001) for a web-based view of the bot.
*   Run the main loop (`run`), pulling actions off the `ActionProcessor`.

### 2. The ActionProcessor (`mineflayer/action_processor.py`)
Bridges the synchronous JS event callbacks and the async agent loop. It holds two queues:
*   An **action queue** for outgoing bot actions (`whisper`, `say`, `chat`). Master chat messages are dispatched to the agent via `_handle_chat` → `orchestrator.call_async`.
*   An **expecting-events queue** for `[SYSTEM EVENT: ...]` markers. Tools call `wait_for_events` to block on a specific completion event (e.g. `diggingCompleted`).

### 3. Orchestrators (`orchestrators/`)
The orchestrator owns everything ADK-related and is the boundary the transport layer talks to.
*   **`AgentOrchestrator`** (base): sets up the `InMemorySessionService`, the `Runner`, and the `AgentStateMachine`. `call_async` runs the ADK loop with retry/backoff on transient LLM errors (`503`, `429`, `RESOURCE_EXHAUSTED`, etc.). Default model is `gemini-3.1-flash-lite` (`_default_model`). Injects `get_knowledge()` (`knowledge.md`) and `get_skills()` (`skills/*.md`) into agent instructions.
*   **`MultiAgentOrchestrator`** (used by `Client`): overrides `_init_agents` to build a `TaskCoordinator` root agent with a `ComplexAgent` sub-agent.
*   **`AgentStateMachine`** (`state_machine.py`): tracks expectation states (`STATE_EXPECT_DIGGING`, `STATE_EXPECT_COLLECTION`, `STATE_EXPECT_CRAFTING`, `STATE_EXPECT_PLACEMENT`, `STATE_EXPECT_DESTINATION`) to filter noise events, and enforces a 60s timeout per expected state.

### 4. LLM Agents (`llm_agents/`)
The actual ADK agent definitions, decoupled from orchestration and constructed via factory functions that take an `orchestrator`:
*   **`create_general_agent`**: a single autonomous `Agent` with all tools (used by the base `AgentOrchestrator`).
*   **`create_task_coordinator`**: an `LlmAgent` that routes user requests to sub-agents and keeps user-facing chatter minimal.
*   **`ComplexAgent`**: a custom `Agent` wrapping a `LoopAgent` of a **PlannerAgent** (writes a markdown checkbox plan) and an **ActionAgent** (executes steps with tools, marks `[x]`/`[!]`). Loops until the `ALL IS DONE` completion phrase.

### 5. Tooling (`mineflayer/tools/`)
Agents interact with the world through Python methods that wrap Mineflayer API calls. The `Tools` aggregator (`tools/__init__.py`) composes topic modules — `MovementTools`, `InventoryTools`, `CreativeTools`, `BasicTools`, `MineTool`, `CollectTool`, `CraftingTool`, `BuildingTool` — and `available_methods()` returns the flat list handed to the ADK agents. All extend `tools/base.py` (shared helpers, lazy `minecraft-data`/pathfinder setup, `_result` dict convention).

### 6. Events (`mineflayer/events/`)
The `Events` aggregator binds handler modules (`BasicEvents`, `PathfindingEvents`, `MineEvents`) to bot events. Handlers translate raw Mineflayer events into `ActionProcessor` calls (e.g. master `chat` → agent) or `[SYSTEM EVENT]` markers, and keep Python references alive to avoid GC of the JS callbacks.

## Setup & Execution

The project is managed with `uv`. 

1.  **Dependencies**: Ensure Python dependencies and necessary Node.js packages (via `JSPyBridge` auto-installation or manual `npm install`) are present.
2.  **Running**: The `main.py` script initializes the `Client`, which connects the bot and starts the agent loop.

```bash
uv run main.py
```

## Development Knowledge & Best Practices
### Keep updating knowledge

If you find out a new nuance please propose updating this section. Always be mindful about new information. We don't want to flood this section


### Asynchronous Tools (Mineflayer & JSPyBridge)
When defining asynchronous tools for the Mineflayer bot (like digging, picking up items, crafting, or placing blocks):
- Always use `@javascript.AsyncTask(start=True)` to wrap the Node.js API calls to prevent blocking the Python main thread.
- Always emit a `[SYSTEM EVENT: <event_name>]` via the action processor upon completion or failure.
- Add a corresponding expectation state (e.g., `STATE_EXPECT_PLACEMENT`) to the `AgentStateMachine` to handle these events and filter noise.
- Explicitly document in the tool docstring that the agent must wait for the system event before taking another action.

### Handling JavaScript Arrays in Python (JSPyBridge)
When calling Mineflayer/Node.js functions that return arrays (like `.recipesFor()` or `bot.inventory.items()`), they are often returned as `javascript.proxy.Proxy` objects in Python.
- Python's `len()` function **cannot** be used on these objects. It will throw a `TypeError`.
- Instead, use `getattr(proxy_object, 'length', 0)` to securely find the array's length.
- Access elements via string indexes rather than integer indexes, for example: `proxy_object[str(i)]`.

### Block Placement & Timeouts
- When using Mineflayer's `bot.placeBlock()`, the method waits for a `blockUpdate` event from the Minecraft server to confirm successful placement.
- If the bot attempts to place a block inside its own collision box (e.g., at its exact feet coordinates without jumping), the server will silently reject it. Mineflayer will then hang for 5000ms until it throws a timeout error (`Event blockUpdate:... did not fire within timeout`).
- Tools must enforce distance checks (`bot.entity.position.distanceTo(target_pos)`) to ensure the placement target isn't too far (>5 blocks) or too close (inside the bot's bounding box).
- Catching Promise timeout errors natively across JSPyBridge inside an `AsyncTask` requires checking if the stringified Python exception (`str(e)`) contains specific phrases like `'did not fire within timeout'`.
