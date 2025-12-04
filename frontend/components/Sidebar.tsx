'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import {
  LayoutDashboard,
  Activity,
  Upload,
  Database,
  Settings,
  ChevronLeft,
  ChevronRight,
  Shield,
  AlertCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';

interface NavItem {
  title: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
  badgeVariant?: 'default' | 'destructive' | 'outline' | 'secondary';
}

const navItems: NavItem[] = [
  {
    title: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
  },
  {
    title: 'Real-time Monitor',
    href: '/realtime',
    icon: Activity,
    badge: 'LIVE',
    badgeVariant: 'destructive',
  },
  {
    title: 'Upload & Analyze',
    href: '/',
    icon: Upload,
  },
  {
    title: 'Model Management',
    href: '/models',
    icon: Database,
  },
  {
    title: 'Settings',
    href: '/settings',
    icon: Settings,
  },
];

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();

  return (
    <div
      className={cn(
        'relative flex h-screen flex-col border-r border-border bg-card transition-all duration-300',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Logo/Brand */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-border">
        {!collapsed && (
          <Link href="/dashboard" className="flex items-center space-x-2">
            <Shield className="h-8 w-8 text-primary animate-pulse-glow" />
            <div className="flex flex-col">
              <span className="text-lg font-bold text-gradient-cyan">
                AI Shield
              </span>
              <span className="text-xs text-muted-foreground">
                Threat Detection
              </span>
            </div>
          </Link>
        )}
        {collapsed && (
          <Shield className="h-6 w-6 text-primary animate-pulse-glow mx-auto" />
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-2 py-4 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;

          return (
            <Link key={item.href} href={item.href}>
              <Button
                variant={isActive ? 'secondary' : 'ghost'}
                className={cn(
                  'w-full justify-start transition-all duration-200',
                  collapsed ? 'px-2' : 'px-3',
                  isActive &&
                    'bg-primary/10 text-primary border-l-2 border-primary shadow-glow'
                )}
              >
                <Icon
                  className={cn(
                    'h-5 w-5',
                    collapsed ? 'mx-auto' : 'mr-3',
                    isActive && 'text-primary'
                  )}
                />
                {!collapsed && (
                  <span className="flex-1 text-left">{item.title}</span>
                )}
                {!collapsed && item.badge && (
                  <Badge
                    variant={item.badgeVariant || 'default'}
                    className="ml-auto text-[10px] px-1.5 py-0 animate-pulse"
                  >
                    {item.badge}
                  </Badge>
                )}
              </Button>
            </Link>
          );
        })}
      </nav>

      {/* Status Section */}
      {!collapsed && (
        <>
          <Separator />
          <div className="p-4 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">System Status</span>
              <div className="flex items-center space-x-1">
                <div className="h-2 w-2 rounded-full bg-status-safe animate-pulse-glow" />
                <span className="text-status-safe font-medium">Online</span>
              </div>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Active Threats</span>
              <span className="font-mono font-bold text-destructive">0</span>
            </div>
          </div>
        </>
      )}

      {/* Collapse Toggle */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setCollapsed(!collapsed)}
        className="absolute -right-3 top-20 h-6 w-6 rounded-full border border-border bg-card p-0 shadow-md hover:shadow-glow"
      >
        {collapsed ? (
          <ChevronRight className="h-4 w-4" />
        ) : (
          <ChevronLeft className="h-4 w-4" />
        )}
      </Button>

      {/* Footer */}
      {!collapsed && (
        <>
          <Separator />
          <div className="p-3">
            <div className="flex items-center space-x-2 rounded-lg bg-muted/50 p-2">
              <AlertCircle className="h-4 w-4 text-muted-foreground" />
              <div className="flex-1 text-xs text-muted-foreground">
                <p className="font-medium">POC Version</p>
                <p className="text-[10px]">v1.0.0</p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
