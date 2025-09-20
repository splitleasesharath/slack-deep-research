const fs = require('fs').promises;
const path = require('path');

async function checkChromeProfiles() {
    const chromeDataPath = path.join('C:', 'Users', 'Split Lease', 'AppData', 'Local', 'Google', 'Chrome', 'User Data');

    console.log('Checking Chrome profiles at:', chromeDataPath);
    console.log('=====================================\n');

    try {
        // Check if Chrome User Data directory exists
        await fs.access(chromeDataPath);

        // Read all directories
        const items = await fs.readdir(chromeDataPath, { withFileTypes: true });

        // Filter for profile directories
        const profiles = items.filter(item =>
            item.isDirectory() &&
            (item.name === 'Default' || item.name.startsWith('Profile'))
        );

        console.log(`Found ${profiles.length} Chrome profile(s):\n`);

        for (const profile of profiles) {
            const profilePath = path.join(chromeDataPath, profile.name);
            console.log(`📁 ${profile.name}`);
            console.log(`   Path: ${profilePath}`);

            // Check for Preferences file to see if profile is valid
            try {
                const prefsPath = path.join(profilePath, 'Preferences');
                await fs.access(prefsPath);

                // Read preferences to get profile name
                const prefs = JSON.parse(await fs.readFile(prefsPath, 'utf8'));
                const profileName = prefs.profile?.name || 'Unnamed';
                console.log(`   Name: ${profileName}`);
            } catch (e) {
                console.log(`   Status: May be incomplete`);
            }
            console.log('');
        }

        console.log('\n📌 To use a profile with Playwright MCP:');
        console.log('1. Choose the profile you want to use (usually "Default" for main profile)');
        console.log('2. Use the full path in your Playwright configuration');
        console.log(`   Example: "${chromeDataPath}"`);

    } catch (error) {
        console.error('Error accessing Chrome profiles:', error.message);
        console.log('\nMake sure Chrome is installed and you have at least opened it once.');
    }
}

checkChromeProfiles();