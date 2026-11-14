import React, { useState } from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  TrendingUp,
  Users,
  Lightbulb,
  BarChart3,
  Database,
  FileText,
  BookmarkCheck,
  LogOut,
  Menu,
  X,
  Building,
  ChevronDown,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { cn } from "../../lib/utils";

const navigationItems = [
  { name: "Overview", href: "/app", icon: LayoutDashboard },
  { name: "Trend Explorer", href: "/app/trends", icon: TrendingUp },
  { name: "Audience Insights", href: "/app/audiences", icon: Users },
  { name: "Opportunity Briefs", href: "/app/opportunities", icon: Lightbulb },
  { name: "Campaign Analytics", href: "/app/campaigns", icon: BarChart3 },
  { name: "Saved Board", href: "/app/saved", icon: BookmarkCheck },
  { name: "Reports & Export", href: "/app/reports", icon: FileText },
  { name: "Data Sources", href: "/app/sources", icon: Database },
];

export function AppLayout() {
  const { user, currentWorkspace, workspaces, logout, setCurrentWorkspace } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [workspaceDropdownOpen, setWorkspaceDropdownOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col md:flex-row">
      {/* Mobile Header */}
      <header className="md:hidden flex items-center justify-between px-4 py-3 bg-white border-b border-slate-200 sticky top-0 z-40 no-print">
        <Link to="/app" className="flex items-center gap-2 font-bold text-slate-900 tracking-tight">
          <span className="h-7 w-7 rounded-lg bg-indigo-600 text-white flex items-center justify-center font-black text-sm">
            DE
          </span>
          <span className="text-base font-semibold">Ecosystem Intel</span>
        </Link>
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-1.5 rounded-md text-slate-600 hover:bg-slate-100"
          aria-label="Toggle Navigation"
        >
          {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </header>

      {/* Mobile Drawer Navigation */}
      {mobileMenuOpen && (
        <div className="md:hidden fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm no-print">
          <div className="fixed inset-y-0 left-0 w-3/4 max-w-xs bg-white p-6 shadow-xl flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-4 border-b border-slate-200">
                <span className="font-bold text-slate-900">Ecosystem Intelligence</span>
                <button
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-1 rounded-md text-slate-400 hover:text-slate-600"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Workspace Switcher Mobile */}
              <div className="my-4 p-3 bg-slate-50 rounded-lg border border-slate-200">
                <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
                  <Building className="h-3.5 w-3.5" /> Workspace
                </div>
                <div className="font-medium text-slate-900 text-sm truncate">
                  {currentWorkspace?.name || "Default Workspace"}
                </div>
                <div className="text-xs text-slate-500 mt-0.5">
                  {currentWorkspace?.market_region || "IN"} • {currentWorkspace?.default_currency || "INR"}
                </div>
              </div>

              <nav className="space-y-1">
                {navigationItems.map((item) => (
                  <NavLink
                    key={item.name}
                    to={item.href}
                    end={item.href === "/app"}
                    onClick={() => setMobileMenuOpen(false)}
                    className={({ isActive }) =>
                      cn(
                        "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition",
                        isActive
                          ? "bg-indigo-50 text-indigo-700"
                          : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                      )
                    }
                  >
                    <item.icon className="h-4 w-4" />
                    {item.name}
                  </NavLink>
                ))}
              </nav>
            </div>

            <div className="pt-4 border-t border-slate-200">
              <div className="text-xs font-medium text-slate-500 mb-1">{user?.email}</div>
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 text-sm text-rose-600 hover:text-rose-700 font-medium py-1"
              >
                <LogOut className="h-4 w-4" /> Sign out
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Desktop Persistent Left Sidebar */}
      <aside className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0 bg-white border-r border-slate-200 z-30 no-print">
        <div className="flex flex-col flex-grow pt-5 pb-4 overflow-y-auto">
          {/* Brand Header */}
          <div className="flex items-center gap-2.5 px-6 pb-5 border-b border-slate-100">
            <span className="h-8 w-8 rounded-lg bg-indigo-600 text-white flex items-center justify-center font-bold text-sm shadow-sm">
              DE
            </span>
            <div>
              <h1 className="text-sm font-bold text-slate-900 leading-tight">Digital Ecosystem</h1>
              <span className="text-[11px] text-slate-500 font-medium tracking-tight">Intelligence Platform</span>
            </div>
          </div>

          {/* Workspace Switcher */}
          <div className="px-4 py-3 border-b border-slate-100 relative">
            <button
              onClick={() => setWorkspaceDropdownOpen(!workspaceDropdownOpen)}
              className="w-full flex items-center justify-between p-2 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-200 text-left transition"
            >
              <div className="truncate">
                <div className="text-[10px] font-semibold tracking-wider text-slate-400 uppercase">
                  Active Workspace
                </div>
                <div className="text-xs font-bold text-slate-800 truncate">
                  {currentWorkspace?.name || "Demo D2C Workspace"}
                </div>
              </div>
              <ChevronDown className="h-4 w-4 text-slate-400 ml-1 shrink-0" />
            </button>

            {workspaceDropdownOpen && (
              <div className="absolute left-4 right-4 mt-1 bg-white border border-slate-200 rounded-lg shadow-lg py-1 z-50 animate-in fade-in">
                {workspaces.map((ws) => (
                  <button
                    key={ws.id}
                    onClick={() => {
                      setCurrentWorkspace(ws);
                      setWorkspaceDropdownOpen(false);
                    }}
                    className={cn(
                      "w-full text-left px-3 py-1.5 text-xs hover:bg-slate-50 flex items-center justify-between",
                      currentWorkspace?.id === ws.id ? "font-bold text-indigo-600 bg-indigo-50/50" : "text-slate-700"
                    )}
                  >
                    <span className="truncate">{ws.name}</span>
                    <span className="text-[10px] text-slate-400 font-normal">{ws.market_region}</span>
                  </button>
                ))}
                <div className="border-t border-slate-100 mt-1 pt-1">
                  <Link
                    to="/onboarding"
                    onClick={() => setWorkspaceDropdownOpen(false)}
                    className="block px-3 py-1.5 text-xs text-indigo-600 hover:bg-slate-50 font-medium"
                  >
                    + Configure Workspace
                  </Link>
                </div>
              </div>
            )}
          </div>

          {/* Main Navigation Links */}
          <nav className="mt-4 flex-1 px-3 space-y-1">
            <div className="px-3 pb-1 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              Navigation
            </div>
            {navigationItems.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                end={item.href === "/app"}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-semibold transition-all duration-150",
                    isActive
                      ? "bg-indigo-600 text-white shadow-sm"
                      : "text-slate-600 hover:bg-slate-100/80 hover:text-slate-900"
                  )
                }
              >
                <item.icon className="h-4 w-4 shrink-0" />
                {item.name}
              </NavLink>
            ))}
          </nav>

          {/* Footer User Profile & Compliance badge */}
          <div className="p-3 mx-3 mb-2 bg-slate-50 border border-slate-200/80 rounded-xl text-[11px] text-slate-500">
            <div className="flex items-center justify-between mb-1">
              <span className="font-semibold text-slate-700 truncate">{user?.full_name || "Analyst"}</span>
              <span className="text-[10px] bg-emerald-100 text-emerald-800 font-semibold px-1.5 py-0.2 rounded">
                DPDP
              </span>
            </div>
            <div className="truncate text-slate-400 text-[10px] mb-2">{user?.email}</div>
            <button
              onClick={handleLogout}
              className="w-full flex items-center justify-center gap-1.5 py-1 text-rose-600 hover:bg-rose-50 rounded text-xs font-medium transition"
            >
              <LogOut className="h-3.5 w-3.5" /> Sign out
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 md:pl-64 flex flex-col min-h-screen">
        <main className="flex-1 p-4 md:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
