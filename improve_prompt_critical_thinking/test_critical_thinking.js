const { improvePromptWithCriticalThinking } = require('./improve_message');

async function runCriticalThinkingExamples() {
    console.log('Critical Thinking Prompt Enhancement Examples');
    console.log('='.repeat(60) + '\n');

    const examples = [
        "how AI works",
        "should we use nuclear energy",
        "what is best programming language",
        "how to make website faster",
        "is remote work better than office",
        "explain blockchain technology",
        "how climate change affects economy"
    ];

    for (const original of examples) {
        console.log(`ORIGINAL: "${original}"`);
        console.log('-'.repeat(40));

        try {
            const improved = await improvePromptWithCriticalThinking(original);
            console.log('ENHANCED WITH CRITICAL THINKING:');
            console.log(improved);
        } catch (error) {
            console.log(`Error: ${error.message}`);
        }

        console.log('\n' + '='.repeat(60) + '\n');
    }
}

if (require.main === module) {
    console.log('NOTE: Make sure you have set your OPENAI_API_KEY in .env file\n');
    runCriticalThinkingExamples().catch(console.error);
}