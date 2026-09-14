import React from 'react';

interface ProgressBarProps {
  total: number;
  success: number;
  failed: number;
  showLabels?: boolean;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  total,
  success,
  failed,
  showLabels = true,
}) => {
  if (total <= 0) {
    return (
      <div className="w-full">
        <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
          <div className="bg-slate-300 h-2.5 rounded-full" style={{ width: '0%' }} />
        </div>
        {showLabels && (
          <div className="flex justify-between text-xs text-slate-500 mt-1">
            <span>0 адресатов</span>
            <span>0%</span>
          </div>
        )}
      </div>
    );
  }

  const successPct = Math.min(100, Math.round((success / total) * 100));
  const failedPct = Math.min(100 - successPct, Math.round((failed / total) * 100));
  const totalCompletedPct = Math.min(100, successPct + failedPct);

  return (
    <div className="w-full">
      <div className="w-full bg-slate-100 rounded-full h-2.5 flex overflow-hidden">
        <div
          className="bg-emerald-500 h-2.5 transition-all duration-500"
          style={{ width: `${successPct}%` }}
          title={`Успешно: ${success} (${successPct}%)`}
        />
        <div
          className="bg-rose-500 h-2.5 transition-all duration-500"
          style={{ width: `${failedPct}%` }}
          title={`Ошибки: ${failed} (${failedPct}%)`}
        />
      </div>
      {showLabels && (
        <div className="flex justify-between text-xs text-slate-500 mt-1">
          <span>
            {success + failed} из {total} ({totalCompletedPct}%)
          </span>
          <span className="flex space-x-2">
            <span className="text-emerald-600 font-medium">✓ {success}</span>
            {failed > 0 && <span className="text-rose-600 font-medium">✗ {failed}</span>}
          </span>
        </div>
      )}
    </div>
  );
};
