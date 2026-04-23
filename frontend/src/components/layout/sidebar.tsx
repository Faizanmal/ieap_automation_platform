'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  Brain,
  Target,
  GitBranch,
  Cpu,
  ListTodo,
  BarChart3,
  Activity,
  Webhook,
  Settings,
  Shield,
  Users,
  ChevronLeft,
  ChevronRight,
  Server,
  Zap,
} from 'lucide-react';
import { useState } from 'react';
import { Button } from '@/components/ui/button';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Real-time', href: '/dashboard/realtime', icon: Zap },
  { name: 'ML Models', href: '/dashboard/models', icon: Brain },
  { name: 'Predictions', href: '/dashboard/predictions', icon: Target },
  { name: 'Pipelines', href: '/dashboard/pipelines', icon: GitBranch },
  { name: 'Decisions', href: '/dashboard/decisions', icon: Cpu },
  { name: 'Tasks', href: '/dashboard/tasks', icon: ListTodo },
  { name: 'Analytics', href: '/dashboard/analytics', icon: BarChart3 },
  { name: 'Health', href: '/dashboard/health', icon: Activity },
  { name: 'Webhooks', href: '/dashboard/webhooks', icon: Webhook },
];

const adminNavigation = [
  { name: 'Admin', href: '/dashboard/admin', icon: Shield },
  { name: 'Users', href: '/dashboard/admin/users', icon: Users },
  { name: 'System', href: '/dashboard/admin/system', icon: Server },
  { name: 'Settings', href: '/dashboard/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        'flex flex-col border-r border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950 transition-all duration-300',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Logo */}
      <div className="flex h-16 items-center justify-between border-b border-zinc-200 px-4 dark:border-zinc-800">
        {!collapsed && (
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-900 dark:bg-zinc-50">
              <Cpu className="h-5 w-5 text-white dark:text-zinc-900" />
            </div>
            <span className="font-semibold text-zinc-900 dark:text-zinc-50">IEAP</span>
          </Link>
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setCollapsed(!collapsed)}
          className="h-8 w-8"
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-4">
        <div className="space-y-1">
          {navigation.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(`${item.href  }/`);
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-zinc-100 text-zinc-900 dark:bg-zinc-800 dark:text-zinc-50'
                    : 'text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-800/50 dark:hover:text-zinc-50'
                )}
              >
                <item.icon className="h-5 w-5 shrink-0" />
                {!collapsed && <span>{item.name}</span>}
              </Link>
            );
          })}
        </div>

        <div className="mt-8">
          {!collapsed && (
            <h3 className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-zinc-500">
              Administration
            </h3>
          )}
          <div className="space-y-1">
            {adminNavigation.map((item) => {
              const isActive = pathname === item.href || pathname.startsWith(`${item.href  }/`);
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-zinc-100 text-zinc-900 dark:bg-zinc-800 dark:text-zinc-50'
                      : 'text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-800/50 dark:hover:text-zinc-50'
                  )}
                >
                  <item.icon className="h-5 w-5 shrink-0" />
                  {!collapsed && <span>{item.name}</span>}
                </Link>
              );
            })}
          </div>
        </div>
      </nav>

      {/* Version */}
      {!collapsed && (
        <div className="border-t border-zinc-200 p-4 dark:border-zinc-800">
          <p className="text-xs text-zinc-500">IEAP v2.0.0</p>
        </div>
      )}
    </aside>
  );
}
