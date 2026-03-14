import { useNavigate } from 'react-router-dom'

const FEATURES = [
  { icon: '🕸️', title: 'Welsh-Powell Coloring', desc: 'Exact graph coloring algorithm to find the chromatic number χ(G) — the minimum number of time slots required.' },
  { icon: '🗺️', title: "Dijkstra's Algorithm", desc: 'Shortest-path travel optimization across stadium spatial graph using haversine distance weights.' },
  { icon: '⚔️', title: 'Conflict Graph G=(V,E)', desc: 'Vertices = matches, edges = same-team / stadium / rest-day conflicts. Guarantees zero scheduling conflicts.' },
  { icon: '🏆', title: 'Knockout Tree', desc: 'Directed rooted tournament tree for bracket visualization with single-elimination progression.' },
  { icon: '📊', title: 'Adjacency Matrix', desc: 'Visual heatmap of the conflict graph adjacency matrix for faculty demonstration.' },
  { icon: '📅', title: 'Master Schedule', desc: 'Full match schedule with team, stadium, date and time slot — respecting all constraints.' },
]

const ALGORITHM_STEPS = [
  { n: '01', title: 'Load Input', desc: 'Teams, stadiums (lat/lng), tournament dates, rest-day rules' },
  { n: '02', title: 'Generate Matches', desc: 'All C(n,2) round-robin match pairs form vertex set V' },
  { n: '03', title: 'Build Conflict Graph', desc: 'Add edges for same-team, stadium, and rest-day conflicts' },
  { n: '04', title: 'Welsh-Powell Coloring', desc: 'Sort by degree ↓, assign min color; χ(G) = time slots needed' },
  { n: '05', title: 'Assign Slots & Stadiums', desc: 'Map colors → (date, slot), rotate stadiums per slot' },
  { n: '06', title: 'Dijkstra Travel Routes', desc: 'Shortest stadium-to-stadium paths; total km per team' },
  { n: '07', title: 'Visualize Results', desc: 'Force graph, bracket tree, heatmap, schedule table' },
]

export default function Home() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen p-8 animate-fade-in">
      {/* Hero */}
      <div className="max-w-5xl mx-auto text-center mb-16">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-600/20 border border-blue-500/30 text-blue-300 text-sm font-medium mb-6">
          <span>🎓</span> Final Year Project — Graph Theory Application
        </div>
        <h1 className="text-5xl font-black mb-4 leading-tight">
          <span className="bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 bg-clip-text text-transparent">
            Tournament Scheduling
          </span>
          <br />
          <span className="text-white">via Graph Theory</span>
        </h1>
        <p className="text-white/60 text-xl max-w-3xl mx-auto leading-relaxed mb-8">
          A constraint-based multi-stadium sports tournament scheduler that models scheduling as a 
          <strong className="text-white/80"> Dynamic Conflict Graph</strong> and solves it using exact 
          <strong className="text-white/80"> Welsh-Powell graph coloring</strong> and 
          <strong className="text-white/80"> Dijkstra's shortest path</strong> algorithms.
        </p>
        <div className="flex flex-wrap gap-4 justify-center">
          <button onClick={() => navigate('/dashboard')} className="btn-primary text-base px-8 py-4">
            ⚙️ Open Schedule Engine
          </button>
          <button onClick={() => navigate('/conflict-graph')} className="btn-secondary text-base px-8 py-4">
            🕸️ View Conflict Graph
          </button>
        </div>
      </div>

      {/* Algorithm Flow */}
      <div className="max-w-5xl mx-auto mb-16">
        <h2 className="text-2xl font-bold text-white text-center mb-8">Algorithm Pipeline</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
          {ALGORITHM_STEPS.map((step, i) => (
            <div key={i} className="glass-card p-3 text-center group hover:border-blue-500/30 transition-all">
              <div className="text-xs font-mono text-blue-400 mb-1">{step.n}</div>
              <div className="text-xs font-bold text-white mb-1 leading-tight">{step.title}</div>
              <div className="text-xs text-white/40 leading-tight hidden group-hover:block">{step.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Feature Cards */}
      <div className="max-w-5xl mx-auto mb-16">
        <h2 className="text-2xl font-bold text-white text-center mb-8">Core Features</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {FEATURES.map((f, i) => (
            <div key={i} className="glass-card-hover p-6">
              <div className="text-3xl mb-3">{f.icon}</div>
              <h3 className="font-bold text-white mb-2">{f.title}</h3>
              <p className="text-white/50 text-sm leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Tech Stack */}
      <div className="max-w-5xl mx-auto">
        <div className="glass-card p-6">
          <h2 className="text-lg font-bold text-white mb-4 text-center">Technology Stack</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            {[
              { label: 'Frontend', items: ['React 18', 'Vite', 'TailwindCSS', 'D3.js'] },
              { label: 'Backend', items: ['Python 3.11+', 'FastAPI', 'NetworkX', 'NumPy'] },
              { label: 'Graph Theory', items: ['Welsh-Powell', "Dijkstra's", 'Tournament Tree', 'Adjacency Matrix'] },
              { label: 'Visualization', items: ['D3 Force Graph', 'SVG Bracket', 'Heatmap', 'Recharts'] },
            ].map((cat, i) => (
              <div key={i}>
                <p className="text-xs font-semibold text-blue-400 uppercase tracking-wider mb-2">{cat.label}</p>
                {cat.items.map(item => (
                  <p key={item} className="text-sm text-white/60 py-0.5">{item}</p>
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
