#!/usr/bin/env node

require('dotenv').config();
const { improvePromptWithCriticalThinking } = require('./improve_message');
const readline = require('readline');

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

async function processPrompt(prompt) {
    try {
        const improved = await improvePromptWithCriticalThinking(prompt);
        console.log('\n' + '='.repeat(50));
        console.log('IMPROVED PROMPT:');
        console.log('='.repeat(50));
        console.log(improved);
        console.log('='.repeat(50) + '\n');
    } catch (error) {
        console.error('Error:', error.message);
    }
}

async function main() {
    const args = process.argv.slice(2);

    if (args.length > 0) {
        const prompt = args.join(' ');
        await processPrompt(prompt);
        process.exit(0);
    }

    console.log('Critical Thinking Prompt Enhancer');
    console.log('Type your prompt and press Enter (or type "exit" to quit)\n');

    const askPrompt = () => {
        rl.question('Enter prompt: ', async (input) => {
            if (input.toLowerCase() === 'exit') {
                rl.close();
                process.exit(0);
            }

            if (input.trim()) {
                await processPrompt(input);
            }

            askPrompt();
        });
    };

    askPrompt();
}

main();