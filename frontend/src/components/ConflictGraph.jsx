import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import axios from 'axios'

const API_BASE = 'http://localhost:8000'

// 20 distinct colors for time-slot groups
const SLOT_COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
  '#ec4899', '#14b8a6', '#f97316', '#84cc16', '#06b6d4',
  '#6366f1', '#d946ef', '#22c55e', '#eab308', '#64748b',
  '#a78bfa', '#fb923c', '#34d399', '#f472b6', '#60a5fa',
]

export default function ConflictGraph({ scheduleData }) {
  const svgRef = useRef(null)
  const [graphData, setGraphData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [tooltip, setTooltip] = useState({ visible: false, x: 0, y: 0, content: '' })
  const [stats, setStats] = useState(null)

  const fetchGraph = async () => {
    setLoading(true); setError('')
    try {
      const { data } = await axios.get(`${API_BASE}/conflict_graph`)
      setGraphData(data.graph)
      setStats({ chi: data.chromatic_number, color_groups: data.color_groups, ...data.stats })
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (scheduleData) fetchGraph()
  }, [scheduleData])

  useEffect(() => {
    if (!graphData || !svgRef.current) return
    drawGraph(graphData)
  }, [graphData])

  const drawGraph = (data) => {
    const container = svgRef.current.parentElement
    const W = container.clientWidth || 800
    const H = 500

    d3.select(svgRef.current).selectAll('*').remove()

    const svg = d3.select(svgRef.current)
      .attr('width', W).attr('height', H)
      .style('background', 'transparent')

    // Add zoom
    const g = svg.append('g')
    svg.call(d3.zoom().scaleExtent([0.3, 3]).on('zoom', e => g.attr('transform', e.transform)))

    const nodes = data.nodes.map(d => ({ ...d }))
    const links = data.edges.map(d => ({ ...d, source: d.source, target: d.target }))

    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id(d => d.id).distance(90))
      .force('charge', d3.forceManyBody().strength(-250))
      .force('center', d3.forceCenter(W / 2, H / 2))
      .force('collision', d3.forceCollide(30))

    // Links
    const link = g.append('g')
      .selectAll('line')
      .data(links).join('line')
      .attr('class', 'conflict-graph-link')
      .attr('stroke', '#475569')
      .attr('stroke-width', 1.5)
      .attr('stroke-opacity', 0.6)

    // Node groups
    const node = g.append('g')
      .selectAll('g')
      .data(nodes).join('g')
      .attr('class', 'conflict-graph-node')
      .call(d3.drag()
        .on('start', (e, d) => { if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y })
        .on('drag', (e, d) => { d.fx = e.x; d.fy = e.y })
        .on('end', (e, d) => { if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null })
      )

    // Circle
    node.append('circle')
      .attr('r', 22)
      .attr('fill', d => SLOT_COLORS[d.color % SLOT_COLORS.length])
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .attr('fill-opacity', 0.85)
      .on('mouseover', function(e, d) {
        d3.select(this).attr('r', 26).attr('stroke-width', 3)
        setTooltip({
          visible: true, x: e.offsetX + 15, y: e.offsetY - 10,
          content: `${d.label}\nTime Slot Group: ${d.color}`
        })
      })
      .on('mouseout', function(e, d) {
        d3.select(this).attr('r', 22).attr('stroke-width', 2)
        setTooltip({ visible: false })
      })

    // Label
    node.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('font-size', 9)
      .attr('font-weight', '600')
      .attr('fill', '#fff')
      .text(d => d.id)
      .style('pointer-events', 'none')

    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x).attr('y2', d => d.target.y)
      node.attr('transform', d => `translate(${d.x},${d.y})`)
    })
  }

  return (
    <div className="p-6 max-w-6xl mx-auto animate-fade-in">
      <div className="mb-6">
        <h1 className="text-3xl font-black text-white mb-1">🕸️ Conflict Graph G=(V,E)</h1>
        <p className="text-white/50">Force-directed graph where nodes = matches, edges = conflicts. Node color = time-slot group (Welsh-Powell coloring).</p>
      </div>

      {!scheduleData && (
        <div className="glass-card p-8 text-center">
          <p className="text-white/50 text-lg mb-4">No schedule generated yet.</p>
          <p className="text-white/30">Go to ⚙️ Schedule Engine, input parameters, and click <strong className="text-white/50">Generate Schedule</strong> first.</p>
        </div>
      )}

      {scheduleData && (
        <div className="flex gap-4 flex-wrap mb-4">
          <button onClick={fetchGraph} disabled={loading} className="btn-primary">
            {loading ? '⏳ Loading...' : '🔄 Refresh Graph'}
          </button>
        </div>
      )}

      {error && <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-300 text-sm mb-4">⚠️ {error}</div>}

      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          {[
            { label: 'Vertices |V|', value: stats.num_vertices, color: 'text-blue-400' },
            { label: 'Edges |E|', value: stats.num_edges, color: 'text-green-400' },
            { label: 'χ(G) Chromatic No.', value: stats.chi, color: 'text-purple-400' },
            { label: 'Max Degree', value: stats.max_degree, color: 'text-orange-400' },
          ].map(s => (
            <div key={s.label} className="stat-card">
              <div className={`text-2xl font-black ${s.color}`}>{s.value}</div>
              <div className="text-xs text-white/40 mt-1">{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {graphData && (
        <div className="glass-card p-4 relative overflow-hidden">
          <div className="text-xs text-white/40 mb-3 flex items-center gap-2">
            <span>🖱️ Drag nodes · Scroll to zoom · Hover for details</span>
          </div>
          <div className="relative">
            <svg ref={svgRef} className="w-full rounded-lg" style={{ minHeight: '500px' }} />
            {tooltip.visible && (
              <div className="node-tooltip" style={{ left: tooltip.x, top: tooltip.y }}>
                {tooltip.content.split('\n').map((line, i) => <div key={i}>{line}</div>)}
              </div>
            )}
          </div>

          {/* Legend */}
          {stats?.color_groups && (
            <div className="mt-4 pt-4 border-t border-white/10">
              <p className="text-xs text-white/40 mb-2 font-semibold uppercase tracking-wider">Time Slot Groups</p>
              <div className="flex flex-wrap gap-2">
                {Object.entries(stats.color_groups).map(([color, nodes]) => (
                  <div key={color} className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-white/5 text-xs">
                    <div className="w-3 h-3 rounded-full" style={{ background: SLOT_COLORS[parseInt(color) % SLOT_COLORS.length] }} />
                    <span className="text-white/60">Group {color}</span>
                    <span className="text-white/30">({nodes.length} matches)</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
