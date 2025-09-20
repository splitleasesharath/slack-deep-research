#!/usr/bin/env node

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs').promises;

// Path to stored authentication state
const STATE_PATH = path.join(__dirname, 'storage', 'auth-state.json');

class PlaywrightMCPServer {
    constructor() {
        this.server = new Server({
            name: 'playwright-with-state',
            version: '1.0.0'
        });
        this.browser = null;
        this.context = null;
        this.page = null;

        this.setupHandlers();
    }

    async checkStateFile() {
        try {
            await fs.access(STATE_PATH);
            return true;
        } catch {
            return false;
        }
    }

    async initializeBrowser() {
        if (this.browser) {
            return;
        }

        this.browser = await chromium.launch({
            headless: false
        });

        const hasState = await this.checkStateFile();

        if (hasState) {
            console.error('Loading saved authentication state...');
            this.context = await this.browser.newContext({
                storageState: STATE_PATH
            });
        } else {
            console.error('No saved state found. Starting fresh session...');
            this.context = await this.browser.newContext();
        }

        this.page = await this.context.newPage();
    }

    async saveState() {
        if (this.context) {
            await this.context.storageState({ path: STATE_PATH });
            console.error('State saved successfully');
        }
    }

    setupHandlers() {
        // List available tools
        this.server.setRequestHandler('tools/list', async () => {
            return {
                tools: [
                    {
                        name: 'navigate',
                        description: 'Navigate to a URL',
                        inputSchema: {
                            type: 'object',
                            properties: {
                                url: { type: 'string' }
                            },
                            required: ['url']
                        }
                    },
                    {
                        name: 'screenshot',
                        description: 'Take a screenshot',
                        inputSchema: {
                            type: 'object',
                            properties: {
                                path: { type: 'string' }
                            }
                        }
                    },
                    {
                        name: 'click',
                        description: 'Click an element',
                        inputSchema: {
                            type: 'object',
                            properties: {
                                selector: { type: 'string' }
                            },
                            required: ['selector']
                        }
                    },
                    {
                        name: 'fill',
                        description: 'Fill an input field',
                        inputSchema: {
                            type: 'object',
                            properties: {
                                selector: { type: 'string' },
                                text: { type: 'string' }
                            },
                            required: ['selector', 'text']
                        }
                    },
                    {
                        name: 'save_state',
                        description: 'Save current browser state',
                        inputSchema: {
                            type: 'object',
                            properties: {}
                        }
                    },
                    {
                        name: 'clear_state',
                        description: 'Clear saved authentication state',
                        inputSchema: {
                            type: 'object',
                            properties: {}
                        }
                    }
                ]
            };
        });

        // Handle tool calls
        this.server.setRequestHandler('tools/call', async (request) => {
            const { name, arguments: args } = request.params;

            await this.initializeBrowser();

            switch (name) {
                case 'navigate':
                    await this.page.goto(args.url);
                    return { content: [{ type: 'text', text: `Navigated to ${args.url}` }] };

                case 'screenshot':
                    const screenshotPath = args.path || `screenshot-${Date.now()}.png`;
                    await this.page.screenshot({ path: screenshotPath });
                    return { content: [{ type: 'text', text: `Screenshot saved to ${screenshotPath}` }] };

                case 'click':
                    await this.page.click(args.selector);
                    return { content: [{ type: 'text', text: `Clicked ${args.selector}` }] };

                case 'fill':
                    await this.page.fill(args.selector, args.text);
                    return { content: [{ type: 'text', text: `Filled ${args.selector}` }] };

                case 'save_state':
                    await this.saveState();
                    return { content: [{ type: 'text', text: 'Browser state saved' }] };

                case 'clear_state':
                    try {
                        await fs.unlink(STATE_PATH);
                        return { content: [{ type: 'text', text: 'Authentication state cleared' }] };
                    } catch {
                        return { content: [{ type: 'text', text: 'No state file to clear' }] };
                    }

                default:
                    throw new Error(`Unknown tool: ${name}`);
            }
        });
    }

    async run() {
        const transport = new StdioServerTransport();
        await this.server.connect(transport);
        console.error('Playwright MCP Server with state management running');

        // Cleanup on exit
        process.on('SIGINT', async () => {
            await this.saveState();
            if (this.browser) {
                await this.browser.close();
            }
            process.exit(0);
        });
    }
}

const server = new PlaywrightMCPServer();
server.run().catch(console.error);