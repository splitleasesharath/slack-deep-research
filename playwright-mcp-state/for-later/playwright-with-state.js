const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs').promises;

class PlaywrightWithState {
    constructor() {
        this.browser = null;
        this.context = null;
        this.statePath = path.join(__dirname, 'storage', 'auth-state.json');
    }

    async initialize() {
        try {
            // Check if state file exists
            const stateExists = await this.stateFileExists();

            this.browser = await chromium.launch({
                headless: false,
                args: ['--start-maximized']
            });

            if (stateExists) {
                console.log('Loading saved authentication state...');
                this.context = await this.browser.newContext({
                    storageState: this.statePath,
                    viewport: null
                });
            } else {
                console.log('No saved state found. Starting fresh session...');
                this.context = await this.browser.newContext({
                    viewport: null
                });
            }

            return this.context;
        } catch (error) {
            console.error('Failed to initialize Playwright:', error);
            throw error;
        }
    }

    async stateFileExists() {
        try {
            await fs.access(this.statePath);
            return true;
        } catch {
            return false;
        }
    }

    async saveCurrentState() {
        if (this.context) {
            await this.context.storageState({ path: this.statePath });
            console.log('Current state saved successfully');
        }
    }

    async newPage() {
        if (!this.context) {
            await this.initialize();
        }
        return await this.context.newPage();
    }

    async close() {
        // Save state before closing
        await this.saveCurrentState();

        if (this.browser) {
            await this.browser.close();
        }
    }
}

module.exports = PlaywrightWithState;