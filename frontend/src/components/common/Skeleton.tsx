import clsx from 'clsx';

interface SkeletonProps {
  rows?: number;
  className?: string;
}

export default function Skeleton({ rows = 3, className }: SkeletonProps) {
  return (
    <div className={clsx('space-y-3', className)}>
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="h-12 bg-dark-hover rounded-lg animate-pulse"
          style={{ width: `${100 - i * 5}%` }}
        />
      ))}
    </div>
  );
}
