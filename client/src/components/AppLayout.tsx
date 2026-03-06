import { Link, useLocation, useNavigate } from "react-router-dom";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Mic,
  BarChart3,
  Users,
  ClipboardCheck,
  Settings,
  LogOut,
  ChevronLeft,
  Menu,
} from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import OracyLogo from "@/components/OracyLogo";
import { useLogout, useCurrentUser } from "@/lib/api";

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
}

const pupilNav: NavItem[] = [
  { label: "Dashboard", href: "/pupil", icon: <LayoutDashboard className="w-5 h-5" /> },
  { label: "My Tasks", href: "/pupil/tasks", icon: <Mic className="w-5 h-5" /> },
  { label: "Progress", href: "/pupil/progress", icon: <BarChart3 className="w-5 h-5" /> },
];

const teacherNav: NavItem[] = [
  { label: "Dashboard", href: "/teacher", icon: <LayoutDashboard className="w-5 h-5" /> },
  { label: "Review", href: "/teacher/review", icon: <ClipboardCheck className="w-5 h-5" /> },
  { label: "Students", href: "/teacher/students", icon: <Users className="w-5 h-5" /> },
  { label: "Progress", href: "/teacher/progress", icon: <BarChart3 className="w-5 h-5" /> },
];

interface AppLayoutProps {
  children: React.ReactNode;
  role: "pupil" | "teacher";
}

export default function AppLayout({ children, role }: AppLayoutProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const nav = role === "pupil" ? pupilNav : teacherNav;
  const { data: user } = useCurrentUser();
  const logoutMutation = useLogout();

  const handleLogout = async () => {
    await logoutMutation.mutateAsync();
    navigate('/login');
  };

  return (
    <div className="flex min-h-screen bg-background">
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-foreground/20 backdrop-blur-sm md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex flex-col bg-card border-r border-border transition-all duration-300",
          collapsed ? "w-16" : "w-60",
          mobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        )}
      >
        {/* Logo */}
        <div className="flex items-center justify-between h-14 md:h-16 lg:h-[72px] px-4 border-b border-border">
          {!collapsed && (
            <OracyLogo
              variant="full"
              theme="light"
              linkTo={role === "pupil" ? "/pupil" : "/teacher"}
            />
          )}
          {collapsed && (
            <OracyLogo
              variant="icon"
              theme="light"
              linkTo={role === "pupil" ? "/pupil" : "/teacher"}
            />
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="hidden md:flex items-center justify-center w-8 h-8 rounded-md hover:bg-secondary transition-colors text-muted-foreground"
          >
            <ChevronLeft className={cn("w-4 h-4 transition-transform", collapsed && "rotate-180")} />
          </button>
        </div>

        {/* Role badge */}
        {!collapsed && (
          <div className="px-4 py-3">
            <span className={cn(
              "inline-flex items-center px-3 py-1 rounded-full text-xs font-medium",
              role === "pupil"
                ? "bg-accent text-accent-foreground"
                : "bg-primary text-primary-foreground"
            )}>
              {role === "pupil" ? "🎤 Pupil" : "📋 Teacher"}
            </span>
          </div>
        )}

        {/* Nav */}
        <nav className="flex-1 px-2 py-2 space-y-1">
          {nav.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.href}
                to={item.href}
                onClick={() => setMobileOpen(false)}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all",
                  isActive
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                )}
              >
                {item.icon}
                {!collapsed && <span>{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="px-2 py-3 border-t border-border space-y-1">
          <button
            onClick={handleLogout}
            disabled={logoutMutation.isPending}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-muted-foreground hover:bg-secondary transition-colors"
          >
            <LogOut className="w-5 h-5" />
            {!collapsed && <span>{logoutMutation.isPending ? "Logging out..." : "Logout"}</span>}
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className={cn("flex-1 transition-all duration-300", collapsed ? "md:ml-16" : "md:ml-60")}>
        {/* Top bar */}
        <header className="sticky top-0 z-30 flex items-center h-14 md:h-16 lg:h-[72px] px-4 bg-card/80 backdrop-blur-sm border-b border-border md:px-6">
          <button
            onClick={() => setMobileOpen(true)}
            className="mr-3 md:hidden text-muted-foreground"
          >
            <Menu className="w-5 h-5" />
          </button>
          <div className="flex-1" />
          <div className="flex items-center gap-3">
            <Link to={role === "pupil" ? "/teacher" : "/pupil"}>
              <Button variant="outline" size="sm">
                Switch to {role === "pupil" ? "Teacher" : "Pupil"}
              </Button>
            </Link>
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
              <span className="text-xs font-medium text-primary-foreground">
                {user?.first_name?.[0] || (role === "pupil" ? "P" : "T")}
              </span>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-4 md:p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
