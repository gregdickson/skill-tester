import { Outlet, Link, useLocation } from 'react-router-dom'

const navItems = [
  { path: '/networks', label: 'Networks', icon: '⊞' },
]

export default function Layout() {
  const location = useLocation()

  return (
    <div className="flex h-screen bg-bg-primary text-white">
      {/* Sidebar */}
      <aside className="w-56 border-r border-border-subtle bg-bg-secondary flex flex-col">
        <div className="p-4 border-b border-border-subtle">
          <h1 className="text-lg font-bold text-accent-green">MicroGrad</h1>
          <p className="text-xs text-gray-500">Skill Optimiser</p>
        </div>
        <nav className="flex-1 p-2">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-2 px-3 py-2 rounded text-sm ${
                location.pathname.startsWith(item.path)
                  ? 'bg-bg-hover text-accent-green'
                  : 'text-gray-400 hover:bg-bg-hover hover:text-white'
              }`}
            >
              <span>{item.icon}</span>
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="p-3 border-t border-border-subtle text-xs text-gray-600">
          v0.1.0
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
