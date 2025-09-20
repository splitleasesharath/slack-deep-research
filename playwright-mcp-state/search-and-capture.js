const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs').promises;

async function searchAndCapture() {
    console.log('Opening Chrome with saved session...\n');

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

    console.log('📍 Navigating to Gemini...');
    await page.goto('https://gemini.google.com', { waitUntil: 'domcontentloaded' });

    // Wait for page to load
    await page.waitForTimeout(3000);

    console.log('🔍 Looking for input field...');

    // Find the input field
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
            console.log(`✅ Found input field`);

            // Click to focus
            await page.click(selector);
            await page.waitForTimeout(500);

            // Type the search query
            const searchQuery = "Tell me about the game Lemmings and the concept of being stuck with the same tool or approach in problem-solving";
            console.log(`\n📝 Typing search query:`);
            console.log(`   "${searchQuery}"\n`);

            await page.type(selector, searchQuery, { delay: 50 });

            // Press Enter to submit
            await page.keyboard.press('Enter');

            console.log('✅ Search submitted! Waiting for response...\n');
            inputFound = true;
            break;
        } catch {
            // Try next selector
        }
    }

    if (!inputFound) {
        console.log('❌ Could not find input field');
        await context.close();
        return;
    }

    // Wait for Gemini to start responding
    console.log('⏳ Waiting for Gemini to respond...');

    // Wait for response elements to appear
    await page.waitForTimeout(5000); // Initial wait for response to start

    // Try to detect when response is complete by checking for response elements
    try {
        // Look for response content
        await page.waitForSelector('[data-message-author="assistant"], [class*="response"], [class*="output"]', {
            timeout: 10000
        });

        console.log('📄 Response detected, waiting for it to complete...');

        // Wait additional time for response to fully render
        await page.waitForTimeout(5000);

        // Capture the current URL
        const currentUrl = page.url();
        console.log('\n✅ Response received!');
        console.log('📌 Captured URL:', currentUrl);

        // Save the URL to a file
        const urlData = {
            url: currentUrl,
            query: "Tell me about the game Lemmings and the concept of being stuck with the same tool or approach in problem-solving",
            timestamp: new Date().toISOString()
        };

        await fs.writeFile(
            path.join(__dirname, 'captured-url.json'),
            JSON.stringify(urlData, null, 2)
        );

        console.log('💾 URL saved to captured-url.json');

    } catch (error) {
        console.log('⚠️ Could not detect response automatically');
        const currentUrl = page.url();
        console.log('📌 Current URL:', currentUrl);
    }

    console.log('\n🎯 Task complete! Closing browser in 3 seconds...');
    await page.waitForTimeout(3000);

    // Close the browser
    await context.close();
    console.log('✅ Browser closed successfully');
    process.exit(0);
}

searchAndCapture().catch(console.error);