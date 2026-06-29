import React, { useEffect, useRef, useMemo } from 'react';
import * as d3 from 'd3';

export const NetworkGraph = ({ processes }) => {
    const svgRef = useRef(null);
    const containerRef = useRef(null);

    // Prepare data for D3
    // We need a stable ID for nodes to keep them consistent across updates
    const nodes = useMemo(() => {
        // 1. Central Hub
        const hub = { id: 'hub', type: 'hub', r: 30, x: 0, y: 0 };

        // 2. Process Nodes
        const processNodes = processes.map(p => ({
            id: p.pid,
            type: 'process',
            name: p.name,
            category: p.category,
            mbps: p.mbps,
            download_rate: p.download_rate,
            upload_rate: p.upload_rate,
            penalized: p.penalized,
            // Target radius based on bandwidth (min 5px, max 40px)
            r: Math.max(8, Math.min(60, Math.sqrt(p.mbps) * 20)),
        }));

        return [hub, ...processNodes];
    }, [processes]);

    const links = useMemo(() => {
        return processes.map(p => ({
            source: 'hub',
            target: p.pid,
            value: p.mbps
        }));
    }, [processes]);

    useEffect(() => {
        if (!svgRef.current || !containerRef.current) return;

        const width = containerRef.current.clientWidth;
        const height = containerRef.current.clientHeight;

        // --- D3 SETUP ---
        const svg = d3.select(svgRef.current);
        svg.selectAll("*").remove(); // Clear previous (simple redraw for now to handle drastic data changes easily)

        // Simulation
        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-200))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collide", d3.forceCollide().radius(d => d.r + 5));

        // --- DRAWING ---
        const linkGroup = svg.append("g").attr("class", "links");
        const nodeGroup = svg.append("g").attr("class", "nodes");

        // Defs for gradients/filters
        const defs = svg.append("defs");

        // Glow Filter
        const filter = defs.append("filter").attr("id", "glow");
        filter.append("feGaussianBlur").attr("stdDeviation", "2.5").attr("result", "coloredBlur");
        const feMerge = filter.append("feMerge");
        feMerge.append("feMergeNode").attr("in", "coloredBlur");
        feMerge.append("feMergeNode").attr("in", "SourceGraphic");

        // 1. Links
        const link = linkGroup.selectAll("line")
            .data(links)
            .enter().append("line")
            .attr("stroke", "#cbd5e1")
            .attr("stroke-width", d => Math.max(1, Math.sqrt(d.value) * 2))
            .attr("stroke-opacity", 0.6);

        // 2. Nodes
        const node = nodeGroup.selectAll("g")
            .data(nodes)
            .enter().append("g")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        // Circle Body
        node.append("circle")
            .attr("r", d => d.r)
            .attr("fill", d => {
                if (d.type === 'hub') return '#f8fafc';
                if (d.penalized) return '#f43f5e'; // Rose
                if (d.category === 'high') return '#10b981'; // Emerald
                if (d.category === 'medium') return '#06b6d4'; // Cyan
                return '#94a3b8'; // Slate
            })
            .attr("fill-opacity", d => d.type === 'hub' ? 1.0 : 0.6)
            .attr("stroke", d => {
                if (d.type === 'hub') return '#cbd5e1';
                if (d.penalized) return '#f43f5e';
                return '#fff';
            })
            .attr("stroke-width", d => d.type === 'hub' ? 0 : 1)
            .style("filter", "url(#glow)");

        // Pulse Animation for Hub
        if (nodes.find(n => n.type === 'hub')) {
            d3.select(".nodes circle") // Select the first circle (hub)
                .append("animate")
                .attr("attributeName", "r")
                .attr("values", "30;35;30")
                .attr("dur", "2s")
                .attr("repeatCount", "indefinite");
        }

        // Labels
        node.append("text")
            .text(d => d.type === 'hub' ? 'GATEWAY' : d.name)
            .attr("text-anchor", "middle")
            .attr("dy", d => d.type === 'hub' ? 5 : 4)
            .attr("font-size", d => d.type === 'hub' ? 10 : Math.min(10, d.r))
            .attr("fill", "#1e293b")
            .attr("pointer-events", "none")
            .attr("font-weight", "bold")
            .style("text-shadow", "none");

        // Tooltips (simple D3 title for now)
        node.append("title")
            .text(d => d.type === 'hub' ? 'Local Gateway' : `${d.name}\n${d.mbps.toFixed(2)} Mbps\nPID: ${d.id}`);

        // Update positions on tick
        simulation.on("tick", () => {
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node
                .attr("transform", d => `translate(${d.x},${d.y})`);
        });

        // Drag Helper functions
        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }

        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }

        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }

        return () => {
            simulation.stop();
        };
    }, [nodes, links]);

    return (
        <div className="glass-panel w-full h-full relative overflow-hidden" ref={containerRef}>
            <div className="absolute top-4 left-4 z-10 pointer-events-none">
                <h3 className="font-semibold text-slate-900">Live Topology</h3>
                <p className="text-xs text-slate-500">Physics-based network visualization</p>
            </div>
            <svg ref={svgRef} className="w-full h-full" />
        </div>
    );
};
