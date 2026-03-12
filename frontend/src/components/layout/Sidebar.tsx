'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';

const navItems = [
  { label: 'Dashboard', href: '/', icon: '/' },
  { label: 'Projects', href: '/projects', icon: 'P' },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r bg-muted/30 p-4 flex flex-col">
      <div className="mb-8">
        <h1 className="text-lg font-bold">Docs-to-TestCases</h1>
        <p className="text-xs text-muted-foreground">RAG + LLM Test Generator</p>
      </div>
      <nav className="space-y-1">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              'block px-3 py-2 rounded-md text-sm font-medium transition-colors',
              pathname === item.href
                ? 'bg-primary text-primary-foreground'
                : 'hover:bg-muted',
            )}
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
