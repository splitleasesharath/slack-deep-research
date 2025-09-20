const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs').promises;

async function saveState() {
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();

    console.log('Browser opened. Please log into your websites.');
    console.log('Press Enter when you are done logging in...');

    // Wait for user to press Enter
    await new Promise(resolve => {
        process.stdin.once('data', resolve);
    });

    // Save the storage state
    const statePath = path.join(__dirname, 'storage', 'auth-state.json');
    await context.storageState({ path: statePath });

    console.log(`State saved to ${statePath}`);

    await browser.close();
}

saveState().catch(console.error);