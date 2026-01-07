import React from 'react';
import clsx from 'clsx';
import { ArrowUpRight, ArrowDownLeft } from 'lucide-react';

export const StatCard = ({ title, value, unit, icon: Icon, trend, color = "indigo" }) => {
    const colors = {
        indigo: "from-indigo-500/10 to-indigo-500/5 border-indigo-500/20 text-indigo-400",
        rose: "from-rose-500/10 to-rose-500/5 border-rose-500/20 text-rose-400",
        emerald: "from-emerald-500/10 to-emerald-500/5 border-emerald-500/20 text-emerald-400",
        amber: "from-amber-500/10 to-amber-500/5 border-amber-500/20 text-amber-400",
        slate: "from-slate-800/50 to-slate-800/30 border-slate-700 text-slate-400",
    };

    return (
        <div className={clsx(
            "relative overflow-hidden rounded-lg border bg-gradient-to-br p-5 transition-all duration-200 hover:border-slate-600",
            colors[color] || colors.slate,
            color === 'slate' ? 'bg-slate-900' : ''
        )}>
            <div className="flex justify-between items-start mb-4">
                <div className="p-2 rounded-md bg-slate-950/30 ring-1 ring-white/5">
                    {Icon && <Icon className="w-5 h-5 opacity-90" />}
                </div>
                {trend && (
                    <div className={clsx("flex items-center text-xs font-medium", trend > 0 ? "text-emerald-400" : "text-rose-400")}>
                        {trend > 0 ? "+" : ""}{trend}%
                    </div>
                )}
            </div>

            <div>
                <h3 className="text-sm font-medium text-slate-400">{title}</h3>
                <div className="mt-1 flex items-baseline gap-1">
                    <span className="text-2xl font-semibold text-slate-100 tracking-tight">{value}</span>
                    {unit && <span className="text-sm font-medium text-slate-500">{unit}</span>}
                </div>
            </div>
        </div>
    );
};
