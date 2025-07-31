class DebuggerUI {
    constructor() {
        this.container = document.getElementById('debug-container');
        this.setupUI();
    }

    setupUI() {
        this.container.innerHTML = `
            <div class="debug-panel">
                <h3>Debug Assistant</h3>
                <div class="debug-frames"></div>
                <button id="analyze-btn">Analyze Error</button>
            </div>
        `;
        
        document.getElementById('analyze-btn').addEventListener('click', () => this.analyzeError());
    }

    async analyzeError() {
        const code = document.getElementById('code-editor').value;
        const error = document.getElementById('error-output').value;
        
        const response = await fetch('/debug', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content: "debug_request",
                context: { code, error }
            })
        });
        
        const result = await response.json();
        this.displayResults(result);
    }

    displayResults(debugData) {
        const framesContainer = document.querySelector('.debug-frames');
        framesContainer.innerHTML = debugData.metadata.frames.map(frame => `
            <div class="debug-frame">
                <h4>${frame.file}:${frame.line}</h4>
                <pre>${frame.context}</pre>
                <div class="variables">${this.formatVariables(frame.variables)}</div>
                ${this.formatSuggestions(debugData.metadata.suggestions[frame.line] || [])}
            </div>
        `).join('');
    }

    formatVariables(vars) {
        return Object.entries(vars).map(([k, v]) => 
            `<span class="var">${k}=${v}</span>`
        ).join(' ');
    }

    formatSuggestions(suggestions) {
        if (!suggestions.length) return '';
        return `
            <div class="suggestions">
                <h5>Suggestions:</h5>
                <ul>${suggestions.map(s => `<li>${s}</li>`).join('')}</ul>
            </div>
        `;
    }
}