import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import axios from 'axios'
import API_BASE_URL from '../config/api'

const API_BASE = API_BASE_URL

export default function TournamentTree({ scheduleData }) {
  const svgRef = useRef(null)
  const [treeData, setTreeData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const fetchTree = async () => {
    setLoading(true); setError('')
    try {
      const { data } = await axios.get(`${API_BASE}/tournament_tree`)
      setTreeData(data.tournament_tree)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { if (scheduleData) fetchTree() }, [scheduleData])

  useEffect(() => {
    if (!treeData || !svgRef.current) return
    drawTree(treeData)
  }, [treeData])

  const drawTree = (data) => {
    const container = svgRef.current.parentElement
    const W = Math.max(container.clientWidth || 900, 900)
    
    // Build adjacency: child -> parent
    const parentMap = {}
    const childrenMap = {}
    data.edges.forEach(e => {
      parentMap[e.source] = e.target
      if (!childrenMap[e.target]) childrenMap[e.target] = []
      childrenMap[e.target].push(e.source)
    })
    const nodeMap = Object.fromEntries(data.nodes.map(n => [n.id, n]))
    
    // Find root (node with no outgoing edge that maps it to a parent)
    const root = data.nodes.find(n => !parentMap[n.id])
    if (!root) return

    // Build d3 hierarchy
    const buildH = (nodeId) => {
      const node = nodeMap[nodeId]
      const children = (childrenMap[nodeId] || []).map(buildH)
      return { id: nodeId, label: node.label, round: node.round, type: node.type, children }
    }

    const hierarchy = d3.hierarchy(buildH(root.id))
    const numLeaves = hierarchy.leaves().length
    const H = Math.max(numLeaves * 55, 400)

    d3.select(svgRef.current).selectAll('*').remove()
    const svg = d3.select(svgRef.current).attr('width', W).attr('height', H + 60)
    const g = svg.append('g').attr('transform', 'translate(60, 30)')

    // Horizontal tree layout (root on right)
    const treeLayout = d3.tree().size([H, W - 200])

    // Reverse: leaves on left, root on right
    treeLayout(hierarchy)
    const maxDepth = d3.max(hierarchy.descendants(), d => d.depth)
    hierarchy.each(d => { d.y = (maxDepth - d.depth) * ((W - 200) / (maxDepth || 1)) })

    // Links
    g.selectAll('.bracket-link')
      .data(hierarchy.links()).join('path')
      .attr('class', 'bracket-link')
      .attr('stroke', 'rgba(99,179,237,0.35)')
      .attr('fill', 'none')
      .attr('stroke-width', 1.5)
      .attr('d', d3.linkHorizontal().x(d => d.y).y(d => d.x))

    // Nodes
    const node = g.selectAll('.bracket-node')
      .data(hierarchy.descendants()).join('g')
      .attr('class', 'bracket-node')
      .attr('transform', d => `translate(${d.y},${d.x})`)

    const isLeaf = d => !childrenMap[d.data.id]
    const isChampion = d => !parentMap[d.data.id]

    node.append('rect')
      .attr('x', -55).attr('y', -18).attr('width', 110).attr('height', 36)
      .attr('rx', 6).attr('ry', 6)
      .attr('fill', d =>
        isChampion(d) ? 'rgba(234,179,8,0.25)' :
        isLeaf(d) ? 'rgba(59,130,246,0.2)' :
        'rgba(139,92,246,0.15)'
      )
      .attr('stroke', d =>
        isChampion(d) ? 'rgba(234,179,8,0.6)' :
        isLeaf(d) ? 'rgba(59,130,246,0.5)' :
        'rgba(139,92,246,0.4)'
      )
      .attr('stroke-width', 1.5)

    node.append('text')
      .attr('text-anchor', 'middle').attr('dy', '0.35em')
      .attr('font-size', d => isLeaf(d) ? 11 : 10)
      .attr('font-weight', d => isLeaf(d) ? '700' : '500')
      .attr('fill', d => isChampion(d) ? '#fbbf24' : '#e2e8f0')
      .text(d => d.data.label.length > 14 ? d.data.label.slice(0, 13) + '…' : d.data.label)

    // Round labels
    const rounds = [...new Set(hierarchy.descendants().map(d => d.depth))]
    rounds.forEach(depth => {
      const nodesAtDepth = hierarchy.descendants().filter(d => d.depth === depth)
      const y = nodesAtDepth[0]?.y ?? 0
      const round = maxDepth - depth + 1
      svg.append('text')
        .attr('x', y + 60).attr('y', 18)
        .attr('text-anchor', 'middle')
        .attr('font-size', 10)
        .attr('fill', 'rgba(255,255,255,0.3)')
        .attr('font-weight', '600')
        .text(depth === 0 ? 'Final' : `Round ${round}`)
    })
  }

  return (
    <div className="p-6 max-w-6xl mx-auto animate-fade-in">
      <div className="mb-6">
        <h1 className="text-3xl font-black text-white mb-1">🏆 Tournament Tree</h1>
        <p className="text-white/50">Single-elimination knockout bracket as a directed rooted tree. Teams seeded by natural order; byes added for non-power-of-2 team counts.</p>
      </div>

      {!scheduleData && (
        <div className="glass-card p-8 text-center">
          <p className="text-white/50 text-lg mb-2">No schedule generated yet.</p>
          <p className="text-white/30">Generate a schedule first from the ⚙️ Schedule Engine.</p>
        </div>
      )}

      {scheduleData && (
        <button onClick={fetchTree} disabled={loading} className="btn-primary mb-4">
          {loading ? '⏳ Loading...' : '🔄 Refresh Tree'}
        </button>
      )}

      {error && <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-300 text-sm mb-4">⚠️ {error}</div>}

      {treeData && (
        <>
          <div className="glass-card p-2 mb-4 flex gap-4 text-sm">
            <div className="flex items-center gap-2 px-3 py-1.5"><div className="w-3 h-3 rounded bg-blue-500/50 border border-blue-500/70"/>Team Seed</div>
            <div className="flex items-center gap-2 px-3 py-1.5"><div className="w-3 h-3 rounded bg-purple-500/30 border border-purple-500/50"/>Match Winner</div>
            <div className="flex items-center gap-2 px-3 py-1.5"><div className="w-3 h-3 rounded bg-yellow-500/30 border border-yellow-500/50"/>Champion</div>
          </div>
          <div className="glass-card p-4 overflow-x-auto">
            <svg ref={svgRef} className="min-w-full" />
          </div>
        </>
      )}
    </div>
  )
}
