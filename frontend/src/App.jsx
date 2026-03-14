import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom'
import Home from './pages/Home.jsx'
import Dashboard from './components/Dashboard.jsx'
import ScheduleTable from './components/ScheduleTable.jsx'
import ConflictGraph from './components/ConflictGraph.jsx'
import TournamentTree from './components/TournamentTree.jsx'
import TravelReport from './components/TravelReport.jsx'
import AdjacencyMatrix from './components/AdjacencyMatrix.jsx'

const NAV_ITEMS = [
  { path: '/', label: 'Home', icon: '🏠' },
  { path: '/dashboard', label: 'Schedule Engine', icon: '⚙️' },
  { path: '/conflict-graph', label: 'Conflict Graph', icon: '🕸️' },
  { path: '/tournament-tree', label: 'Tournament Tree', icon: '🏆' },
  { path: '/travel-report', label: 'Travel Optimizer', icon: '🗺️' },
  { path: '/adjacency-matrix', label: 'Adjacency Matrix', icon: '📊' },
]

export default function App() {
  const [scheduleData, setScheduleData] = useState(null)
  const [isNavOpen, setIsNavOpen] = useState(true)

  return (
    <Router>
      <div className="flex min-h-screen">
        {/* Sidebar */}
        <aside className={`${isNavOpen ? 'w-64' : 'w-16'} transition-all duration-300 flex-shrink-0 relative`}>
          <div className="fixed top-0 left-0 h-full glass-card rounded-none border-r border-white/10 overflow-hidden"
               style={{ width: isNavOpen ? '256px' : '64px', transition: 'width 0.3s' }}>
            {/* Logo */}
            <div className="p-4 border-b border-white/10">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center text-lg flex-shrink-0">
                  🎯
                </div>
                {isNavOpen && (
                  <div className="overflow-hidden">
                    <p className="font-bold text-sm text-white leading-tight">Tournament</p>
                    <p className="text-xs text-blue-400">Graph Scheduler</p>
                  </div>
                )}
              </div>
            </div>

            {/* Nav Links */}
            <nav className="p-3 space-y-1">
              {NAV_ITEMS.map(item => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  end={item.path === '/'}
                  className={({ isActive }) => isActive ? 'nav-item-active' : 'nav-item'}
                >
                  <span className="text-lg flex-shrink-0">{item.icon}</span>
                  {isNavOpen && <span className="truncate">{item.label}</span>}
                </NavLink>
              ))}
            </nav>

            {/* Toggle */}
            <button
              onClick={() => setIsNavOpen(!isNavOpen)}
              className="absolute bottom-4 right-3 p-2 rounded-lg bg-white/10 hover:bg-white/20 text-white/60 hover:text-white transition-all"
              title={isNavOpen ? 'Collapse' : 'Expand'}
            >
              {isNavOpen ? '◀' : '▶'}
            </button>
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/dashboard" element={<Dashboard scheduleData={scheduleData} setScheduleData={setScheduleData} />} />
            <Route path="/conflict-graph" element={<ConflictGraph scheduleData={scheduleData} />} />
            <Route path="/tournament-tree" element={<TournamentTree scheduleData={scheduleData} />} />
            <Route path="/travel-report" element={<TravelReport scheduleData={scheduleData} />} />
            <Route path="/adjacency-matrix" element={<AdjacencyMatrix scheduleData={scheduleData} />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}
