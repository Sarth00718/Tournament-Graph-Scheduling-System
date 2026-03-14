import { useEffect, useState } from 'react'
import axios from 'axios'

const API_BASE = 'http://localhost:8000'

// Heatmap color based on value
const cellColor = (val) => {
  if (val === 1) return 'bg-blue-500/70 text-white' // Same Team
  if (val === 2) return 'bg-yellow-500/70 text-white' // Rest Day
  if (val === 3) return 'bg-red-500/70 text-white' // Stadium Constraint
  return 'bg-white/3 text-white/20'
}

export default function AdjacencyMatrix({ scheduleData }) {
  const [matrixData, setMatrixData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const fetchMatrix = async () => {
    setLoading(true); setError('')
    try {
      const { data } = await axios.get(`${API_BASE}/adjacency_matrix`)
      setMatrixData(data.adjacency_matrix)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { if (scheduleData) fetchMatrix() }, [scheduleData])

  const cellSize = matrixData ? Math.max(Math.min(Math.floor(600 / matrixData.labels.length), 42), 18) : 32

  const edgeCount = matrixData
    ? matrixData.matrix.reduce((s, row) => s + row.reduce((rs, v) => rs + v, 0), 0) / 2
    : 0

  return (
    <div className="p-6 max-w-6xl mx-auto animate-fade-in">
      <div className="mb-6">
        <h1 className="text-3xl font-black text-white mb-1">📊 Adjacency Matrix</h1>
        <p className="text-white/50">
          Symmetric binary matrix A where A[i][j] = 1 if matches i and j have a conflict edge in G=(V,E).
          Blue cells indicate conflicting match pairs.
        </p>
      </div>

      {!scheduleData && (
        <div className="glass-card p-8 text-center">
          <p className="text-white/50 text-lg mb-2">No schedule generated yet.</p>
          <p className="text-white/30">Generate a schedule from ⚙️ Schedule Engine first.</p>
        </div>
      )}

      {scheduleData && (
        <button onClick={fetchMatrix} disabled={loading} className="btn-primary mb-4">
          {loading ? '⏳ Loading...' : '🔄 Refresh Matrix'}
        </button>
      )}

      {error && <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-300 text-sm mb-4">⚠️ {error}</div>}

      {matrixData && (
        <>
          {/* Stats */}
          <div className="grid grid-cols-3 gap-3 mb-6">
            <div className="stat-card">
              <div className="text-2xl font-black text-blue-400">{matrixData.labels.length}</div>
              <div className="text-xs text-white/40 mt-1">Vertices |V|</div>
            </div>
            <div className="stat-card">
              <div className="text-2xl font-black text-green-400">{edgeCount}</div>
              <div className="text-xs text-white/40 mt-1">Edges |E|</div>
            </div>
            <div className="stat-card">
              <div className="text-2xl font-black text-purple-400">
                {(edgeCount / (matrixData.labels.length * (matrixData.labels.length - 1) / 2) * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-white/40 mt-1">Density</div>
            </div>
          </div>

          {/* Matrix */}
          <div className="glass-card p-5 overflow-auto">
            <h2 className="section-title">Conflict Adjacency Matrix</h2>
            <div className="inline-block">
              <div className="flex" style={{ marginLeft: cellSize + 4 }}>
                {matrixData.labels.map((l, j) => (
                  <div
                    key={j}
                    className="text-center text-white/50 font-mono flex-shrink-0"
                    style={{ width: cellSize, fontSize: Math.min(cellSize * 0.35, 11), writingMode: 'vertical-rl', height: cellSize }}
                    title={l.label}
                  >
                    {l.id}
                  </div>
                ))}
              </div>
              {matrixData.matrix.map((row, i) => (
                <div key={i} className="flex items-center gap-0.5 mb-0.5">
                  <div
                    className="text-right text-white/50 font-mono flex-shrink-0 pr-1"
                    style={{ width: cellSize, fontSize: Math.min(cellSize * 0.35, 11) }}
                    title={matrixData.labels[i]?.label}
                  >
                    {matrixData.labels[i]?.id}
                  </div>
                  {row.map((val, j) => (
                    <div
                      key={j}
                      className={`flex-shrink-0 flex items-center justify-center transition-all rounded-sm font-bold ${
                        i === j ? 'bg-white/10 text-white/30' : cellColor(val)
                      }`}
                      style={{ width: cellSize - 1, height: cellSize - 1, fontSize: Math.min(cellSize * 0.4, 12) }}
                      title={val ? `${matrixData.labels[i]?.id} and ${matrixData.labels[j]?.id} (Conflict Type ${val})` : ''}
                    >
                      {i === j ? '—' : val || ''}
                    </div>
                  ))}
                </div>
              ))}
            </div>

            {/* Legend */}
            <div className="flex flex-wrap gap-4 mt-4 pt-4 border-t border-white/10 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 rounded-sm bg-blue-500/70 flex items-center justify-center text-xs font-bold">1</div>
                <span className="text-white/50">Same-Team Conflict</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 rounded-sm bg-yellow-500/70 flex items-center justify-center text-xs font-bold">2</div>
                <span className="text-white/50">Rest-Day Violation</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 rounded-sm bg-red-500/70 flex items-center justify-center text-xs font-bold">3</div>
                <span className="text-white/50">Stadium Conflict</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 rounded-sm bg-white/3 border border-white/10 flex items-center justify-center text-xs font-bold text-white/20">0</div>
                <span className="text-white/50">No Conflict</span>
              </div>
            </div>
          </div>

          {/* Match labels table */}
          <div className="glass-card p-5 mt-4">
            <h2 className="section-title">Match Index Reference</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
              {matrixData.labels.map((l, i) => (
                <div key={i} className="flex items-center gap-2 py-1.5 px-3 rounded-lg bg-white/5 text-sm">
                  <span className="badge bg-blue-600/20 text-blue-400 font-mono text-xs">{l.id}</span>
                  <span className="text-white/60 truncate">{l.label}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
