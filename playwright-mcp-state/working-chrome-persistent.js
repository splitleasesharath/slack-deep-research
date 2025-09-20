const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs').promises;

async function launchWithPersistentContext() {
    console.log('Launching Chrome with proper configuration to avoid Google blocking...\n');

    // CRITICAL: Use a dedicated persistent context directory
    const userDataDir = path.join(__dirname, 'chrome-persistent-profile');

    // Ensure directory exists
    await fs.mkdir(userDataDir, { recursive: true });

    console.log('Using persistent context at:', userDataDir);

    // CRITICAL CONFIGURATION - This exact setup worked before:
    const context = await chromium.launchPersistentContext(userDataDir, {
        headless: false,
        channel: 'chrome',  // Use real Chrome, not Chromium
        viewport: null,
        // IMPORTANT: These args help bypass Google's detection
        args: [
            '--disable-blink-features=AutomationControlled',
            '--disable-features=site-per-process',
            '--start-maximized'
        ],
        // Additional options to appear more like regular Chrome
        ignoreDefaultArgs: ['--enable-automation'],
        // User agent to look like regular Chrome
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    });

    console.log('✅ Chrome launched with persistent context');
    console.log('\n📌 IMPORTANT NOTES:');
    console.log('1. This uses real Chrome (not Chromium)');
    console.log('2. Automation flags are disabled');
    console.log('3. Your logins will persist between sessions');
    console.log('4. Close the browser when done to save state\n');

    const page = await context.newPage();

    // Navigate to Google
    await page.goto('https://accounts.google.com');

    console.log('Browser is open. Your session will be automatically saved when you close it.');
    console.log('Press Ctrl+C here when done.\n');

    // Keep running
    await new Promise(() => {});
}

launchWithPersistentContext().catch(console.error);