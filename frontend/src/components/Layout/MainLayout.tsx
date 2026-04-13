import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import Sidebar from './Sidebar';
import BottomTabBar from './BottomTabBar';
import clsx from 'clsx';

export default function MainLayout() {
  const breakpoint = useBreakpoint();
  const [collapsed, setCollapsed] = useState(breakpoint === 'md');

  const isMobile = breakpoint === 'sm';

  return (
    <div className="min-h-screen bg-dark-bg">
      {!isMobile && (
        <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />
      )}

      <main
        className={clsx(
          'min-h-screen transition-all duration-300',
          isMobile ? 'pb-16' : collapsed ? 'ml-16' : 'ml-60'
        )}
      >
        <div className="p-4 lg:p-6">
          <Outlet />
        </div>
      </main>

      {isMobile && <BottomTabBar />}
    </div>
  );
}
