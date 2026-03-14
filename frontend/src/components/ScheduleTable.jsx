import { useState } from 'react'

const SLOT_COLORS = {
  Morning: 'bg-yellow-500/20 text-yellow-400',
  Afternoon: 'bg-orange-500/20 text-orange-400',
  Evening: 'bg-indigo-500/20 text-indigo-400',
}

const COLOR_PALETTE = [
  'bg-blue-600/20 text-blue-400','bg-green-600/20 text-green-400','bg-purple-600/20 text-purple-400',
  'bg-red-600/20 text-red-400','bg-pink-600/20 text-pink-400','bg-teal-600/20 text-teal-400',
  'bg-orange-600/20 text-orange-400','bg-cyan-600/20 text-cyan-400',
]

export default function ScheduleTable({ scheduleData }) {
  const [search, setSearch] = useState('')
  const [filterTeam, setFilterTeam] = useState('')
  const [filterSlot, setFilterSlot] = useState('')
  const [sortKey, setSortKey] = useState('date')
  const [sortDir, setSortDir] = useState('asc')
  const [page, setPage] = useState(0)
  const PAGE_SIZE = 20

  if (!scheduleData?.schedule) {
    return (
      <div className="p-6 max-w-6xl mx-auto">
        <h1 className="text-3xl font-black text-white mb-4">📅 Master Schedule</h1>
        <div className="glass-card p-8 text-center">
          <p className="text-white/50 text-lg mb-2">No schedule generated yet.</p>
          <p className="text-white/30">Generate a schedule from ⚙️ Schedule Engine first.</p>
        </div>
      </div>
    )
  }

  const rows = scheduleData.schedule
  const allTeams = [...new Set(rows.flatMap(r => [r.teamA, r.teamB]))].sort()

  const SLOT_ORDER = { Morning: 0, Afternoon: 1, Evening: 2 }

  let filtered = rows.filter(r => {
    if (filterTeam && r.teamA !== filterTeam && r.teamB !== filterTeam) return false
    if (filterSlot && r.time_slot !== filterSlot) return false
    if (search) {
      const s = search.toLowerCase()
      return [r.match, r.teamA, r.teamB, r.stadium, r.date].some(v => v.toLowerCase().includes(s))
    }
    return true
  })

  filtered = [...filtered].sort((a, b) => {
    let va, vb
    if (sortKey === 'date') { va = a.date + SLOT_ORDER[a.time_slot]; vb = b.date + SLOT_ORDER[b.time_slot] }
    else if (sortKey === 'match') { va = parseInt(a.match.slice(1)); vb = parseInt(b.match.slice(1)) }
    else { va = a[sortKey]; vb = b[sortKey] }
    if (va < vb) return sortDir === 'asc' ? -1 : 1
    if (va > vb) return sortDir === 'asc' ? 1 : -1
    return 0
  })

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE)
  const paginated = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  const handleSort = (key) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('asc') }
    setPage(0)
  }
  const SortIcon = ({ key: k }) => sortKey === k ? (sortDir === 'asc' ? ' ↑' : ' ↓') : ' ↕'

  return (
    <div className="p-6 max-w-7xl mx-auto animate-fade-in">
      <div className="mb-6">
        <h1 className="text-3xl font-black text-white mb-1">📅 Master Schedule</h1>
        <p className="text-white/50">Complete match schedule. All constraints are satisfied by Welsh-Powell graph coloring.</p>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        {[
          { label: 'Total Matches', value: rows.length, c: 'text-blue-400' },
          { label: 'Time Slot Groups', value: scheduleData.chromatic_number, c: 'text-purple-400' },
          { label: 'Teams', value: scheduleData.total_teams, c: 'text-green-400' },
          { label: 'Filtered Results', value: filtered.length, c: 'text-orange-400' },
        ].map(s => (
          <div key={s.label} className="stat-card">
            <div className={`text-2xl font-black ${s.c}`}>{s.value}</div>
            <div className="text-xs text-white/40 mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="glass-card p-4 mb-4 flex flex-wrap gap-3 items-center">
        <input
          className="input-field w-48"
          placeholder="🔍 Search..."
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(0) }}
        />
        <select
          className="input-field w-44"
          value={filterTeam}
          onChange={e => { setFilterTeam(e.target.value); setPage(0) }}
        >
          <option value="">All Teams</option>
          {allTeams.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <select
          className="input-field w-40"
          value={filterSlot}
          onChange={e => { setFilterSlot(e.target.value); setPage(0) }}
        >
          <option value="">All Slots</option>
          {['Morning','Afternoon','Evening'].map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        {(search || filterTeam || filterSlot) && (
          <button onClick={() => { setSearch(''); setFilterTeam(''); setFilterSlot(''); setPage(0) }}
            className="btn-secondary text-sm">Clear</button>
        )}
        <span className="ml-auto text-white/30 text-sm">{filtered.length} matches</span>
      </div>

      {/* Table */}
      <div className="glass-card overflow-x-auto">
        <table className="data-table">
          <thead>
            <tr>
              {[
                ['match','Match'], ['teamA','Team A'], ['teamB','Team B'],
                ['date','Date'], ['time_slot','Slot'], ['stadium','Stadium'], ['color','Group']
              ].map(([key, label]) => (
                <th key={key}>
                  <button onClick={() => handleSort(key)} className="flex items-center gap-1 hover:text-white transition-colors">
                    {label}<SortIcon key={key} />
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginated.map((row, i) => (
              <tr key={i} className="hover:bg-white/5 transition-colors">
                <td><span className="badge bg-blue-600/20 text-blue-400 font-mono">{row.match}</span></td>
                <td className="font-semibold text-white">{row.teamA}</td>
                <td className="font-semibold text-white">{row.teamB}</td>
                <td className="font-mono text-sm text-white/60">{row.date}</td>
                <td><span className={`badge ${SLOT_COLORS[row.time_slot] || 'bg-white/10 text-white/50'}`}>{row.time_slot}</span></td>
                <td className="text-white/70">{row.stadium}</td>
                <td><span className={`badge ${COLOR_PALETTE[row.color % COLOR_PALETTE.length]}`}>G{row.color}</span></td>
              </tr>
            ))}
          </tbody>
        </table>

        {filtered.length === 0 && (
          <div className="text-center py-8 text-white/30">No matches found for current filters.</div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-white/10">
            <span className="text-white/40 text-sm">Page {page + 1} of {totalPages}</span>
            <div className="flex gap-2">
              <button disabled={page === 0} onClick={() => setPage(p => p - 1)} className="btn-secondary text-sm px-3 py-1.5">← Prev</button>
              {[...Array(Math.min(totalPages, 5))].map((_, i) => {
                const p = page < 3 ? i : page - 2 + i
                if (p >= totalPages) return null
                return (
                  <button key={p} onClick={() => setPage(p)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${p === page ? 'bg-blue-600/50 text-white' : 'btn-secondary'}`}>
                    {p + 1}
                  </button>
                )
              })}
              <button disabled={page === totalPages - 1} onClick={() => setPage(p => p + 1)} className="btn-secondary text-sm px-3 py-1.5">Next →</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
