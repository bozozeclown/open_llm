from modules.base_module import BaseModule
from shared.schemas import Query, Response
from core.signature_help import SignatureProvider

class SignatureModule(BaseModule):
    MODULE_ID = "signature"
    CAPABILITIES = ["signature_help"]

    async def initialize(self):
        self.provider = SignatureProvider()

    async def process(self, query: Query) -> Response:
        help_data = self.provider.get_signature_help(
            code=query.context.get("code", ""),
            language=query.context.get("language", "python"),
            cursor_pos=query.context.get("cursor_pos", 0)
        )
        return Response(
            content=help_data if help_data else "No signature found",
            metadata={"type": "signature_help"}
        )