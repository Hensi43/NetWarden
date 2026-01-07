import React, { useState } from 'react';
import {
    LayoutDashboard,
    Settings,
    Activity,
    ShieldAlert,
    Network,
    LogOut,
    ChevronLeft,
    Search
} from 'lucide-react';
import clsx from 'clsx';

export const Sidebar = ({ activeTab, onTabChange }) => {
    const [collapsed, setCollapsed] = useState(false);

    const navItems = [
        { id: 'dashboard', icon: LayoutDashboard, label: 'Dashboard' },
        { id: 'topology', icon: Network, label: 'Topology' },
        { id: 'rules', icon: ShieldAlert, label: 'Rules & Policies' },
        { id: 'settings', icon: Settings, label: 'Settings' },
    ];

    return (
        <div className={clsx(
            "flex flex-col border-r border-slate-800 bg-slate-950 transition-all duration-300",
            collapsed ? "w-16" : "w-64"
        )}>
            {/* Logo Area */}
            <div className="h-16 flex items-center px-4 border-b border-slate-800">
                <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center shrink-0">
                    <Activity className="text-white w-5 h-5" />
                </div>
                {!collapsed && (
                    <div className="ml-3 font-semibold text-slate-100 tracking-tight">
                        NetWarden <span className="text-indigo-500">Pro</span>
                    </div>
                )}
            </div>

            {/* Navigation */}
            <div className="flex-1 py-6 px-2 space-y-1">
                {navItems.map((item) => (
                    <button
                        key={item.id}
                        onClick={() => onTabChange(item.id)}
                        className={clsx(
                            "w-full flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors group",
                            activeTab === item.id
                                ? "bg-indigo-500/10 text-indigo-400"
                                : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
                        )}
                    >
                        <item.icon className={clsx("w-5 h-5 shrink-0", activeTab === item.id ? "text-indigo-400" : "text-slate-500 group-hover:text-slate-300")} />
                        {!collapsed && <span className="ml-3">{item.label}</span>}
                        {collapsed && activeTab === item.id && (
                            <div className="absolute left-16 px-2 py-1 bg-slate-800 text-xs text-white rounded shadow-md ml-2 z-50">
                                {item.label}
                            </div>
                        )}
                    </button>
                ))}
            </div>

            {/* Bottom Actions */}
            <div className="p-4 border-t border-slate-800">
                <button
                    onClick={() => setCollapsed(!collapsed)}
                    className="flex items-center justify-center w-full p-2 text-slate-500 hover:text-slate-300 transition-colors"
                    title="Toggle Sidebar"
                >
                    <ChevronLeft className={clsx("w-5 h-5 transition-transform", collapsed && "rotate-180")} />
                </button>
            </div>
        </div>
    );
};
