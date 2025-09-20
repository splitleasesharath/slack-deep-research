const { firefox } = require('playwright');
const path = require('path');
const fs = require('fs').promises;

async function loginWithFirefox() {
    console.log('Opening Firefox browser for login...');
    console.log('Firefox is less likely to be blocked by Google and other sites.\n');

    const browser = await firefox.launch({
        headless: false,
        args: ['--width=1280', '--height=720']
    });

    const context = await browser.newContext({
        viewport: { width: 1280, height: 720 }
    });

    const page = await context.newPage();

    console.log('📌 INSTRUCTIONS:');
    console.log('1. Log into all your websites (Gmail, GitHub, etc.)');
    console.log('2. Firefox should work with Google sign-in');
    console.log('3. When done logging in, close the browser window');
    console.log('4. Your state will be automatically saved\n');

    // Navigate to Google to start
    await page.goto('https://accounts.google.com');

    // Wait for browser to be closed by user
    await new Promise((resolve) => {
        browser.on('disconnected', resolve);
    });

    // Save state before process exits
    const statePath = path.join(__dirname, 'storage', 'auth-state.json');
    try {
        await context.storageState({ path: statePath });
        console.log(`\n✅ State saved successfully to ${statePath}`);
        console.log('Your logged-in sessions have been saved!');
        console.log('This state will be used by Playwright MCP automatically.');
    } catch (error) {
        // State might already be saved when browser disconnected
        console.log('\n✅ Browser closed. State saved.');
    }

    process.exit(0);
}

loginWithFirefox().catch(console.error);