import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { AppLayout } from "./components/layout/AppLayout";
import { Login } from "./pages/auth/Login";
import { Signup } from "./pages/auth/Signup";
import { Onboarding } from "./pages/onboarding/Onboarding";
import { Overview } from "./pages/overview/Overview";
import { TrendExplorer } from "./pages/trends/TrendExplorer";
import { TrendDetail } from "./pages/trends/TrendDetail";
import { AudienceInsights } from "./pages/audiences/AudienceInsights";
import { OpportunityDetail } from "./pages/opportunities/OpportunityDetail";
import { SavedBoard } from "./pages/opportunities/SavedBoard";
import { CampaignAnalytics } from "./pages/campaigns/CampaignAnalytics";
import { DataSources } from "./pages/sources/DataSources";
import { Reports } from "./pages/reports/Reports";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30000,
    },
  },
});

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent" />
          <span className="text-xs font-semibold text-slate-500">Loading workspace session...</span>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public Auth Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />

            {/* Protected Workspace Setup */}
            <Route
              path="/onboarding"
              element={
                <ProtectedRoute>
                  <Onboarding />
                </ProtectedRoute>
              }
            />

            {/* Main Application Shell */}
            <Route
              path="/app"
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Overview />} />
              <Route path="trends" element={<TrendExplorer />} />
              <Route path="trends/:id" element={<TrendDetail />} />
              <Route path="audiences" element={<AudienceInsights />} />
              <Route path="opportunities" element={<SavedBoard />} />
              <Route path="opportunities/:id" element={<OpportunityDetail />} />
              <Route path="saved" element={<SavedBoard />} />
              <Route path="campaigns" element={<CampaignAnalytics />} />
              <Route path="sources" element={<DataSources />} />
              <Route path="reports" element={<Reports />} />
            </Route>

            {/* Default redirect to /app */}
            <Route path="/" element={<Navigate to="/app" replace />} />
            <Route path="*" element={<Navigate to="/app" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
