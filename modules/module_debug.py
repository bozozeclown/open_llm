from modules.base_module import BaseModule
from shared.schemas import Response, Query
from core.debugger import CodeDebugger

class DebugModule(BaseModule):
    MODULE_ID = "debug"
    CAPABILITIES = ["error_diagnosis", "fix_suggestion"]
    
    async def initialize(self):
        self.debugger = CodeDebugger(self.context.graph)
        
    async def process(self, query: Query) -> Response:
        if not query.context.get("error"):
            return Response(content="No error provided", metadata={})
            
        frames = self.debugger.analyze_traceback(
            query.context["code"],
            query.context["error"]
        )
        suggestions = self.debugger.suggest_fixes(frames)
        
        return Response(
            content=self._format_report(frames, suggestions),
            metadata={
                "frames": [f.__dict__ for f in frames],
                "suggestions": suggestions
            }
        )
        
    def _format_report(self, frames, suggestions) -> str:
        report = []
        for frame in frames:
            report.append(f"File {frame.file}, line {frame.line}:")
            report.append(f"Context:\n{frame.context}")
            report.append(f"Error: {frame.error}")
            if frame.line in suggestions:
                report.append("Suggestions:")
                report.extend(f"- {sug}" for sug in suggestions[frame.line])
            report.append("")
        return '\n'.join(report)