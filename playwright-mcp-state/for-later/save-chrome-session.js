const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs').promises;

async function saveChromeSession() {
    console.log('Opening Chrome to save your logged-in session...\n');

    // Use the full User Data directory and specify the profile
    const userDataDir = path.join('C:', 'Users', 'Split Lease', 'AppData', 'Local', 'Google', 'Chrome', 'User Data');

    const browser = await chromium.launch({
        headless: false,
        channel: 'chrome',  // Use real Chrome
        args: [
            `--user-data-dir=${userDataDir}`,
            '--profile-directory=Profile 4',  // Specifically use Profile 4
            '--start-maximized'
        ]
    });

    const context = await browser.newContext();
    const page = await context.newPage();

    console.log('✅ Chrome opened with Profile 4 (leasesplit.com)');
    console.log('\n📌 INSTRUCTIONS:');
    console.log('1. Log into any websites you need (Google, GitHub, etc.)');
    console.log('2. When done, come back here and press Enter');
    console.log('3. State will be saved for future use\n');

    // Go to Google to start
    await page.goto('https://accounts.google.com');

    // Wait for user input
    await new Promise(resolve => {
        process.stdin.once('data', resolve);
    });

    // Save the state
    const statePath = path.join(__dirname, 'storage', 'chrome-profile4-state.json');
    await context.storageState({ path: statePath });

    console.log(`\n✅ State saved to ${statePath}`);
    console.log('This state can now be used with Playwright MCP!');

    await browser.close();
}

// Alternative: Use persistent context which maintains the profile
async function usePersistentProfile() {
    console.log('Opening Chrome with persistent Profile 4...\n');

    // This will use the actual Chrome profile directory
    const profilePath = path.join('C:', 'Users', 'Split Lease', 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Profile 4');

    try {
        // Check if profile exists
        await fs.access(profilePath);
        console.log('✅ Found Profile 4 directory');
    } catch {
        console.log('❌ Profile 4 directory not found!');
        return;
    }

    // Copy the profile to a temporary location to avoid conflicts
    const tempProfileDir = path.join(__dirname, 'temp-chrome-profile');

    // Create temp directory if it doesn't exist
    try {
        await fs.mkdir(tempProfileDir, { recursive: true });
    } catch {}

    console.log('Launching Chrome with persistent context...');

    const context = await chromium.launchPersistentContext(tempProfileDir, {
        headless: false,
        channel: 'chrome',
        viewport: null,
        args: ['--start-maximized']
    });

    const page = await context.newPage();

    console.log('\n📌 IMPORTANT:');
    console.log('1. This is a fresh Chrome session');
    console.log('2. Please log into your accounts');
    console.log('3. Your logins will persist for next time');
    console.log('4. Press Enter when done\n');

    await page.goto('https://accounts.google.com');

    // Wait for user
    await new Promise(resolve => {
        process.stdin.once('data', resolve);
    });

    // Save state
    const statePath = path.join(__dirname, 'storage', 'persistent-state.json');
    await context.storageState({ path: statePath });

    console.log('\n✅ Session saved!');
    console.log('Next time, this profile will be used automatically.');

    await context.close();
}

// Ask user which method to use
async function main() {
    console.log('Chrome Session Manager');
    console.log('======================\n');
    console.log('Choose an option:');
    console.log('1. Use temporary session (save state to file)');
    console.log('2. Use persistent Chrome profile (recommended)\n');

    process.stdout.write('Enter choice (1 or 2): ');

    const choice = await new Promise(resolve => {
        process.stdin.once('data', data => {
            resolve(data.toString().trim());
        });
    });

    if (choice === '1') {
        await saveChromeSession();
    } else if (choice === '2') {
        await usePersistentProfile();
    } else {
        console.log('Invalid choice');
    }

    process.exit(0);
}

main().catch(console.error);