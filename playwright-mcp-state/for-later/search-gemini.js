const { chromium } = require('playwright');
const path = require('path');

async function searchGemini() {
    console.log('Opening Chrome with saved session to search Gemini...\n');

    const userDataDir = path.join(__dirname, 'chrome-persistent-profile');

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

    const page = await context.newPage();

    console.log('Navigating to Gemini...');
    await page.goto('https://gemini.google.com', { waitUntil: 'domcontentloaded' });

    // Wait for page to load
    await page.waitForTimeout(3000);

    console.log('Looking for input field...');

    // Try different selectors for the Gemini input field
    const selectors = [
        'textarea[placeholder*="Enter a prompt"]',
        'textarea[placeholder*="Message"]',
        'div[contenteditable="true"]',
        'textarea.ql-editor',
        '[role="textbox"]'
    ];

    let inputFound = false;
    for (const selector of selectors) {
        try {
            await page.waitForSelector(selector, { timeout: 3000 });
            console.log(`✅ Found input field: ${selector}`);

            // Click to focus
            await page.click(selector);
            await page.waitForTimeout(500);

            // Type the search query
            const searchQuery = "Tell me about lemmings and the concept of being stuck with the same tool or approach";
            console.log(`\n📝 Typing: "${searchQuery}"`);

            await page.type(selector, searchQuery, { delay: 50 });

            // Press Enter to submit
            await page.keyboard.press('Enter');

            console.log('✅ Search submitted!\n');
            console.log('Gemini is now processing your query...');
            inputFound = true;
            break;
        } catch {
            // Try next selector
        }
    }

    if (!inputFound) {
        console.log('\n⚠️ Could not find the input field automatically.');
        console.log('Please type manually in the browser:');
        console.log('"Tell me about lemmings and the concept of being stuck with the same tool or approach"');
    }

    console.log('\n🌐 Browser is open. Gemini should be responding to your query.');
    console.log('Press Ctrl+C when done.\n');

    // Keep running
    await new Promise(() => {});
}

searchGemini().catch(console.error);