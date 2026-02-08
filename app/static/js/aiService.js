// aiService.js - Centralized AI API Service for SheSafe

class AIService {
    constructor(keys = {}) {
        this.providers = [
            {
                name: "OpenRouter",
                apiKey: keys.openRouter || "",
                apiUrl: "https://openrouter.ai/api/v1/chat/completions",
                models: [
                    "google/gemma-2-9b-it:free",
                    "meta-llama/llama-3.2-3b-instruct:free",
                    "microsoft/phi-3-mini-128k-instruct:free",
                    "google/gemini-2.0-flash-exp:free"
                ]
            },
            {
                name: "NVIDIA NIM",
                apiKey: keys.nvidia || "",
                apiUrl: "https://integrate.api.nvidia.com/v1/chat/completions",
                models: [
                    "meta/llama-3.1-405b-instruct",
                    "mistralai/mistral-large-2-instruct",
                    "nvidia/llama-3.1-nemotron-70b-instruct",
                    "google/gemma-2-27b-it",
                    "nvidia/nemotron-mini-4b-instruct"
                ]
            },
            {
                name: "Ollama Cloud",
                apiKey: keys.siliconFlow || "",
                apiUrl: "https://api.siliconflow.cn/v1/chat/completions",
                models: [
                    "deepseek-ai/DeepSeek-V3",
                    "deepseek-ai/DeepSeek-R1",
                    "THUDM/glm-4-9b-chat",
                    "Qwen/Qwen2.5-7B-Instruct",
                    "internlm/internlm2_5-20b-chat"
                ]
            }
        ];
        this.currentProviderIndex = 0;
        this.currentModelIndex = 0;
    }


    cleanReasoningOutput(text) {
        if (!text) return text;

        let cleanedText = text;

        // 1. Specific Personality Motivation Fishing (Short responses only)
        if (cleanedText.length < 1000) {
            const signatureRegex = /(Sharmila[\s\S]*from\s+(Dibakar|Cristiano Ronaldo|Virat Kohli|Park Bo Gum|Karan Aujla))/i;
            const match = cleanedText.match(signatureRegex);
            if (match && match[1]) {
                return match[1].trim();
            }
        }

        // 2. Business Plan / Long Response Cleaning
        const thinkingHeaders = [
            /^(Thinking|Reasoning|Okay|First|Let me|The user|Based on|I need|I will|Parsing).*?[\n\r]/mi,
            /^(Key instructions|Interpretation|Original note|Draft|Start with|State her symptoms).*?[\n\r]/mi
        ];

        let lines = cleanedText.split('\n');
        let strippedAny = false;
        while (lines.length > 0) {
            const firstLine = lines[0].trim();
            if (!firstLine || thinkingHeaders.some(regex => regex.test(firstLine))) {
                lines.shift();
                strippedAny = true;
            } else {
                break;
            }
        }

        if (strippedAny) {
            cleanedText = lines.join('\n').trim();
        }

        return cleanedText || text;
    }



    async callGemini(prompt, systemPrompt) {
        const apiKey = "AIzaSyA8nrVFVmlpFSp-AJXWH2an7jau6YU9e2g";
        const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`;

        // Construct request body for Google's API
        const requestBody = {
            contents: [{
                role: "user",
                parts: [{ text: prompt }]
            }],
            generationConfig: {
                maxOutputTokens: 1000,
                temperature: 0.5
            }
        };

        if (systemPrompt) {
            requestBody.systemInstruction = {
                parts: [{ text: systemPrompt }]
            };
        }

        try {
            console.log("[Gemini] Trying: gemini-1.5-flash");
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                console.warn(`[Fallback] Gemini -> HTTP ${response.status}`);
                return null;
            }

            const data = await response.json();
            const responseText = data.candidates?.[0]?.content?.parts?.[0]?.text;

            if (!responseText) {
                console.warn("[Fallback] Gemini -> Empty Response");
                return null;
            }

            console.log("[Success] Used Gemini Flash");
            return this.cleanReasoningOutput(responseText);

        } catch (error) {
            console.error("[Network Error] Gemini:", error.message);
            return null;
        }
    }

    async callAI(prompt, maxTokens = 1000, systemPrompt = null) {
        // 1. Try Gemini First (Hardcoded Priority)
        const geminiResponse = await this.callGemini(prompt, systemPrompt);
        if (geminiResponse) return geminiResponse;

        // 2. Fallback to existing providers
        const startProviderIndex = this.currentProviderIndex;

        for (let p = 0; p < this.providers.length; p++) {
            const providerIndex = (startProviderIndex + p) % this.providers.length;
            const provider = this.providers[providerIndex];

            // Inner loop tries models in this provider
            const startModelIndex = (p === 0) ? this.currentModelIndex : 0;

            for (let m = 0; m < provider.models.length; m++) {
                const modelIndex = (startModelIndex + m) % provider.models.length;
                const model = provider.models[modelIndex];

                try {
                    console.log(`[${provider.name}] Trying: ${model}`);

                    const response = await fetch(provider.apiUrl, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${provider.apiKey}`,
                            'HTTP-Referer': window.location.origin,
                            'X-Title': 'SheSafe'
                        },
                        body: JSON.stringify({
                            model: model,
                            messages: systemPrompt ?
                                [{ role: "system", content: systemPrompt }, { role: "user", content: prompt }] :
                                [{ role: "user", content: prompt }],
                            max_tokens: maxTokens,
                            temperature: 0.5
                        })
                    });

                    if (!response.ok) {
                        console.warn(`[Fallback] ${provider.name} ${model} -> HTTP ${response.status}`);
                        continue;
                    }

                    const data = await response.json();
                    let responseText = data.choices?.[0]?.message?.content || data.choices?.[0]?.message?.reasoning;

                    if (!responseText) {
                        console.warn(`[Fallback] ${provider.name} ${model} -> Empty Response`);
                        continue;
                    }

                    // Success! Update indices for next time and return
                    this.currentProviderIndex = providerIndex;
                    this.currentModelIndex = modelIndex;
                    console.log(`[Success] Used ${provider.name} - ${model}`);
                    return this.cleanReasoningOutput(responseText);

                } catch (error) {
                    console.error(`[Network Error] ${provider.name} - ${model}:`, error.message);

                    if (error instanceof TypeError) {
                        console.warn(`[Critical] Provider ${provider.name} appears blocked or inaccessible. Skipping entire provider.`);
                        break;
                    }
                    continue;
                }
            }
        }

        return "AI Error: All providers (Gemini, OpenRouter, NVIDIA, SiliconFlow) failed to respond. This may be due to browser security settings or network issues.";
    }
}

export default AIService;
