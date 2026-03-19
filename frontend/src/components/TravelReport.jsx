import { useEffect, useState } from 'react'
import axios from 'axios'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import API_BASE_URL from '../config/api'

const API_BASE = API_BASE_URL
const COLORS = ['#3b82f6','#10b981','#f59e0b','#ef4444','#8b5cf6','#ec4899','#14b8a6','#f97316','#84cc16','#06b6d4']

export default function TravelReport({ scheduleData }) {
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [expanded, setExpanded] = useState({})

  const fetchReport = async () => {
    setLoading(true); setError('')
    try {
      const { data } = await axios.get(`${API_BASE}/travel_report`)
      setReport(data.travel_report)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { if (scheduleData) fetchReport() }, [scheduleData])

  const teams = report ? Object.keys(report) : []
  const chartData = teams.map((t, i) => ({ name: t, km: report[t].total_km, color: COLORS[i % COLORS.length] }))
    .sort((a, b) => b.km - a.km)
  const totalKm = teams.reduce((s, t) => s + report[t].total_km, 0)

  return (
    <div className="p-6 max-w-6xl mx-auto animate-fade-in">
      <div className="mb-6">
        <h1 className="text-3xl font-black text-white mb-1">🗺️ Travel Optimizer</h1>
        <p className="text-white/50">
          Dijkstra's shortest-path algorithm on the stadium spatial graph (haversine distances).
          Each team's route is the sequence of stadiums visited in match order.
        </p>
      </div>

      {!scheduleData && (
        <div className="glass-card p-8 text-center">
          <p className="text-white/50 text-lg mb-2">No schedule generated yet.</p>
          <p className="text-white/30">Generate a schedule from ⚙️ Schedule Engine first.</p>
        </div>
      )}

      {scheduleData && (
        <button onClick={fetchReport} disabled={loading} className="btn-primary mb-4">
          {loading ? '⏳ Loading...' : '🔄 Refresh Report'}
        </button>
      )}

      {error && <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-300 text-sm mb-4">⚠️ {error}</div>}

      {report && (
        <>
          {/* Summary stats */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-6">
            <div className="stat-card"><div className="text-2xl font-black text-blue-400">{teams.length}</div><div className="text-xs text-white/40 mt-1">Teams</div></div>
            <div className="stat-card"><div className="text-2xl font-black text-green-400">{totalKm.toFixed(0)} km</div><div className="text-xs text-white/40 mt-1">Total Travel</div></div>
            <div className="stat-card"><div className="text-2xl font-black text-purple-400">{(totalKm / teams.length).toFixed(0)} km</div><div className="text-xs text-white/40 mt-1">Avg per Team</div></div>
          </div>

          {/* Bar chart */}
          <div className="glass-card p-5 mb-6">
            <h2 className="section-title">📊 Travel Distance by Team</h2>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="name" tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }} />
                <YAxis tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }} unit=" km" />
                <Tooltip
                  contentStyle={{ background: 'rgba(13,22,41,0.95)', border: '1px solid rgba(255,255,255,0.15)', borderRadius: 8 }}
                  labelStyle={{ color: 'white', fontWeight: 600 }}
                  itemStyle={{ color: '#93c5fd' }}
                  formatter={v => [`${v} km`, 'Travel Distance']}
                />
                <Bar dataKey="km" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry, i) => <Cell key={i} fill={entry.color} fillOpacity={0.8} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Per-team accordions */}
          <div className="space-y-3">
            {teams.map((team, i) => {
              const info = report[team]
              const isOpen = expanded[team]
              return (
                <div key={team} className="glass-card overflow-hidden">
                  <button
                    onClick={() => setExpanded(e => ({ ...e, [team]: !e[team] }))}
                    className="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-all"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 rounded-full" style={{ background: COLORS[i % COLORS.length] }} />
                      <span className="font-bold text-white">{team}</span>
                      <span className="text-white/40 text-sm">
                        {info.stadiums.join(' → ')}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="font-mono font-bold text-green-400">{info.total_km} km</span>
                      <span className="text-white/40">{isOpen ? '▲' : '▼'}</span>
                    </div>
                  </button>

                  {isOpen && (
                    <div className="px-4 pb-4 border-t border-white/10">
                      <table className="data-table mt-3">
                        <thead><tr><th>#</th><th>From</th><th>To</th><th>Dijkstra Path</th><th>Distance</th></tr></thead>
                        <tbody>
                          {info.legs.map((leg, j) => (
                            <tr key={j}>
                              <td className="text-white/40">{j+1}</td>
                              <td>{leg.from}</td>
                              <td>{leg.to}</td>
                              <td className="font-mono text-xs text-blue-300">{leg.path.join(' → ')}</td>
                              <td className="font-bold text-green-400">{leg.distance_km} km</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}
