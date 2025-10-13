import { NavLink } from 'react-router-dom';

const navigation = [
  { name: 'Dashboard', href: '/app/dashboard', icon: '📊' },
  { name: 'Properties', href: '/app/properties', icon: '🏠' },
  { name: 'Booking Requests', href: '/app/booking-requests', icon: '📨' },
  { name: 'Tasks', href: '/app/tasks', icon: '✓' },
  { name: 'Calendar', href: '/app/calendar', icon: '📅' },
  { name: 'Cleaning Sessions', href: '/app/cleaning', icon: '🧹' },
  { name: 'Financial', href: '/app/financial', icon: '💰' },
  { name: 'Inventory', href: '/app/inventory/items', icon: '📦' },
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
