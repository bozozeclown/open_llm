// Configuration
const CONFIG = {
    nodeColors: {
        concept: '#FF6D00',
        code: '#2962FF',
        api: '#00C853',
        error: '#D50000',
        default: '#666666'
    },
    apiBaseUrl: '/knowledge/graph'
};

class GraphExplorer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.simulation = null;
        this.currentGraph = { nodes: [], edges: [] };
        this.init();
    }

    async init() {
        this.setupUI();
        await this.loadGraph();
        this.setupEventListeners();
    }

    setupUI() {
        this.container.innerHTML = `
            <div class="controls">
                <button id="refresh-graph">Refresh</button>
                <label>
                    Depth: <input type="range" id="graph-depth" min="1" max="3" value="2">
                </label>
                <label>
                    Physics: <input type="checkbox" id="toggle-physics" checked>
                </label>
                <button id="analyze-btn">Run Analysis</button>
            </div>
            <div id="graph-canvas"></div>
            <div id="graph-analytics"></div>
        `;
    }

    async loadGraph(depth = 2, physics = true) {
        try {
            const response = await fetch(`${CONFIG.apiBaseUrl}/json?depth=${depth}`);
            this.currentGraph = await response.json();
            this.renderGraph(physics);
        } catch (error) {
            console.error('Failed to load graph:', error);
        }
    }

    renderGraph(enablePhysics) {
        const canvas = document.getElementById('graph-canvas');
        canvas.innerHTML = '';
        
        const width = canvas.clientWidth;
        const height = canvas.clientHeight;
        
        const svg = d3.select(canvas)
            .append('svg')
            .attr('width', width)
            .attr('height', height);
        
        // Create simulation
        this.simulation = d3.forceSimulation()
            .force('link', d3.forceLink().id(d => d.id))
            .force('charge', d3.forceManyBody().strength(-100))
            .force('center', d3.forceCenter(width / 2, height / 2));
        
        // Draw links
        const link = svg.append('g')
            .selectAll('line')
            .data(this.currentGraph.edges)
            .enter().append('line')
            .attr('class', 'graph-link')
            .attr('stroke-width', d => Math.sqrt(d.value));
        
        // Draw nodes
        const node = svg.append('g')
            .selectAll('circle')
            .data(this.currentGraph.nodes)
            .enter().append('circle')
            .attr('class', 'graph-node')
            .attr('r', 8)
            .attr('fill', d => CONFIG.nodeColors[d.type] || CONFIG.nodeColors.default)
            .call(d3.drag()
                .on('start', (event, d) => {
                    if (!event.active) this.simulation.alphaTarget(0.3).restart();
                    d.fx = d.x;
                    d.fy = d.y;
                })
                .on('drag', (event, d) => {
                    d.fx = event.x;
                    d.fy = event.y;
                })
                .on('end', (event, d) => {
                    if (!event.active) this.simulation.alphaTarget(0);
                    d.fx = null;
                    d.fy = null;
                }));
        
        // Add labels
        const label = svg.append('g')
            .selectAll('text')
            .data(this.currentGraph.nodes)
            .enter().append('text')
            .attr('class', 'node-label')
            .text(d => d.label)
            .attr('font-size', 10)
            .attr('dx', 10)
            .attr('dy', 4);
        
        // Update positions
        this.simulation.nodes(this.currentGraph.nodes)
            .on('tick', () => {
                link.attr('x1', d => d.source.x)
                    .attr('y1', d => d.source.y)
                    .attr('x2', d => d.target.x)
                    .attr('y2', d => d.target.y);
                
                node.attr('cx', d => d.x)
                    .attr('cy', d => d.y);
                
                label.attr('x', d => d.x)
                    .attr('y', d => d.y);
            });
        
        this.simulation.force('link')
            .links(this.currentGraph.edges);
        
        if (!enablePhysics) {
            this.simulation.stop();
        }
    }

    setupEventListeners() {
        document.getElementById('refresh-graph').addEventListener('click', () => {
            const depth = document.getElementById('graph-depth').value;
            const physics = document.getElementById('toggle-physics').checked;
            this.loadGraph(depth, physics);
        });

        document.getElementById('analyze-btn').addEventListener('click', () => {
            this.runAnalytics();
        });
    }

    async runAnalytics() {
        try {
            const response = await fetch(`${CONFIG.apiBaseUrl}/analytics`);
            const analytics = await response.json();
            this.displayAnalytics(analytics);
        } catch (error) {
            console.error('Failed to run analytics:', error);
        }
    }

    displayAnalytics(analytics) {
        const panel = document.getElementById('graph-analytics');
        panel.innerHTML = `
            <h3>Graph Analytics</h3>
            <div class="metric">
                <span class="metric-label">Central Nodes:</span>
                <div class="metric-values">
                    ${analytics.centrality.map(n => `
                        <div>${n.label} (${n.value.toFixed(3)})</div>
                    `).join('')}
                </div>
            </div>
            <div class="metric">
                <span class="metric-label">Communities:</span>
                <div>${analytics.community.count} detected</div>
            </div>
        `;
    }
	
	highlightNode(nodeId, clientId) {
        const color = this.getClientColor(clientId);
        d3.select(`circle[data-id="${nodeId}"]`)
            .transition()
            .attr("stroke", color)
            .attr("stroke-width", 3);
    }
    
    getClientColor(clientId) {
        // Simple deterministic color assignment
        const colors = ["#FF00FF", "#00FFFF", "#FFFF00", "#FF9900"];
        const index = parseInt(clientId.split("-")[1]) % colors.length;
        return colors[index];
    }
    
    refreshNode(nodeId) {
        // Refresh node visualization
        this.loadGraph(this.currentDepth, true);
    }
	
	renderHistoricalGraph(graphData) {
        // Clear current graph
        d3.select("#graph-canvas").selectAll("*").remove();
        
        // Render historical version
        this.currentGraph = graphData;
        this.renderGraph(false); // Disable physics for historical views
        
        // Visual indication
        d3.select("#graph-canvas")
            .append("rect")
            .attr("width", "100%")
            .attr("height", "100%")
            .attr("fill", "rgba(0,0,0,0.1)")
            .attr("class", "historical-overlay");
    }
	
}

// Initialize when loaded
window.addEventListener('DOMContentLoaded', () => {
    new GraphExplorer('graph-explorer-container');
});