const { firefox } = require('playwright');
const path = require('path');
const fs = require('fs').promises;

async function openFirefoxForLogin() {
    console.log('Starting Firefox for login...');

    const browser = await firefox.launch({
        headless: false,
        slowMo: 100
    });

    const context = await browser.newContext();
    const page = await context.newPage();

    console.log('\n📌 Firefox is now open!');
    console.log('1. Log into your websites (Gmail, GitHub, etc.)');
    console.log('2. When done, close the browser');
    console.log('3. State will be saved automatically\n');

    // Go to Google
    await page.goto('https://www.google.com');

    // Handle browser close
    browser.on('disconnected', async () => {
        console.log('\nBrowser closed. Saving state...');
        const statePath = path.join(__dirname, 'storage', 'auth-state.json');

        try {
            // Save state before exit
            await context.storageState({ path: statePath });
            console.log('✅ State saved successfully!');
        } catch (e) {
            // State might already be saved
        }

        process.exit(0);
    });

    // Keep script running
    await new Promise(() => {});
}

openFirefoxForLogin().catch(console.error);