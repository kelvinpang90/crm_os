import { useState, useEffect } from 'react';

type Breakpoint = 'sm' | 'md' | 'lg';

export function useBreakpoint(): Breakpoint {
  const getBreakpoint = (): Breakpoint => {
    if (typeof window === 'undefined') return 'lg';
    const w = window.innerWidth;
    if (w < 768) return 'sm';
    if (w < 1024) return 'md';
    return 'lg';
  };

  const [breakpoint, setBreakpoint] = useState<Breakpoint>(getBreakpoint);

  useEffect(() => {
    const handleResize = () => setBreakpoint(getBreakpoint());
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return breakpoint;
}

export function useIsMobile() {
  return useBreakpoint() === 'sm';
}
