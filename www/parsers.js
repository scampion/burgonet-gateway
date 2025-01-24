// Model-specific message format translators and response parsers
const parsers = {
    // OpenAI-compatible format (used by many providers)
    openai: {
        formatMessages: (messages) => {
            return messages.map(msg => ({
                role: msg.role,
                content: msg.content
            }));
        },
        parseResponse: (response) => {
            if (!response.choices || !response.choices[0]?.message?.content) {
                throw new Error('Invalid OpenAI response format');
            }
            return [{
                role: 'assistant',
                content: response.choices[0].message.content
            }];
        }
    },

    // Ollama format
    ollama: {
        formatMessages: (messages) => {
            // Ollama uses the same format as OpenAI
            return messages.map(msg => ({
                role: msg.role,
                content: msg.content
            }));
        },
        parseResponse: (response) => {
            if (!response.message || !response.message.content) {
                throw new Error('Invalid Ollama response format');
            }
            return [{
                role: 'assistant',
                content: response.message.content
            }];
        }
    },

    // Deepseek format
    deepseek: {
        formatMessages: (messages) => {
            return messages.map(msg => ({
                role: msg.role,
                content: msg.content
            }));
        },
        parseResponse: (response) => {
            if (!response.choices || !response.choices[0]?.message?.content) {
                throw new Error('Invalid Deepseek response format');
            }
            return [{
                role: 'assistant',
                content: response.choices[0].message.content
            }];
        }
    },

    // Llama.cpp format
    llamacpp: {
        formatMessages: (messages) => {
            return messages.map(msg => ({
                role: msg.role,
                content: msg.content
            }));
        },
        parseResponse: (response) => {
            if (!response.content) {
                throw new Error('Invalid Llama.cpp response format');
            }
            return [{
                role: 'assistant',
                content: response.content
            }];
        }
    },

    // Echo format (for testing)
    echo: {
        formatMessages: (messages) => {
            return messages;
        },
        parseResponse: (response) => {
            return [{
                role: 'assistant',
                content: response.content || 'Echo response'
            }];
        }
    }
};

// Get the appropriate parser based on model name
function getParser(modelName) {
    // Default to openai format if model not recognized
    return parsers[modelName] || parsers.openai;
}

export { getParser };
