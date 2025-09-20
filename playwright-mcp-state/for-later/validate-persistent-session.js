const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs').promises;

async function validatePersistentSession() {
    console.log('Reopening Chrome with saved persistent session...\n');

    // Use the same persistent context directory
    const userDataDir = path.join(__dirname, 'chrome-persistent-profile');

    // Check if the directory exists
    try {
        await fs.access(userDataDir);
        console.log('✅ Found saved persistent profile at:', userDataDir);
    } catch {
        console.log('❌ No saved profile found!');
        return;
    }

    // Launch with the SAME configuration as before
    const context = await chromium.launchPersistentContext(userDataDir, {
        headless: false,
        channel: 'chrome',
        viewport: null,
        args: [
            '--disable-blink-features=AutomationControlled',
            '--disable-features=site-per-process',
            '--start-maximized'
        ],
        ignoreDefaultArgs: ['--enable-automation'],
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    });

    console.log('✅ Chrome relaunched with persistent context');
    console.log('\n🔍 VALIDATION TESTS:');
    console.log('1. Navigating to Gmail to check if logged in...');
    console.log('2. Then to GitHub...');
    console.log('3. Finally to Google Account page...\n');

    const page = await context.newPage();

    // Test 1: Gmail
    console.log('Testing Gmail...');
    await page.goto('https://mail.google.com');
    await page.waitForTimeout(3000);

    // Check if we're logged in by looking for compose button or email
    try {
        await page.waitForSelector('[aria-label*="Compose"]', { timeout: 5000 });
        console.log('✅ Gmail: LOGGED IN - Compose button found!');
    } catch {
        console.log('❌ Gmail: Not logged in or different UI');
    }

    // Test 2: GitHub
    console.log('\nTesting GitHub...');
    await page.goto('https://github.com');
    await page.waitForTimeout(2000);

    // Check for user menu (indicates logged in)
    try {
        await page.waitForSelector('img.avatar', { timeout: 5000 });
        console.log('✅ GitHub: LOGGED IN - Avatar found!');
    } catch {
        console.log('❌ GitHub: Not logged in');
    }

    // Test 3: Google Account
    console.log('\nTesting Google Account page...');
    await page.goto('https://myaccount.google.com');
    await page.waitForTimeout(2000);

    // Check for account name or profile picture
    try {
        await page.waitForSelector('[aria-label*="Google Account"]', { timeout: 5000 });
        console.log('✅ Google Account: LOGGED IN!');
    } catch {
        console.log('❌ Google Account: Not logged in');
    }

    console.log('\n📊 VALIDATION COMPLETE!');
    console.log('If you see ✅ marks above, your persistent session is working!');
    console.log('\nThe browser will stay open for you to verify manually.');
    console.log('Press Ctrl+C when done.\n');

    // Keep running
    await new Promise(() => {});
}

validatePersistentSession().catch(console.error);