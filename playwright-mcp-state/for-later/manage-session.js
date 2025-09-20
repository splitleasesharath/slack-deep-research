const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs').promises;
const readline = require('readline');

const STATE_PATH = path.join(__dirname, 'storage', 'auth-state.json');

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

function question(query) {
    return new Promise(resolve => rl.question(query, resolve));
}

async function checkState() {
    try {
        await fs.access(STATE_PATH);
        const stat = await fs.stat(STATE_PATH);
        const data = await fs.readFile(STATE_PATH, 'utf-8');
        const state = JSON.parse(data);

        console.log('\n📁 State file exists');
        console.log(`📅 Last modified: ${stat.mtime.toLocaleString()}`);
        console.log(`🍪 Cookies: ${state.cookies?.length || 0} saved`);
        console.log(`🗂️ Origins with localStorage: ${state.origins?.length || 0}`);

        if (state.cookies && state.cookies.length > 0) {
            console.log('\n🌐 Domains with saved cookies:');
            const domains = [...new Set(state.cookies.map(c => c.domain))];
            domains.forEach(d => console.log(`   • ${d}`));
        }

        return true;
    } catch (error) {
        console.log('\n❌ No saved state found');
        return false;
    }
}

async function saveNewState() {
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();

    console.log('\n🌐 Browser opened. Please log into your websites.');
    console.log('💡 Tip: Log into all websites you want to save credentials for');
    console.log('\nPress Enter when you are done logging in...');

    await question('');

    await context.storageState({ path: STATE_PATH });
    console.log(`\n✅ State saved to ${STATE_PATH}`);

    await browser.close();
}

async function testState() {
    const hasState = await checkState();
    if (!hasState) {
        console.log('No state to test. Please save a state first.');
        return;
    }

    const url = await question('\nEnter URL to test (or press Enter to skip): ');

    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext({ storageState: STATE_PATH });
    const page = await context.newPage();

    if (url) {
        await page.goto(url);
    }

    console.log('\n✅ Browser opened with saved state');
    console.log('Check if you are logged in. Press Enter to close...');

    await question('');
    await browser.close();
}

async function clearState() {
    try {
        await fs.unlink(STATE_PATH);
        console.log('\n✅ State cleared successfully');
    } catch (error) {
        console.log('\n❌ No state to clear');
    }
}

async function main() {
    console.log('🎭 Playwright MCP State Manager');
    console.log('================================\n');

    while (true) {
        console.log('\nOptions:');
        console.log('1. Check current state');
        console.log('2. Save new state (login to websites)');
        console.log('3. Test saved state');
        console.log('4. Clear saved state');
        console.log('5. Exit');

        const choice = await question('\nSelect option (1-5): ');

        switch (choice) {
            case '1':
                await checkState();
                break;
            case '2':
                await saveNewState();
                break;
            case '3':
                await testState();
                break;
            case '4':
                await clearState();
                break;
            case '5':
                rl.close();
                process.exit(0);
            default:
                console.log('Invalid option');
        }
    }
}

main().catch(console.error);