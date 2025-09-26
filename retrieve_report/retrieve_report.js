const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs').promises;

async function retrieveReport(url) {
    console.log('🔧 Connecting to existing Chrome session...\n');

    // Use the same persistent context from the other project
    const userDataDir = path.join('C:', 'Users', 'Split Lease', 'Documents', 'gemini-deep-research', 'playwright-mcp-state', 'chrome-persistent-profile');

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

        // Try to find the specific Deep Research report container
        const selectors = [
            // Primary selector: Look for the markdown container with the specific ID
            '#extended-response-markdown-content',
            // Fallback selector 1: Look for markdown main panel class
            '.markdown.markdown-main-panel',
            // Fallback selector 2: Look for message content with markdown
            'message-content .markdown',
            // Fallback selector 3: Look for any markdown container in the response
            '.response-container-content .markdown',
            // Last resort: Look for any div with markdown class
            'div.markdown'
        ];

        let extractedContent = '';
        let selectorUsed = '';

        // Try each selector in order until we find content
        for (const selector of selectors) {
            try {
                const element = await page.$(selector);
                if (element) {
                    const content = await page.evaluate(el => {
                        // Get text content, preserving structure
                        return el.innerText || el.textContent || '';
                    }, element);

                    if (content && content.length > 500) { // Ensure we have substantial content
                        extractedContent = content;
                        selectorUsed = selector;
                        break;
                    }
                }
            } catch (e) {
                // Continue to next selector
                console.log(`  Selector "${selector}" didn't work, trying next...`);
            }
        }

        // If specific selectors didn't work, fall back to broader extraction
        if (!extractedContent) {
            console.log('⚠️ Specific selectors failed, attempting pattern-based extraction...');

            // Try to get content from the response container by pattern matching
            extractedContent = await page.evaluate(() => {
                // Look for any element that contains the deep research report
                // Identify by looking for substantial text content with headings
                const containers = document.querySelectorAll('[class*="response"], [class*="message"], [class*="markdown"]');

                for (const container of containers) {
                    const text = container.innerText || container.textContent || '';
                    // Check if this looks like a research report (has headings and substantial content)
                    if (text.length > 1000 &&
                        (text.includes('Executive Summary') ||
                         text.includes('Section') ||
                         text.includes('Research') ||
                         text.includes('## ') ||
                         text.includes('### '))) {
                        return text;
                    }
                }

                return ''; // Return empty if pattern matching fails
            });

            if (extractedContent) {
                selectorUsed = 'pattern-based-extraction';
            }
        }

        // Ultimate fallback: Extract entire page text if all targeted methods fail
        if (!extractedContent) {
            console.log('⚠️ All targeted extraction methods failed.');
            console.log('📄 Falling back to extracting entire page text...');

            extractedContent = await page.evaluate(() => {
                return document.body.innerText || document.body.textContent || '';
            });

            selectorUsed = 'full-page-fallback';

            if (extractedContent) {
                console.log('✅ Successfully extracted full page content as fallback');
            }
        }

        reportContent = extractedContent;

        if (reportContent && reportContent.length > 1000) {
            console.log(`✅ Extracted Deep Research report using selector: "${selectorUsed}"`);
            console.log(`   Report length: ${reportContent.length} characters`);

            // Log first 200 characters as preview
            const preview = reportContent.substring(0, 200).replace(/\n/g, ' ');
            console.log(`   Preview: "${preview}..."`);
        } else if (reportContent) {
            console.log(`⚠️ Report content seems too short (${reportContent.length} characters)`);
            console.log(`   Selector used: "${selectorUsed}"`);
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