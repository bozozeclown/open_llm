import asyncio
import json
from fastapi import WebSocket
from typing import Dict, List

class CollaborationServer:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_activities = {}
        self.annotation_queue = asyncio.Queue()

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.user_activities[client_id] = {"last_action": "connected"}
        
        # Send current knowledge graph state
        await self._send_graph_snapshot(websocket)

    async def disconnect(self, client_id: str):
        self.active_connections.pop(client_id, None)
        self.user_activities.pop(client_id, None)

    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)

    async def handle_message(self, client_id: str, data: dict):
        message_type = data.get("type")
        
        if message_type == "node_select":
            self.user_activities[client_id] = {
                "selected_node": data["node_id"],
                "last_action": "selection"
            }
            await self.broadcast({
                "type": "user_activity",
                "client": client_id,
                "activity": "selected_node",
                "node_id": data["node_id"]
            })

        elif message_type == "add_annotation":
            await self.annotation_queue.put({
                "client_id": client_id,
                "node_id": data["node_id"],
                "content": data["content"]
            })
            await self.broadcast({
                "type": "new_annotation",
                "node_id": data["node_id"],
                "preview": data["content"][:50] + "..."
            })

    async def _send_graph_snapshot(self, websocket: WebSocket):
        # This would come from your knowledge graph
        await websocket.send_json({
            "type": "graph_snapshot",
            "nodes": [],  # Actual nodes would be populated
            "edges": []   # Actual edges would be populated
        })

    async def process_annotations(self, kg):
        """Background task to process annotation queue"""
        while True:
            annotation = await self.annotation_queue.get()
            node_id = annotation["node_id"]
            
            # Add to knowledge graph
            kg.add_entity(
                content=annotation["content"],
                type="annotation",
                metadata={
                    "author": annotation["client_id"],
                    "timestamp": str(datetime.now())
                }
            )
            
            # Notify all users
            await self.broadcast({
                "type": "annotation_added",
                "node_id": node_id,
                "author": annotation["client_id"]
            })