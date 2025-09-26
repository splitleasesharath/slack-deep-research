const { improveMessage } = require('./improve_message');

async function runExamples() {
    console.log('Message Improvement Examples\n' + '='.repeat(40));

    const examples = [
        {
            message: "hey can u send me the report",
            improvements: ["Make it more professional", "Add politeness", "Improve grammar"]
        },
        {
            message: "The meeting is tomorrow",
            improvements: ["Add more details", "Make it sound urgent", "Include a call to action"]
        },
        {
            message: "Thanks for your help",
            improvements: ["Make it more heartfelt", "Add specific appreciation", "Professional tone"]
        }
    ];

    for (const example of examples) {
        console.log(`\nOriginal: "${example.message}"`);
        console.log(`Improvements: ${example.improvements.join(', ')}`);

        try {
            const improved = await improveMessage(example.message, example.improvements);
            console.log(`Improved: "${improved}"`);
        } catch (error) {
            console.log(`Error: ${error.message}`);
        }
        console.log('-'.repeat(40));
    }
}

if (require.main === module) {
    runExamples();
}