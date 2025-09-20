# Playwright Browser Automation with Persistent Sessions - Complete Setup Guide

## Overview
This setup solves the "browser not secure" error when using Playwright with Google services by using persistent Chrome profiles with anti-automation detection bypass.

## Problem & Solution
- **Problem**: Google blocks Playwright's Chromium as an insecure/automated browser
- **Solution**: Use real Chrome with persistent context and anti-automation flags

## Directory Structure
```
playwright-mcp-state/
├── chrome-persistent-profile/     # Persistent browser profile data
├── storage/                       # Authentication state storage
│   ├── auth-state.json
│   └── chrome-session-state.json
├── package.json                   # Dependencies
└── [scripts listed below]
```

## Installation
```bash
cd playwright-mcp-state
npm install playwright @modelcontextprotocol/sdk
npx playwright install chromium firefox chrome
```

## Core Configuration (CRITICAL)

```javascript
// Essential configuration that bypasses Google's automation detection
const context = await chromium.launchPersistentContext(userDataDir, {
    headless: false,
    channel: 'chrome',  // MUST use real Chrome, not Chromium
    viewport: null,
    args: [
        '--disable-blink-features=AutomationControlled',  // Critical flag
        '--disable-features=site-per-process',
        '--start-maximized'
    ],
    ignoreDefaultArgs: ['--enable-automation'],  // Remove automation indicator
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
});
```

## Complete Scripts

### 1. working-chrome-persistent.js - Base Persistent Session
```javascript
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs').promises;

async function launchWithPersistentContext() {
    console.log('Launching Chrome with proper configuration to avoid Google blocking...\\n');

    const userDataDir = path.join(__dirname, 'chrome-persistent-profile');
    await fs.mkdir(userDataDir, { recursive: true });

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
    await page.goto('https://accounts.google.com');

    console.log('Browser is open. Your session will be automatically saved when you close it.');
    await new Promise(() => {});
}

launchWithPersistentContext().catch(console.error);
```

### 2. search-and-capture.js - Automated Gemini Search
```javascript
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs').promises;

async function searchAndCapture() {
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
    await page.goto('https://gemini.google.com', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);

    // Find input field
    const selectors = [
        'textarea[placeholder*="Enter a prompt"]',
        'div[contenteditable="true"]',
        '[role="textbox"]'
    ];

    for (const selector of selectors) {
        try {
            await page.waitForSelector(selector, { timeout: 3000 });
            await page.click(selector);
            await page.waitForTimeout(500);

            const searchQuery = "Tell me about the game Lemmings and the concept of being stuck with the same tool";
            await page.type(selector, searchQuery, { delay: 50 });
            await page.keyboard.press('Enter');

            console.log('✅ Search submitted! Waiting for response...');
            break;
        } catch {}
    }

    // Wait for response
    await page.waitForTimeout(5000);
    await page.waitForSelector('[data-message-author="assistant"], [class*="response"]', { timeout: 10000 });
    await page.waitForTimeout(5000);

    // Capture URL
    const currentUrl = page.url();
    const urlData = {
        url: currentUrl,
        query: searchQuery,
        timestamp: new Date().toISOString()
    };

    await fs.writeFile(
        path.join(__dirname, 'captured-url.json'),
        JSON.stringify(urlData, null, 2)
    );

    console.log('📌 Captured URL:', currentUrl);
    await page.waitForTimeout(3000);
    await context.close();
}

searchAndCapture().catch(console.error);
```

