import { useState } from 'react'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'

const API_BASE = 'http://localhost:8000'

const DEFAULT_TEAMS = ['TeamA', 'TeamB', 'TeamC', 'TeamD', 'TeamE', 'TeamF']
const DEFAULT_STADIUMS = [
  { name: 'Wankhede Stadium', lat: 18.9388, lng: 72.8258 },
  { name: 'Eden Gardens', lat: 22.5645, lng: 88.3434 },
  { name: 'Chinnaswamy Stadium', lat: 12.9790, lng: 77.5985 },
  { name: 'Narendra Modi Stadium', lat: 23.0902, lng: 72.5959 },
  { name: 'Chepauk Stadium', lat: 13.0620, lng: 80.2789 },
]

export default function Dashboard({ scheduleData, setScheduleData }) {
  const navigate = useNavigate()

  const [teams, setTeams] = useState([...DEFAULT_TEAMS])
  const [newTeam, setNewTeam] = useState('')
  const [stadiums, setStadiums] = useState([...DEFAULT_STADIUMS])
  const [newStadium, setNewStadium] = useState({ name: '', lat: '', lng: '' })
  const [rules, setRules] = useState({
    start_date: '2024-06-01',
    end_date: '2024-06-30',
    time_slots: ['Morning', 'Afternoon', 'Evening'],
    rest_days_between_matches: 2,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // ── Team management ──────────────────────────────────────────────────────
  const addTeam = () => {
    setError('')
    const t = newTeam.trim()
    if (!t) return setError('Team name cannot be empty.')
    if (teams.includes(t)) return setError(`Team "${t}" already exists.`)
    setTeams([...teams, t]); setNewTeam('')
  }
  const removeTeam = (name) => setTeams(teams.filter(t => t !== name))

  // ── Stadium management ───────────────────────────────────────────────────
  const addStadium = () => {
    setError('')
    const n = newStadium.name.trim()
    if (!n) return setError('Stadium name cannot be empty.')
    if (!newStadium.lat || !newStadium.lng) return setError('Stadium coordinates cannot be empty.')
    if (stadiums.find(s => s.name === n)) return setError(`Stadium "${n}" already exists.`)
    setStadiums([...stadiums, { ...newStadium, lat: parseFloat(newStadium.lat), lng: parseFloat(newStadium.lng) }])
    setNewStadium({ name: '', lat: '', lng: '' })
  }
  const removeStadium = (name) => setStadiums(stadiums.filter(s => s.name !== name))

  // ── Time slot toggles ─────────────────────────────────────────────────────
  const toggleSlot = (slot) => {
    setError('')
    const slots = rules.time_slots.includes(slot)
      ? rules.time_slots.filter(s => s !== slot)
      : [...rules.time_slots, slot]
    if (slots.length === 0) return setError('At least one time slot must be selected.')
    setRules({ ...rules, time_slots: slots })
  }

  // ── Generate schedule ─────────────────────────────────────────────────────
  const handleGenerate = async () => {
    setError(''); setSuccess('');
    
    // Validations
    if (new Date(rules.start_date) > new Date(rules.end_date)) {
      return setError('Start date must be before or equal to the end date.')
    }
    if (teams.length < 2) return setError('At least 2 teams are required.')
    if (stadiums.length < 1) return setError('At least 1 stadium is required.')

    setLoading(true)
    try {
      const { data } = await axios.post(`${API_BASE}/generate_schedule`, {
        teams,
        stadiums,
        rules: {
          start_date: rules.start_date,
          end_date: rules.end_date,
          time_slots: rules.time_slots,
          rest_days_between_matches: parseInt(rules.rest_days_between_matches),
        },
      })
      
      const totalDays = Math.ceil((new Date(data.schedule[data.schedule.length - 1].date) - new Date(data.schedule[0].date)) / (1000 * 60 * 60 * 24)) + 1;
      
      // Calculate stadium usage
      const usage = {}
      data.schedule.forEach(m => usage[m.stadium] = (usage[m.stadium] || 0) + 1)
      data.stadiumUsage = Object.entries(usage).map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count)
      data.totalDays = totalDays
      
      setScheduleData(data)
      setSuccess(`✅ Schedule generated! ${data.total_matches} matches across ${totalDays} days.`)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to connect to backend.')
    } finally {
      setLoading(false)
    }
  }

  const loadSample = () => {
    setTeams([...DEFAULT_TEAMS])
    setStadiums([...DEFAULT_STADIUMS])
    setRules({ start_date: '2024-06-01', end_date: '2024-06-30', time_slots: ['Morning', 'Afternoon', 'Evening'], rest_days_between_matches: 2 })
    setSuccess('Sample data loaded.')
  }

  return (
    <div className="p-6 max-w-6xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-black text-white mb-1">⚙️ Schedule Engine</h1>
        <p className="text-white/50">Configure tournament parameters and generate the optimal schedule using graph coloring.</p>
      </div>

      {/* Stats bar (after generation) */}
      {scheduleData && (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-3 mb-6 animate-slide-up">
          {[
            { label: 'Total Matches', value: scheduleData.total_matches, color: 'text-green-400' },
            { label: 'χ(G) Time Slots Needed', value: scheduleData.chromatic_number, color: 'text-purple-400' },
            { label: 'Total Days Required', value: scheduleData.totalDays, color: 'text-yellow-400' },
          ].map(s => (
            <div key={s.label} className="stat-card">
              <div className={`text-2xl font-black ${s.color}`}>{s.value}</div>
              <div className="text-xs text-white/40 mt-1">{s.label}</div>
            </div>
          ))}
          <div className="stat-card col-span-2 sm:col-span-4 lg:col-span-2 overflow-y-auto max-h-24">
            <div className="text-xs text-white/40 mb-1 font-bold uppercase">Stadium Usage Frequency</div>
            <div className="flex flex-wrap gap-2">
              {scheduleData.stadiumUsage?.map(st => (
                 <span key={st.name} className="px-2 py-1 rounded bg-blue-500/20 text-blue-300 text-xs border border-blue-500/30">
                    {st.name}: <strong className="text-white">{st.count} matches</strong>
                 </span>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Teams */}
        <div className="glass-card p-5">
          <h2 className="section-title">👥 Teams <span className="text-white/40 text-sm font-normal">({teams.length})</span></h2>
          <div className="flex gap-2 mb-3">
            <input
              className="input-field flex-1"
              placeholder="Team name..."
              value={newTeam}
              onChange={e => setNewTeam(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && addTeam()}
            />
            <button onClick={addTeam} className="btn-secondary px-3">＋</button>
          </div>
          <div className="space-y-1.5 max-h-60 overflow-y-auto pr-1">
            {teams.map(t => (
              <div key={t} className="flex items-center justify-between py-2 px-3 rounded-lg bg-white/5 text-sm">
                <span className="text-white/80 font-medium">{t}</span>
                <button onClick={() => removeTeam(t)} className="text-red-400/60 hover:text-red-400 text-xs">✕</button>
              </div>
            ))}
          </div>
        </div>

        {/* Stadiums */}
        <div className="glass-card p-5">
          <h2 className="section-title">🏟️ Stadiums <span className="text-white/40 text-sm font-normal">({stadiums.length})</span></h2>
          <div className="space-y-2 mb-3">
            <input className="input-field" placeholder="Stadium name" value={newStadium.name}
              onChange={e => setNewStadium({ ...newStadium, name: e.target.value })} />
            <div className="grid grid-cols-2 gap-2">
              <input className="input-field" placeholder="Latitude" type="number" step="0.0001" value={newStadium.lat}
                onChange={e => setNewStadium({ ...newStadium, lat: e.target.value })} />
              <input className="input-field" placeholder="Longitude" type="number" step="0.0001" value={newStadium.lng}
                onChange={e => setNewStadium({ ...newStadium, lng: e.target.value })} />
            </div>
            <button onClick={addStadium} className="btn-secondary w-full justify-center">＋ Add Stadium</button>
          </div>
          <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
            {stadiums.map(s => (
              <div key={s.name} className="flex items-start justify-between py-2 px-3 rounded-lg bg-white/5">
                <div>
                  <p className="text-sm text-white/80 font-medium">{s.name}</p>
                  <p className="text-xs text-white/40 font-mono">{s.lat.toFixed(4)}, {s.lng.toFixed(4)}</p>
                </div>
                <button onClick={() => removeStadium(s.name)} className="text-red-400/60 hover:text-red-400 text-xs mt-0.5">✕</button>
              </div>
            ))}
          </div>
        </div>

        {/* Rules */}
        <div className="glass-card p-5">
          <h2 className="section-title">📋 Tournament Rules</h2>
          <div className="space-y-4">
            <div>
              <label className="label">Start Date</label>
              <input type="date" className="input-field" value={rules.start_date}
                onChange={e => setRules({ ...rules, start_date: e.target.value })} />
            </div>
            <div>
              <label className="label">End Date</label>
              <input type="date" className="input-field" value={rules.end_date}
                onChange={e => setRules({ ...rules, end_date: e.target.value })} />
            </div>
            <div>
              <label className="label">Daily Time Slots</label>
              <div className="flex gap-2 flex-wrap">
                {['Morning', 'Afternoon', 'Evening'].map(slot => (
                  <button
                    key={slot}
                    onClick={() => toggleSlot(slot)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                      rules.time_slots.includes(slot)
                        ? 'bg-blue-600/40 border border-blue-500/50 text-blue-300'
                        : 'bg-white/5 border border-white/10 text-white/40'
                    }`}
                  >
                    {slot}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="label">Rest Days Between Matches</label>
              <div className="flex items-center gap-3">
                <input type="range" min="0" max="7" value={rules.rest_days_between_matches}
                  onChange={e => setRules({ ...rules, rest_days_between_matches: e.target.value })}
                  className="flex-1 accent-blue-500" />
                <span className="text-white font-bold w-6 text-center">{rules.rest_days_between_matches}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="mt-6 flex flex-wrap gap-4 items-center">
        <button onClick={handleGenerate} disabled={loading} className="btn-primary px-8 py-3.5 text-base">
          {loading ? <><span className="loading-spinner w-4 h-4 border-2"></span> Generating...</> : '🚀 Generate Schedule'}
        </button>
        <button onClick={loadSample} className="btn-secondary">📂 Load Sample Data</button>
        {scheduleData && (
          <>
            <button onClick={() => navigate('/conflict-graph')} className="btn-secondary">🕸️ Conflict Graph</button>
            <button onClick={() => navigate('/tournament-tree')} className="btn-secondary">🏆 Tournament Tree</button>
            <button onClick={() => navigate('/travel-report')} className="btn-secondary">🗺️ Travel Report</button>
            <button onClick={() => navigate('/adjacency-matrix')} className="btn-secondary">📊 Adjacency Matrix</button>
          </>
        )}
      </div>

      {/* Messages */}
      {error && (
        <div className="mt-4 p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-300 text-sm">
          ⚠️ {error}
        </div>
      )}
      {success && (
        <div className="mt-4 p-4 rounded-lg bg-green-500/10 border border-green-500/30 text-green-300 text-sm">
          {success}
        </div>
      )}

      {/* Schedule table preview */}
      {scheduleData?.schedule && (
        <div className="mt-8 glass-card p-5 animate-slide-up">
          <h2 className="section-title">📅 Master Schedule Preview</h2>
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Match</th><th>Team A</th><th>Team B</th><th>Date</th><th>Time Slot</th><th>Stadium</th><th>Slot Group</th>
                </tr>
              </thead>
              <tbody>
                {scheduleData.schedule.slice(0, 15).map((row, i) => (
                  <tr key={i}>
                    <td><span className="badge bg-blue-600/20 text-blue-400">{row.match}</span></td>
                    <td className="font-medium text-white">{row.teamA}</td>
                    <td className="font-medium text-white">{row.teamB}</td>
                    <td className="font-mono text-sm">{row.date}</td>
                    <td>
                      <span className={`badge ${
                        row.time_slot === 'Morning' ? 'bg-yellow-500/20 text-yellow-400' :
                        row.time_slot === 'Afternoon' ? 'bg-orange-500/20 text-orange-400' :
                        'bg-indigo-500/20 text-indigo-400'
                      }`}>{row.time_slot}</span>
                    </td>
                    <td>{row.stadium}</td>
                    <td><span className="badge bg-purple-600/20 text-purple-400">Color {row.color}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
            {scheduleData.schedule.length > 15 && (
              <p className="text-white/30 text-xs mt-2 text-center">
                Showing 15 of {scheduleData.schedule.length} matches.
                <button onClick={() => navigate('/schedule')} className="text-blue-400 ml-1 hover:underline">View all →</button>
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
