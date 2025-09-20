const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs').promises;

async function testAndSaveSession() {
    console.log('Opening Chrome session to test and save state...\n');

    // Use the temporary Chrome profile we created
    const tempProfileDir = path.join(__dirname, 'temp-chrome-profile');

    try {
        // Check if temp profile exists
        await fs.access(tempProfileDir);
        console.log('✅ Found temporary Chrome profile\n');
    } catch {
        console.log('❌ No temporary profile found. Creating new one...\n');
        await fs.mkdir(tempProfileDir, { recursive: true });
    }

    // Launch Chrome with persistent context
    const context = await chromium.launchPersistentContext(tempProfileDir, {
        headless: false,
        channel: 'chrome',
        viewport: null,
        args: ['--start-maximized']
    });

    console.log('✅ Chrome opened with persistent session');
    console.log('\n📌 WHAT TO DO:');
    console.log('1. Check if you are logged in to any sites');
    console.log('2. If not, log into Google, GitHub, etc.');
    console.log('3. Navigate to a few pages to test the session');
    console.log('4. When ready, press Enter here to save the state\n');

    const page = await context.newPage();

    // Go to Google to check login status
    await page.goto('https://myaccount.google.com');

    // Wait for user to press Enter
    console.log('Press Enter when you want to save the current state...');
    await new Promise(resolve => {
        process.stdin.once('data', resolve);
    });

    // Save the state to a JSON file
    const statePath = path.join(__dirname, 'storage', 'chrome-session-state.json');

    // Ensure storage directory exists
    await fs.mkdir(path.join(__dirname, 'storage'), { recursive: true });

    // Save the state
    await context.storageState({ path: statePath });

    console.log('\n✅ SUCCESS! State has been saved to:');
    console.log(`   ${statePath}`);

    // Check what was saved
    const savedState = JSON.parse(await fs.readFile(statePath, 'utf8'));
    console.log('\n📊 State Summary:');
    console.log(`   - Cookies saved: ${savedState.cookies?.length || 0}`);
    console.log(`   - Local storage origins: ${savedState.origins?.length || 0}`);

    if (savedState.cookies && savedState.cookies.length > 0) {
        const domains = [...new Set(savedState.cookies.map(c => c.domain))];
        console.log('\n🌐 Domains with saved cookies:');
        domains.slice(0, 10).forEach(d => console.log(`   • ${d}`));
        if (domains.length > 10) {
            console.log(`   ... and ${domains.length - 10} more`);
        }
    }

    console.log('\n✨ This state file can now be used with Playwright MCP!');
    console.log('The session will persist across browser restarts.\n');

    await context.close();
    process.exit(0);
}

testAndSaveSession().catch(console.error);