import React from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';

export const MetricCard = ({ title, value, unit, icon: Icon, color = "blue", subtext }) => {
    const colorMap = {
        blue: "text-cyan-400 border-cyan-500/30",
        red: "text-rose-400 border-rose-500/30",
        green: "text-emerald-400 border-emerald-500/30",
        amber: "text-amber-400 border-amber-500/30",
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className={clsx("glass-card p-6 flex flex-col justify-between h-32", colorMap[color])}
        >
            <div className="flex justify-between items-start">
                <span className="text-gray-400 text-sm font-medium uppercase tracking-wider">{title}</span>
                {Icon && <Icon className="w-5 h-5 opacity-80" />}
            </div>
            <div>
                <div className="flex items-baseline gap-1">
                    <span className="text-3xl font-bold text-white tracking-tight">{value}</span>
                    {unit && <span className="text-sm text-gray-500">{unit}</span>}
                </div>
                {subtext && <div className="text-xs text-gray-500 mt-1">{subtext}</div>}
            </div>
        </motion.div>
    );
};
