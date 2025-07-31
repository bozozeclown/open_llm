class CollaborationClient {
    constructor(graphExplorer, clientId) {
        this.socket = new WebSocket(`ws://${window.location.host}/collaborate`);
        this.graphExplorer = graphExplorer;
        this.clientId = clientId;
        this.setupSocket();
    }

    setupSocket() {
        this.socket.onopen = () => {
            this.send({ type: "register", client_id: this.clientId });
        };

        this.socket.onmessage = (event) => {
            const message = JSON.parse(event.data);
            
            switch(message.type) {
                case "user_activity":
                    this.handleUserActivity(message);
                    break;
                case "new_annotation":
                    this.showAnnotationPreview(message);
                    break;
                case "annotation_added":
                    this.graphExplorer.refreshNode(message.node_id);
                    break;
                case "graph_update":
                    this.graphExplorer.updateGraph(message.nodes, message.edges);
                    break;
            }
        };

        this.socket.onclose = () => {
            console.log("Collaboration disconnected");
        };
    }

    send(data) {
        if (this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(data));
        }
    }

    handleUserActivity(message) {
        // Visualize other users' activity
        if (message.client !== this.clientId) {
            this.graphExplorer.highlightNode(message.node_id, message.client);
        }
    }

    showAnnotationPreview(message) {
        // Display notification about new annotation
        const notification = document.createElement("div");
        notification.className = "annotation-notification";
        notification.innerHTML = `
            New annotation on ${message.node_id}: ${message.preview}
        `;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }
}
