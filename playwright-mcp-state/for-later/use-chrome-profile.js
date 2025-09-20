const { chromium } = require('playwright');
const path = require('path');

async function useExistingChromeProfile() {
    console.log('Starting Chrome with Profile 4 (leasesplit.com)...\n');

    // Launch Chrome with existing profile
    const browser = await chromium.launchPersistentContext(
        path.join('C:', 'Users', 'Split Lease', 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Profile 4'),
        {
            headless: false,
            channel: 'chrome',  // Use real Chrome instead of Chromium
            viewport: null,
            args: [
                '--start-maximized'
            ]
        }
    );

    console.log('✅ Chrome launched with your existing profile');
    console.log('You should be logged into all your accounts!\n');

    // Get the first page or create a new one
    let page = browser.pages()[0];
    if (!page) {
        page = await browser.newPage();
    }

    console.log('Navigating to Gemini...');
    await page.goto('https://gemini.google.com', { waitUntil: 'networkidle' });

    // Wait a moment for page to load
    await page.waitForTimeout(3000);

    console.log('Searching for lemon meringue pie recipes...\n');

    // Try to find and click on the input field
    try {
        // Look for the main input field in Gemini
        const inputSelector = 'textarea[placeholder*="Enter a prompt"], textarea[aria-label*="Message"], div[contenteditable="true"]';

        await page.waitForSelector(inputSelector, { timeout: 10000 });
        await page.click(inputSelector);

        // Type the search query
        const searchQuery = "Give me 5 different lemon meringue pie recipes with varying difficulty levels";
        await page.type(inputSelector, searchQuery);

        console.log('✅ Typed search query');
        console.log('📝 Query: "' + searchQuery + '"');

        // Press Enter to submit
        await page.keyboard.press('Enter');

        console.log('✅ Submitted search\n');
        console.log('Gemini is now processing your request...');

    } catch (error) {
        console.log('Note: You may need to manually type the search if the input field has changed.');
        console.log('Search for: "Give me 5 different lemon meringue pie recipes with varying difficulty levels"');
    }

    console.log('\n🌐 Browser is open. You can interact with it manually.');
    console.log('Press Ctrl+C when you want to close the browser.\n');

    // Keep the browser open
    await new Promise(() => {});
}

useExistingChromeProfile().catch(console.error);