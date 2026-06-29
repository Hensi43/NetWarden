import React from 'react';
import clsx from 'clsx';
import { ArrowUpRight, ArrowDownLeft } from 'lucide-react';

export const StatCard = ({ title, value, unit, icon: Icon, trend, color = "indigo" }) => {
    const colors = {
        indigo: "from-indigo-500/10 to-indigo-500/5 border-indigo-500/20 text-indigo-600",
        rose: "from-rose-500/10 to-rose-500/5 border-rose-500/20 text-rose-600",
        emerald: "from-emerald-500/10 to-emerald-500/5 border-emerald-500/20 text-emerald-600",
        amber: "from-amber-500/10 to-amber-500/5 border-amber-500/20 text-amber-600",
        slate: "from-slate-100 to-slate-50 border-slate-200 text-slate-600",
    };

    return (
        <div className={clsx(
            "relative overflow-hidden rounded-lg border bg-gradient-to-br p-5 transition-all duration-200 hover:border-slate-300",
            colors[color] || colors.slate,
            color === 'slate' ? 'bg-white' : ''
        )}>
            <div className="flex justify-between items-start mb-4">
                <div className="p-2 rounded-md bg-white/50 ring-1 ring-slate-200">
                    {Icon && <Icon className="w-5 h-5 opacity-90" />}
                </div>
                {trend && (
                    <div className={clsx("flex items-center text-xs font-medium", trend > 0 ? "text-emerald-600" : "text-rose-600")}>
                        {trend > 0 ? "+" : ""}{trend}%
                    </div>
                )}
            </div>

            <div>
                <h3 className="text-sm font-medium text-slate-600">{title}</h3>
                <div className="mt-1 flex items-baseline gap-1">
                    <span className="text-2xl font-semibold text-slate-900 tracking-tight">{value}</span>
                    {unit && <span className="text-sm font-medium text-slate-500">{unit}</span>}
                </div>
            </div>
        </div>
    );
};
