const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs').promises;

async function loginAndSave() {
    console.log('Opening browser for login...');
    const browser = await chromium.launch({
        headless: false,
        args: ['--start-maximized']
    });

    const context = await browser.newContext({
        viewport: null
    });

    const page = await context.newPage();

    console.log('\n📌 INSTRUCTIONS:');
    console.log('1. Log into all your websites (Gmail, GitHub, etc.)');
    console.log('2. Keep this terminal open');
    console.log('3. When done, close the browser window');
    console.log('\nThe state will be automatically saved when you close the browser.\n');

    // Wait for browser to be closed by user
    browser.on('disconnected', async () => {
        console.log('Browser closed by user. Saving state...');
    });

    // Navigate to a common login page to start
    await page.goto('https://www.google.com');

    // Wait for the browser to be closed
    await new Promise((resolve) => {
        browser.on('disconnected', resolve);
    });

    // Save state before browser fully closes
    const statePath = path.join(__dirname, 'storage', 'auth-state.json');
    try {
        await context.storageState({ path: statePath });
        console.log(`✅ State saved to ${statePath}`);
        console.log('\nYour logged-in sessions have been saved!');
        console.log('This state will be used by Playwright MCP automatically.');
    } catch (error) {
        console.log('Note: State might already be saved or browser was closed too quickly.');
    }

    process.exit(0);
}

loginAndSave().catch(console.error);