### 3. deep-research-search.js - Advanced Deep Research Automation
```javascript
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs').promises;

async function deepResearchSearch() {
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
    await page.goto('https://gemini.google.com', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);

    // Find and click input
    const inputSelector = 'div[contenteditable="true"]';
    await page.waitForSelector(inputSelector, { timeout: 3000 });
    await page.click(inputSelector);

    // Click Tools button
    console.log('🛠️ Looking for tools button...');
    const toolsButton = await page.$('button:has-text("Tools")');
    if (toolsButton) {
        await toolsButton.click();
        console.log('✅ Clicked tools button');
        await page.waitForTimeout(1000);
    }

    // Select Deep Research
    console.log('🔬 Selecting Deep Research...');
    try {
        await page.click('text="Deep Research"');
        console.log('✅ Selected Deep Research mode');
        await page.waitForTimeout(1000);
    } catch {}

    // Type search query
    const searchQuery = "Deep research for Lemmings the game and being stuck with the same tool";
    await page.click(inputSelector);
    await page.keyboard.press('Control+A');
    await page.keyboard.press('Backspace');
    await page.type(inputSelector, searchQuery, { delay: 50 });
    await page.keyboard.press('Enter');

    console.log('⏳ Waiting for Deep Research response...');
    await page.waitForTimeout(10000);

    // Wait for response
    await page.waitForSelector('[data-message-author="assistant"]', { timeout: 30000 });
    await page.waitForTimeout(8000);

    // Capture URL
    const currentUrl = page.url();
    const urlData = {
        url: currentUrl,
        query: searchQuery,
        mode: "Deep Research",
        timestamp: new Date().toISOString()
    };

    await fs.writeFile(
        path.join(__dirname, 'deep-research-url.json'),
        JSON.stringify(urlData, null, 2)
    );

    console.log('✅ Deep Research URL captured:', currentUrl);
    await page.waitForTimeout(3000);
    await context.close();
}

deepResearchSearch().catch(console.error);
```

## Key Selectors for Gemini

```javascript
// Input field selectors (in order of reliability)
const inputSelectors = [
    'textarea[placeholder*="Enter a prompt"]',
    'textarea[placeholder*="Message"]',
    'div[contenteditable="true"]',        // Most common
    'textarea.ql-editor',
    '[role="textbox"]'
];

// Tools and options
const toolsSelectors = [
    'button:has-text("Tools")',           // Working selector
    'button[aria-label*="tools"]',
    '[role="button"]:has-text("Tools")'
];

// Deep Research option
const deepResearchSelectors = [
    'text="Deep Research"',               // Working selector
    '[aria-label*="Deep Research"]',
    '[role="option"]:has-text("Deep Research")'
];

// Response detection
const responseSelectors = [
    '[data-message-author="assistant"]',  // Primary
    '[class*="response"]',
    '[class*="output"]'
];
```

## Usage Instructions

### Initial Setup
1. Install dependencies: `npm install`
2. Install browsers: `npx playwright install chrome`

### First Time - Save Login Session
```bash
node working-chrome-persistent.js
# Log into Google/GitHub/etc manually
# Close browser when done - session is saved
```

### Run Automated Searches
```bash
# Regular search
node search-and-capture.js

# Deep Research search
node deep-research-search.js
```

### Check Captured URLs
```bash
# View regular search results
cat captured-url.json

# View Deep Research results
cat deep-research-url.json
```

## Chrome Profiles Available
- Default (Person 1)
- Profile 1-3 (Your Chrome)
- Profile 4 (leasesplit.com) - Used for testing

## Critical Success Factors
1. **Must use `channel: 'chrome'`** - Real Chrome bypasses detection
2. **Disable automation flags** - Prevents "insecure browser" blocking
3. **Persistent context directory** - Maintains login across sessions
4. **Custom user agent** - Appears as regular browser
5. **Proper wait strategies** - Allow time for responses

## Captured URLs (Examples)
- Regular: `https://gemini.google.com/app/17fe7ed77fea6b90`
- Regular 2: `https://gemini.google.com/app/dc86f194098ec828`
- Deep Research: `https://gemini.google.com/app/0ac21a822e854317`

## Limitations & Notes
- **Cannot use official Playwright MCP** - It doesn't support required flags
- **Runs as standalone scripts** - Not through MCP protocol
- **Claude controls via bash** - Not real-time control
- **Firefox alternative available** - But Chrome works better with anti-detection

## Troubleshooting
- If "browser not secure" appears: Check that `channel: 'chrome'` is set
- If login doesn't persist: Ensure `chrome-persistent-profile` directory exists
- If selectors fail: Check browser console for updated element structure

## Testing Date
Successfully tested and working: September 20, 2025

---
*This setup bypasses Google's automation detection and enables persistent browser sessions for automated testing and web scraping.*