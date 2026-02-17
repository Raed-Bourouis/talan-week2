interface KPICardProps {
  title: string;
  value: string;
  change: number;
  trend: 'up' | 'down';
  subtitle: string;
}

export default function KPICard({
  title,
  value,
  change,
  trend,
  subtitle,
}: KPICardProps) {
  const isPositive = trend === 'up';

  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-gray-500">{title}</p>
        <span
          className={`inline-flex items-center text-xs font-medium ${
            isPositive ? 'text-green-600' : 'text-red-600'
          }`}
        >
          {isPositive ? '▲' : '▼'} {Math.abs(change)}%
        </span>
      </div>
      <p className="mt-2 text-2xl font-bold text-gray-900">{value}</p>
      <p className="mt-1 text-xs text-gray-400">{subtitle}</p>
    </div>
  );
}
