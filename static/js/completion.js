class CompletionUI {
    constructor(editorElementId) {
        this.editor = document.getElementById(editorElementId);
        this.setupListeners();
    }

    setupListeners() {
        this.editor.addEventListener("keydown", async (e) => {
            if (e.key === "Tab" || (e.key === " " && e.ctrlKey)) {
                e.preventDefault();
                const completions = await this.fetchCompletions();
                this.showCompletions(completions);
            }
        });
    }

    async fetchCompletions() {
        const response = await fetch("/completion", {
            method: "POST",
            body: JSON.stringify({
                content: this.getCursorContext(),
                context: {
                    code: this.editor.value,
                    language: "python"  # Dynamic in real impl
                }
            })
        });
        return await response.json();
    }

    getCursorContext() {
        const cursorPos = this.editor.selectionStart;
        return this.editor.value.substring(
            Math.max(0, cursorPos - 50), 
            cursorPos
        );
    }

    showCompletions(completions) {
        // Render as dropdown or inline suggestions
        console.log("Suggestions:", completions);
    }
}