'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const navigation = [
  { name: 'Dashboard', href: '/', icon: '📊' },
  { name: 'Budgets', href: '/budgets', icon: '💰' },
  { name: 'Contrats', href: '/contracts', icon: '📄' },
  { name: 'Trésorerie', href: '/cashflow', icon: '💹' },
  { name: 'Simulations', href: '/simulations', icon: '🧪' },
  { name: 'Recommandations', href: '/recommendations', icon: '💡' },
  { name: 'Documents', href: '/documents', icon: '📁' },
  { name: 'Recherche IA', href: '/search', icon: '🔍' },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-full w-64 bg-gray-900 text-white flex flex-col z-50">
      {/* Logo */}
      <div className="p-6 border-b border-gray-700">
        <h1 className="text-xl font-bold">
          <span className="text-blue-400">F360</span>
        </h1>
        <p className="text-xs text-gray-400 mt-1">Financial Command Center</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 space-y-1 px-3">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              }`}
            >
              <span className="text-lg">{item.icon}</span>
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-700">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-sm font-bold">
            A
          </div>
          <div>
            <p className="text-sm font-medium">Admin</p>
            <p className="text-xs text-gray-400">analyst</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
