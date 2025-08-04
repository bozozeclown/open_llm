// vscode-extension/src/extension.ts
import * as vscode from 'vscode';
import * as axios from 'axios';

interface CodeSuggestion {
    content: string;
    confidence: number;
    explanation: string;
    line_range: [number, number];
}

interface RefactoringSuggestion {
    type: string;
    title: string;
    description: string;
    original_code: string;
    suggested_code: string;
    confidence: number;
}

export function activate(context: vscode.ExtensionContext) {
    console.log('Open LLM Code Assistant is now active!');

    // Register commands
    const disposable = vscode.commands.registerCommand('open-llm.getCodeSuggestion', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor');
            return;
        }

        const selection = editor.selection;
        const text = editor.document.getText(selection);
        
        try {
            const suggestion = await getCodeSuggestion(text);
            if (suggestion) {
                showSuggestion(editor, suggestion);
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to get suggestion: ${error.message}`);
        }
    });

    const refactoringDisposable = vscode.commands.registerCommand('open-llm.analyzeRefactoring', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor');
            return;
        }

        const document = editor.document;
        const text = document.getText();
        const language = document.languageId;
        
        try {
            const suggestions = await getRefactoringSuggestions(text, language);
            if (suggestions.length > 0) {
                showRefactoringSuggestions(editor, suggestions);
            } else {
                vscode.window.showInformationMessage('No refactoring suggestions found.');
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to analyze refactoring: ${error.message}`);
        }
    });

    const imageAnalysisDisposable = vscode.commands.registerCommand('open-llm.analyzeImage', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor');
            return;
        }

        // Let user select an image file
        const options: vscode.OpenDialogOptions = {
            canSelectMany: false,
            openLabel: 'Select Image',
            filters: {
                'Images': ['png', 'jpg', 'jpeg', 'gif', 'bmp']
            }
        };

        const fileUri = await vscode.window.showOpenDialog(options);
        if (fileUri && fileUri[0]) {
            try {
                const analysis = await analyzeImage(fileUri[0].fsPath);
                if (analysis.success) {
                    showImageAnalysis(editor, analysis);
                } else {
                    vscode.window.showErrorMessage(`Image analysis failed: ${analysis.error}`);
                }
            } catch (error) {
                vscode.window.showErrorMessage(`Failed to analyze image: ${error.message}`);
            }
        }
    });

    context.subscriptions.push(disposable, refactoringDisposable, imageAnalysisDisposable);
}

async function getCodeSuggestion(code: string): Promise<CodeSuggestion | null> {
    const config = vscode.workspace.getConfiguration('open-llm');
    const apiUrl = config.get('apiUrl', 'http://localhost:8000');
    
    const response = await axios.post(`${apiUrl}/query`, {
        content: `Complete this code: ${code}`,
        metadata: {
            language: 'python',
            context: { code }
        }
    });

    return {
        content: response.data.content,
        confidence: 0.8,
        explanation: "AI-generated code suggestion",
        line_range: [0, 0]
    };
}

async function getRefactoringSuggestions(code: string, language: string): Promise<RefactoringSuggestion[]> {
    const config = vscode.workspace.getConfiguration('open-llm');
    const apiUrl = config.get('apiUrl', 'http://localhost:8000');
    
    const response = await axios.post(`${apiUrl}/refactor/analyze`, {
        code,
        language
    });

    return response.data.suggestions;
}

async function analyzeImage(imagePath: string): Promise<any> {
    const fs = require('fs');
    const config = vscode.workspace.getConfiguration('open-llm');
    const apiUrl = config.get('apiUrl', 'http://localhost:8000');
    
    const imageBuffer = fs.readFileSync(imagePath);
    const base64Image = imageBuffer.toString('base64');
    
    const response = await axios.post(`${apiUrl}/multimodal/analyze`, {
        image_data: base64Image
    });

    return response.data;
}

function showSuggestion(editor: vscode.TextEditor, suggestion: CodeSuggestion) {
    const range = new vscode.Range(
        editor.selection.start.line,
        editor.selection.start.character,
        editor.selection.end.line,
        editor.selection.end.character
    );

    vscode.window.showTextDocument(editor.document);
    editor.edit(editBuilder => {
        editBuilder.replace(range, suggestion.content);
    });

    vscode.window.showInformationMessage(`Applied suggestion with ${Math.round(suggestion.confidence * 100)}% confidence`);
}

function showRefactoringSuggestions(editor: vscode.TextEditor, suggestions: RefactoringSuggestion[]) {
    const items = suggestions.map(s => ({
        label: s.title,
        description: s.description,
        detail: `Confidence: ${Math.round(s.confidence * 100)}%`,
        suggestion: s
    }));

    vscode.window.showQuickPick(items, {
        placeHolder: 'Select a refactoring suggestion to apply'
    }).then(selected => {
        if (selected) {
            applyRefactoring(editor, selected.suggestion);
        }
    });
}

function applyRefactoring(editor: vscode.TextEditor, suggestion: RefactoringSuggestion) {
    // Find the original code in the document
    const document = editor.document;
    const text = document.getText();
    const startIndex = text.indexOf(suggestion.original_code);
    
    if (startIndex !== -1) {
        const endIndex = startIndex + suggestion.original_code.length;
        const range = new vscode.Range(
            document.positionAt(startIndex),
            document.positionAt(endIndex)
        );

        editor.edit(editBuilder => {
            editBuilder.replace(range, suggestion.suggested_code);
        });

        vscode.window.showInformationMessage(`Applied refactoring: ${suggestion.title}`);
    } else {
        vscode.window.showErrorMessage('Could not find the original code to replace');
    }
}

function showImageAnalysis(editor: vscode.TextEditor, analysis: any) {
    if (analysis.structured_code) {
        const position = editor.selection.active;
        
        editor.edit(editBuilder => {
            editBuilder.insert(position, `\n# Code extracted from image\n${analysis.structured_code}\n`);
        });

        vscode.window.showInformationMessage(`Extracted ${analysis.language} code from image with ${Math.round(analysis.confidence * 100)}% confidence`);
    }
}

export function deactivate() {}