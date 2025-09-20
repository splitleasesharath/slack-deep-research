const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs').promises;

async function retrieveReport(url) {
    console.log('🔧 Connecting to existing Chrome session...\n');

    // Use the same persistent context from the other project
    const userDataDir = path.join('C:', 'Users', 'Split Lease', 'Documents', 'chatgpt-deep-research', 'playwright-mcp-state', 'chrome-persistent-profile');

    console.log('📂 Using persistent profile:', userDataDir);

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

    console.log('✅ Connected to Chrome with persistent session\n');

    const page = await context.newPage();

    console.log(`📍 Navigating to: ${url}`);
    await page.goto(url, { waitUntil: 'domcontentloaded' });

    console.log('⏳ Waiting for page to load completely...');
    await page.waitForTimeout(5000);

    console.log('\n🔍 Looking for right-side Deep Research report...');

    // Wait for the report to be fully loaded
    let reportContent = '';

    try {
        // Wait for content to load
        await page.waitForTimeout(5000);

        // Extract the ENTIRE page content
        reportContent = await page.evaluate(() => {
            // Simply return all text content from the page
            return document.body.innerText || '';
        });

        if (reportContent && reportContent.length > 1000) {
            console.log(`✅ Extracted Deep Research report (${reportContent.length} characters)`);
        } else if (reportContent) {
            console.log(`⚠️ Report content seems too short (${reportContent.length} characters)`);
        } else {
            console.log('❌ Could not find Deep Research report content');
            reportContent = 'Unable to extract report content. Please check the page manually.';
        }
    } catch (error) {
        console.log('❌ Error during extraction:', error.message);
        reportContent = 'Error extracting report: ' + error.message;
    }

    // Generate timestamp for filename
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').replace('T', '_').split('Z')[0];
    const domain = new URL(url).hostname.replace(/\./g, '_');
    const filename = `report_${domain}_${timestamp}.txt`;
    const filepath = path.join(__dirname, 'reports', filename);

    // Create reports directory if it doesn't exist
    await fs.mkdir(path.join(__dirname, 'reports'), { recursive: true });

    // Save the report
    await fs.writeFile(filepath, reportContent);

    console.log(`\n✅ Report saved to: ${filepath}`);
    console.log(`📊 Report size: ${(reportContent.length / 1024).toFixed(2)} KB`);

    // Also save metadata
    const metadata = {
        url: url,
        timestamp: new Date().toISOString(),
        filename: filename,
        contentLength: reportContent.length,
        extraction_method: 'deep_research_report'
    };

    const metadataPath = path.join(__dirname, 'reports', `metadata_${timestamp}.json`);
    await fs.writeFile(metadataPath, JSON.stringify(metadata, null, 2));
    console.log(`📋 Metadata saved to: ${metadataPath}`);

    // Take a screenshot for reference
    const screenshotPath = path.join(__dirname, 'reports', `screenshot_${timestamp}.png`);
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`📸 Screenshot saved to: ${screenshotPath}`);

    console.log('\n✨ Report retrieval complete!');

    // Close the browser
    await context.close();
    return filepath;
}

// Check if URL is provided as command line argument
if (process.argv.length < 3) {
    console.log('❌ Error: Please provide a URL as an argument');
    console.log('Usage: node retrieve_report.js <URL>');
    console.log('Example: node retrieve_report.js https://gemini.google.com/app/abc123def456');
    process.exit(1);
}

const targetUrl = process.argv[2];

// Validate URL
try {
    new URL(targetUrl);
} catch (error) {
    console.log('❌ Error: Invalid URL provided');
    console.log('Please provide a valid URL starting with http:// or https://');
    process.exit(1);
}

// Run the retrieval
retrieveReport(targetUrl)
    .then(() => {
        console.log('\n🎉 Process completed successfully!');
        process.exit(0);
    })
    .catch((error) => {
        console.error('\n❌ Error occurred:', error);
        process.exit(1);
    });