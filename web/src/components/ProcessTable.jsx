import React, { useState } from 'react';
import { Shield, ArrowDown, ArrowUp, Filter, Search } from 'lucide-react';
import clsx from 'clsx';

export const ProcessTable = ({ processes }) => {
    const [filter, setFilter] = useState('');

    const filteredProcesses = processes.filter(p =>
        p.name.toLowerCase().includes(filter.toLowerCase()) ||
        String(p.pid).includes(filter)
    );

    return (
        <div className="flex flex-col h-full bg-slate-900 border border-slate-800 rounded-lg shadow-sm overflow-hidden">
            {/* Table Header / Toolbar */}
            <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
                <h3 className="font-semibold text-slate-200 text-sm">Active Processes</h3>

                <div className="flex items-center gap-2">
                    <div className="relative">
                        <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
                        <input
                            type="text"
                            placeholder="Filter..."
                            className="h-8 pl-8 pr-3 text-xs bg-slate-950 border border-slate-700 rounded-md focus:outline-none focus:border-indigo-500 text-slate-300 w-40 transition-colors"
                            value={filter}
                            onChange={(e) => setFilter(e.target.value)}
                        />
                    </div>
                    <button className="h-8 w-8 flex items-center justify-center rounded-md border border-slate-700 bg-slate-950 hover:bg-slate-800 text-slate-400">
                        <Filter className="w-3.5 h-3.5" />
                    </button>
                </div>
            </div>

            {/* Table Content */}
            <div className="flex-1 overflow-auto">
                <table className="w-full text-left border-collapse">
                    <thead className="bg-slate-950/50 sticky top-0 z-10 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                        <tr>
                            <th className="px-4 py-3 border-b border-slate-800">Process Info</th>
                            <th className="px-4 py-3 border-b border-slate-800 text-right">Download</th>
                            <th className="px-4 py-3 border-b border-slate-800 text-right">Upload</th>
                            <th className="px-4 py-3 border-b border-slate-800 text-center">Priority</th>
                            <th className="px-4 py-3 border-b border-slate-800 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/50">
                        {filteredProcesses.map((proc) => (
                            <ProcessRow key={proc.pid} proc={proc} />
                        ))}
                        {filteredProcesses.length === 0 && (
                            <tr>
                                <td colSpan="5" className="px-4 py-8 text-center text-slate-500 text-sm">
                                    No processes found.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {/* Footer */}
            <div className="px-4 py-2 border-t border-slate-800 bg-slate-950/30 text-xs text-slate-500 flex justify-between">
                <span>In-Scope: {filteredProcesses.length}</span>
                <span>Total Bandwidth: {filteredProcesses.reduce((acc, p) => acc + p.mbps, 0).toFixed(2)} Mbps</span>
            </div>
        </div>
    );
};

const ProcessRow = ({ proc }) => {
    return (
        <tr className={clsx(
            "group hover:bg-slate-800/40 transition-colors text-sm",
            proc.penalized && "bg-rose-500/5 hover:bg-rose-500/10"
        )}>
            <td className="px-4 py-2.5">
                <div className="flex flex-col">
                    <span className="font-medium text-slate-200 flex items-center gap-2">
                        {proc.name}
                        {proc.penalized && <Shield className="w-3 h-3 text-rose-500 animate-pulse" />}
                    </span>
                    <span className="text-xs text-slate-500 font-mono">PID: {proc.pid}</span>
                </div>
            </td>
            <td className="px-4 py-2.5 text-right tabular-nums text-slate-300">
                {formatBytes(proc.download_rate)}/s
            </td>
            <td className="px-4 py-2.5 text-right tabular-nums text-slate-300">
                {formatBytes(proc.upload_rate)}/s
            </td>
            <td className="px-4 py-2.5 text-center">
                <Badge category={proc.category} />
            </td>
            <td className="px-4 py-2.5 text-right">
                <button className="text-xs px-2 py-1 rounded border border-slate-700 hover:bg-slate-700 text-slate-400">
                    Details
                </button>
            </td>
        </tr>
    )
}

const Badge = ({ category }) => {
    const styles = {
        high: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
        medium: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
        low: "bg-slate-500/10 text-slate-400 border-slate-500/20"
    };

    return (
        <span className={clsx("inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium border uppercase tracking-wide", styles[category] || styles.low)}>
            {category}
        </span>
    );
};

const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};
