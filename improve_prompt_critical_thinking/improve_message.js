require('dotenv').config();
const OpenAI = require('openai');

const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY
});

const CRITICAL_THINKING_SYSTEM_PROMPT = `You are an expert prompt engineer who transforms basic user questions into comprehensive critical thinking prompts. Your role is to:

1. PRESERVE the original intent and core question from the user (often from non-native English speakers)
2. ENHANCE the prompt to invoke deep critical thinking and analysis
3. OUTPUT only the improved prompt - no explanations or meta-commentary

Transform the user's prompt by incorporating these critical thinking elements naturally into the question:

1. Devil's Advocate - Include request for counterarguments
2. Missing Pieces - Ask for assumptions and missing perspectives
3. Roleplay Perspectives - Request analysis from multiple viewpoints (policymaker, entrepreneur, scientist)
4. Sub-Questions - Break down into component questions
5. Bias Check - Include request to identify potential biases
6. Timeline Builder - Ask for temporal/causal analysis when relevant
7. Falsifiability - Request evidence that could disprove claims
8. So-What Chain - Ask for 2nd and 3rd order consequences
9. Concept Map - Request structural relationships between ideas
10. Opposite Day - Ask what if the opposite were true

The improved prompt should:
- Start with the clarified main question
- Naturally weave in all of the above elements
- Be clear and actionable
- Maintain focus on getting a comprehensive, thoughtful response
- Be formatted as a single, flowing prompt (not a numbered list)

Remember: Output ONLY the improved prompt text, nothing else.`;

async function improvePromptWithCriticalThinking(originalPrompt) {
    try {
        const response = await openai.chat.completions.create({
            model: "gpt-5",
            messages: [
                {
                    role: "system",
                    content: CRITICAL_THINKING_SYSTEM_PROMPT
                },
                {
                    role: "user",
                    content: originalPrompt
                }
            ],
            temperature: 0.7,
            max_completion_tokens: 1000
        });

        return response.choices[0].message.content.trim();
    } catch (error) {
        console.error('Error calling OpenAI API:', error.message);
        throw error;
    }
}

async function improveMessage(originalMessage, improvements) {
    try {
        const prompt = `Please improve the following message based on the specified improvements.

Original Message:
${originalMessage}

Improvements to apply:
${Array.isArray(improvements) ? improvements.join('\n') : improvements}

Return ONLY the improved message, without any explanations or additional text.`;

        const response = await openai.chat.completions.create({
            model: "gpt-5",
            messages: [
                {
                    role: "system",
                    content: "You are a professional message editor. Return only the improved message without any explanations."
                },
                {
                    role: "user",
                    content: prompt
                }
            ],
            temperature: 0.7,
            max_completion_tokens: 1000
        });

        return response.choices[0].message.content.trim();
    } catch (error) {
        console.error('Error calling OpenAI API:', error.message);
        throw error;
    }
}

async function main() {
    const args = process.argv.slice(2);

    if (args.length < 1) {
        console.log('Usage for critical thinking mode:');
        console.log('  node improve_message.js "your prompt"');
        console.log('Example: node improve_message.js "how AI works"');
        console.log('\nUsage for custom improvements:');
        console.log('  node improve_message.js --custom "message" "improvement1,improvement2,..."');
        process.exit(1);
    }

    try {
        if (args[0] === '--custom' && args.length >= 3) {
            const message = args[1];
            const improvements = args[2].split(',').map(imp => imp.trim());
            const improvedMessage = await improveMessage(message, improvements);
            console.log(improvedMessage);
        } else {
            const originalPrompt = args.join(' ');
            const improvedPrompt = await improvePromptWithCriticalThinking(originalPrompt);
            console.log(improvedPrompt);
        }
    } catch (error) {
        console.error('Failed to improve prompt:', error.message);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}

module.exports = { improveMessage, improvePromptWithCriticalThinking };