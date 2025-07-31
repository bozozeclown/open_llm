class SignatureUI {
    constructor(editorElementId) {
        this.editor = document.getElementById(editorElementId);
        this.tooltip = this._createTooltip();
        this._setupListeners();
    }

    _createTooltip() {
        const tooltip = document.createElement('div');
        tooltip.className = 'signature-tooltip';
        tooltip.style.display = 'none';
        document.body.appendChild(tooltip);
        return tooltip;
    }

    _setupListeners() {
        this.editor.addEventListener('mousemove', this._debounce(async (e) => {
            const pos = this._getCursorPosition(e);
            const signature = await this._fetchSignature(pos);
            if (signature) this._showSignature(signature);
        }, 300));
    }

    async _fetchSignature(cursorPos) {
        const response = await fetch('/signature', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                content: this.editor.value,
                context: {
                    code: this.editor.value,
                    language: 'python',
                    cursor_pos: cursorPos
                }
            })
        });
        return await response.json();
    }

    _showSignature(data) {
        if (!data.name) {
            this.tooltip.style.display = 'none';
            return;
        }

        const params = data.parameters.map((p, i) => 
            `<span class="${i === data.active_parameter ? 'active-param' : ''}">
                ${p.type ? `${p.type} ` : ''}${p.name}
            </span>`
        ).join(', ');

        this.tooltip.innerHTML = `
            <div class="signature-title">${data.name}(${params})</div>
        `;
        this._positionTooltip();
        this.tooltip.style.display = 'block';
    }

    _positionTooltip() {
        // Position near cursor (simplified)
        const rect = this.editor.getBoundingClientRect();
        this.tooltip.style.left = `${rect.left + 20}px`;
        this.tooltip.style.top = `${rect.top - 40}px`;
    }

    _debounce(func, delay) {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), delay);
        };
    }
}