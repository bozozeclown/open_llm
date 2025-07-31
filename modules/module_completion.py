from modules.base_module import BaseModule
from shared.schemas import Query, Response
from core.completion import CodeCompleter

class CompletionModule(BaseModule):
    MODULE_ID = "completion"
    CAPABILITIES = ["code_completion"]

    async def initialize(self):
        self.completer = CodeCompleter()

    async def process(self, query: Query) -> Response:
        completions = self.completer.generate_completions({
            "context": query.context.get("code", ""),
            "cursor_context": query.content
        })
        return Response(
            content="\n---\n".join(completions["completions"]),
            metadata={
                "type": "completion",
                "language": query.context.get("language", "unknown")
            }
        )