# Report Retriever

This script retrieves complete reports from URLs using an existing Chrome session with saved login credentials.

## Features

- Connects to existing Chrome session from `playwright-mcp-state` directory
- Retrieves complete report content from any URL
- Saves reports with timestamps in the `reports` directory
- Takes screenshots for reference
- Saves metadata about each retrieval

## Installation

```bash
npm install
```

## Usage

Run the script with a URL as parameter:

```bash
node retrieve_report.js <URL>
```

### Example:

```bash
node retrieve_report.js https://gemini.google.com/app/abc123def456
```

## Output

The script creates a `reports` directory with:

1. **Report text file**: `report_<domain>_<timestamp>.txt`
   - Contains the extracted text content from the page

2. **Metadata file**: `metadata_<timestamp>.json`
   - URL, timestamp, filename, content length, extraction method

3. **Screenshot**: `screenshot_<timestamp>.png`
   - Full page screenshot for visual reference

## Notes

- The script uses the existing Chrome session from the `playwright-mcp-state` directory
- Make sure you're logged into the service in that Chrome session before running this script
- The script will automatically detect and extract report content
- If specific report elements aren't found, it will extract the entire page content

## Troubleshooting

If the script can't connect to Chrome:
1. Make sure the Chrome session exists in `C:\Users\Split Lease\Documents\chatgpt-deep-research\playwright-mcp-state\chrome-persistent-profile`
2. Ensure you've previously logged into the service using the persistent Chrome session

If reports aren't being extracted properly:
- The script may need selector adjustments for different platforms
- Check the screenshot to see what was visible on the page