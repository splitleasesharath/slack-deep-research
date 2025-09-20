# Playwright MCP with State Storage

This setup allows you to use Playwright MCP with persistent browser state (cookies, localStorage, etc.) so you stay logged into websites between sessions.

## Setup Instructions

### 1. Install Dependencies
```bash
cd playwright-mcp-state
npm install
```

### 2. Save Your Browser State
Run this to open a browser where you can log into your websites:
```bash
npm run save-state
# OR
npm run manage  # Interactive menu with more options
```

### 3. Configure Claude to Use Custom Playwright Server

Add this to your Claude config (`.claude.json`):

```json
{
  "mcpServers": {
    "playwright-state": {
      "type": "stdio",
      "command": "node",
      "args": [
        "C:\\Users\\Split Lease\\Documents\\chatgpt-deep-research\\playwright-mcp-state\\custom-playwright-server.js"
      ]
    }
  }
}
```

**Alternative:** Use the existing Playwright MCP with environment variable:

```json
{
  "mcpServers": {
    "playwright": {
      "type": "stdio",
      "command": "npx",
      "args": ["@playwright/mcp@latest"],
      "env": {
        "PLAYWRIGHT_STORAGE_STATE": "C:\\Users\\Split Lease\\Documents\\chatgpt-deep-research\\playwright-mcp-state\\storage\\auth-state.json"
      }
    }
  }
}
```

## Usage

### Managing Sessions
```bash
npm run manage
```
This opens an interactive menu to:
- Check current saved state
- Save new login sessions
- Test if saved state works
- Clear saved state

### How It Works
1. Browser state (cookies, localStorage) is saved to `storage/auth-state.json`
2. When Playwright MCP starts, it automatically loads this state
3. You stay logged into websites between Claude sessions
4. State persists until you explicitly clear it

### Files
- `save-state.js` - Quick script to save browser state
- `manage-session.js` - Interactive session manager
- `custom-playwright-server.js` - Custom MCP server with state support
- `playwright-with-state.js` - Helper class for state management
- `storage/auth-state.json` - Where your browser state is saved

### Security Note
The `auth-state.json` file contains sensitive authentication data. Keep it secure and don't share it.