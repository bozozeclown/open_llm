# core/multimodal/image_analyzer.py
import base64
import io
from typing import Dict, Any, List
from PIL import Image
import pytesseract
from transformers import pipeline, AutoImageProcessor, AutoModelForImageClassification
import re

class ImageAnalyzer:
    def __init__(self):
        self.ocr_reader = None
        self.code_classifier = None
        self.image_processor = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize ML models for image analysis"""
        try:
            # Initialize OCR
            self.ocr_reader = pytesseract
            
            # Initialize code image classifier
            self.code_classifier = pipeline(
                "image-classification",
                model="microsoft/swin-base-patch4-window7-224"
            )
            
            # Initialize image processor
            self.image_processor = AutoImageProcessor.from_pretrained(
                "microsoft/swin-base-patch4-window7-224"
            )
        except Exception as e:
            print(f"Failed to initialize image models: {e}")
    
    async def analyze_code_image(self, image_data: str) -> Dict[str, Any]:
        """
        Analyze code from image (screenshot, handwritten code, etc.)
        Returns extracted code, language detection, and structure analysis
        """
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Extract text using OCR
            extracted_text = self._extract_text(image)
            
            # Detect programming language
            language = self._detect_language(extracted_text)
            
            # Structure the code
            structured_code = self._structure_code(extracted_text, language)
            
            # Analyze code patterns
            patterns = self._analyze_patterns(structured_code, language)
            
            return {
                "success": True,
                "extracted_text": extracted_text,
                "language": language,
                "structured_code": structured_code,
                "patterns": patterns,
                "confidence": self._calculate_confidence(extracted_text)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_text(self, image: Image.Image) -> str:
        """Extract text from image using OCR"""
        # Preprocess image for better OCR
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Use Tesseract OCR
        text = self.ocr_reader.image_to_string(image)
        return text
    
    def _detect_language(self, code: str) -> str:
        """Detect programming language from extracted text"""
        language_patterns = {
            "python": [r"def\s+\w+\(", r"import\s+\w+", r"if\s+__name__"],
            "javascript": [r"function\s+\w+\(", r"const\s+\w+\s*=", r"console\.log"],
            "java": [r"public\s+class\s+\w+", r"public\s+static\s+void", r"System\.out"],
            "csharp": [r"using\s+System", r"public\s+class\s+\w+", r"Console\.Write"],
            "cpp": [r"#include\s*<", r"int\s+main\(", r"std::"],
            "html": [r"<!DOCTYPE", r"<html>", r"</html>"],
            "css": [r"\{[^}]*:\s*[^;]*;"]
        }
        
        scores = {}
        for lang, patterns in language_patterns.items():
            score = sum(1 for pattern in patterns if re.search(pattern, code, re.IGNORECASE))
            if score > 0:
                scores[lang] = score
        
        return max(scores.items(), key=lambda x: x[1])[0] if scores else "unknown"
    
    def _structure_code(self, text: str, language: str) -> str:
        """Structure and format the extracted code"""
        # Basic cleanup
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line:  # Skip empty lines
                # Fix common OCR errors
                line = self._fix_ocr_errors(line, language)
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _fix_ocr_errors(self, line: str, language: str) -> str:
        """Fix common OCR errors for different languages"""
        fixes = {
            "python": {
                "def ": "def ",
                "imp ort": "import",
                "retu rn": "return",
                "class ": "class "
            },
            "javascript": {
                "fun ction": "function",
                "con st": "const",
                "var ": "var "
            }
        }
        
        lang_fixes = fixes.get(language, {})
        for error, correction in lang_fixes.items():
            line = line.replace(error, correction)
        
        return line
    
    def _analyze_patterns(self, code: str, language: str) -> List[Dict[str, Any]]:
        """Analyze code patterns and structures"""
        patterns = []
        
        if language == "python":
            # Check for functions
            func_matches = re.findall(r'def\s+(\w+)\s*\([^)]*\):', code)
            for func in func_matches:
                patterns.append({
                    "type": "function",
                    "name": func,
                    "line_start": code.find(f"def {func}")
                })
            
            # Check for classes
            class_matches = re.findall(r'class\s+(\w+):', code)
            for cls in class_matches:
                patterns.append({
                    "type": "class",
                    "name": cls,
                    "line_start": code.find(f"class {cls}")
                })
        
        elif language == "javascript":
            # Check for functions
            func_matches = re.findall(r'function\s+(\w+)\s*\(', code)
            for func in func_matches:
                patterns.append({
                    "type": "function",
                    "name": func,
                    "line_start": code.find(f"function {func}")
                })
            
            # Check for arrow functions
            arrow_matches = re.findall(r'(\w+)\s*=\s*\([^)]*\)\s*=>', code)
            for func in arrow_matches:
                patterns.append({
                    "type": "arrow_function",
                    "name": func,
                    "line_start": code.find(f"{func} =")
                })
        
        return patterns
    
    def _calculate_confidence(self, text: str) -> float:
        """Calculate confidence score for the extraction"""
        # Simple heuristic based on code-like patterns
        code_indicators = [
            r'[a-zA-Z_][a-zA-Z0-9_]*\s*\(',  # Function calls
            r'[a-zA-Z_][a-zA-Z0-9_]*\s*=',  # Variable assignments
            r'\b(if|else|for|while|class|def|function)\b',  # Keywords
            r'[{}[\]()<>]',  # Brackets
        ]
        
        score = 0
        for indicator in code_indicators:
            matches = re.findall(indicator, text)
            score += len(matches)
        
        # Normalize to 0-1 range
        return min(score / 10, 1.0)