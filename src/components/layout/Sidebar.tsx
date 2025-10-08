import { NavLink } from 'react-router-dom';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: '📊' },
  { name: 'Properties', href: '/properties', icon: '🏠' },
  { name: 'Tasks', href: '/tasks', icon: '✓' },
  { name: 'Calendar', href: '/calendar', icon: '📅' },
  { name: 'Cleaning Sessions', href: '/cleaning', icon: '🧹' },
];

export function Sidebar() {
  return (
    <aside className="w-64 bg-gray-50 border-r border-gray-200 min-h-[calc(100vh-4rem)]">
      <nav className="px-4 py-6 space-y-1">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-gray-700 hover:bg-gray-100'
              }`
            }
          >
            <span className="text-lg">{item.icon}</span>
            {item.name}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
