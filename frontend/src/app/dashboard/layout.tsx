"use client";

import { useAuth } from "@/components/AuthProvider";
import { useRouter, usePathname } from "next/navigation";
import { useEffect } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { BarChart3, Database, MessageSquare, Settings, LogOut } from "lucide-react";

interface NavLinkProps {
  href: string;
  icon: React.ElementType;
  children: React.ReactNode;
  exact?: boolean;
}

const NavLink = ({ href, icon: Icon, children, exact = false }: NavLinkProps) => {
  const pathname = usePathname();
  const isActive = exact ? pathname === href : pathname.startsWith(href);
  return (
    <Link 
      href={href} 
      className={`flex items-center gap-3 px-3 py-2.5 rounded-lg font-medium text-sm transition-all duration-200 hover:scale-[1.02] active:scale-95 ${
        isActive 
          ? "text-primary bg-primary/15 dark:bg-primary/20 shadow-sm" 
          : "text-muted-foreground hover:bg-muted hover:text-foreground"
      }`}
    >
      <Icon className={`h-4 w-4 ${isActive ? "text-primary" : ""}`} /> 
      {children}
    </Link>
  );
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user, logout, isInitialized } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isInitialized && !isAuthenticated) {
      router.push("/login");
    }
  }, [isInitialized, isAuthenticated, router]);

  if (!isInitialized || !isAuthenticated || !user) {
    return null;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50 dark:bg-slate-950">
      <aside className="w-64 flex-shrink-0 border-r bg-card/95 backdrop-blur-xl shadow-[4px_0_24px_rgba(0,0,0,0.02)] flex flex-col transition-all z-20">
        <div className="h-16 flex items-center px-6 border-b">
          <Link href="/dashboard" className="font-bold text-xl tracking-tight flex items-center gap-2 group transition-transform hover:scale-105">
            <div className="bg-gradient-to-br from-primary to-purple-600 p-1.5 rounded-lg shadow-md group-hover:shadow-primary/20 transition-all">
              <BarChart3 className="h-5 w-5 text-white" />
            </div>
            AI Analyst
          </Link>
        </div>
        <div className="flex-1 overflow-y-auto py-6 px-4 space-y-2">
          <div className="px-3 mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider opacity-70">Navigation</div>
          <NavLink href="/dashboard" icon={BarChart3} exact>Overview</NavLink>
          <NavLink href="/dashboard/datasets" icon={Database}>Datasets Library</NavLink>
          <NavLink href="/dashboard/chat" icon={MessageSquare}>Analysis Chat</NavLink>
          
          {user.is_admin && (
            <>
              <div className="px-3 mt-8 mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider opacity-70">Administration</div>
              <NavLink href="/dashboard/admin" icon={Settings}>System Settings</NavLink>
            </>
          )}
        </div>
        <div className="p-4 border-t bg-muted/20 backdrop-blur-md">
          <div className="flex items-center justify-between">
            <div className="truncate pr-2">
              <p className="text-sm font-medium truncate">{user.email}</p>
              <p className="text-xs text-primary/70 truncate">{user.is_admin ? "Administrator" : "Standard User"}</p>
            </div>
            <Button variant="ghost" size="icon" onClick={logout} className="text-muted-foreground hover:bg-destructive/10 hover:text-destructive shrink-0 transition-colors" title="Logout">
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </aside>
      <main className="flex-1 h-full overflow-y-auto relative z-10">
        <div className="p-6 md:p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
