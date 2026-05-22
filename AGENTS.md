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

The project follows a component-based architecture:

### 1. The Client (`mineflayer/client.py`)
The `Client` class is the main entry point for the Minecraft connection. It uses `JSPyBridge` (`javascript` module) to:
*   Instantiate the Mineflayer bot (`mineflayer.createBot`).
*   Manage connection states (IDLE, CONNECTING, CONNECTED, DISCONNECTED).
*   Initialize the `prismarine-viewer` for a web-based view of the bot.
*   Expose `Tools` to the agent.

### 2. The Agent (`agents/base_agent.py`)
The `BaseAgent` class encapsulates the AI logic using Google ADK:
*   **Agent Definition**: Defines the `root_agent` ("main_minecraft_agent") with specific instructions and the `gemini-2.5-flash` model.
*   **Session Management**: Uses `InMemorySessionService` to maintain conversation state.
*   **Runner**: The `Runner` class executes the agent loop, processing user messages and agent tool calls asynchronously.
*   **Knowledge**: Injects static knowledge about Minecraft (e.g., item prefixes) into the agent's context.

### 3. Tooling
The agent interacts with the world through a set of defined tools. These tools are Python methods that wrap Mineflayer API calls, exposed to the ADK agent.

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
