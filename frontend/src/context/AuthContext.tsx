import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { User, Workspace, MeResponseData } from "../types";
import { apiClient } from "../api/client";

interface AuthContextType {
  user: User | null;
  currentWorkspace: Workspace | null;
  workspaces: Workspace[];
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, fullName: string, workspaceName?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  setCurrentWorkspace: (workspace: Workspace) => void;
  updateWorkspace: (workspaceId: string, data: Partial<Workspace>) => Promise<Workspace>;
  seedDemoData: (workspaceId: string, industry?: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [currentWorkspace, setCurrentWorkspaceState] = useState<Workspace | null>(null);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refreshUser = useCallback(async () => {
    try {
      const data = await apiClient.get<MeResponseData>("/me");
      setUser(data.user);
      setWorkspaces(data.workspaces || []);
      if (data.current_workspace) {
        setCurrentWorkspaceState(data.current_workspace);
      } else if (data.workspaces && data.workspaces.length > 0) {
        setCurrentWorkspaceState(data.workspaces[0]);
      }
    } catch {
      setUser(null);
      setCurrentWorkspaceState(null);
      setWorkspaces([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = async (email: string, password: string) => {
    await apiClient.post("/auth/login", { email, password });
    await refreshUser();
  };

  const signup = async (email: string, password: string, fullName: string, workspaceName?: string) => {
    await apiClient.post("/auth/signup", {
      email,
      password,
      full_name: fullName,
      workspace_name: workspaceName || `${fullName}'s Brand`,
    });
    await refreshUser();
  };

  const logout = async () => {
    try {
      await apiClient.post("/auth/logout");
    } finally {
      setUser(null);
      setCurrentWorkspaceState(null);
      setWorkspaces([]);
    }
  };

  const setCurrentWorkspace = (workspace: Workspace) => {
    setCurrentWorkspaceState(workspace);
  };

  const updateWorkspace = async (workspaceId: string, data: Partial<Workspace>) => {
    const updated = await apiClient.patch<Workspace>(`/workspaces/${workspaceId}`, data);
    setCurrentWorkspaceState(updated);
    setWorkspaces((prev) =>
      prev.map((w) => (w.id === workspaceId ? { ...w, ...updated } : w))
    );
    return updated;
  };

  const seedDemoData = async (workspaceId: string, industry: string = "D2C / Sustainable Fashion") => {
    await apiClient.post(`/workspaces/${workspaceId}/seed-demo`, { industry });
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        currentWorkspace,
        workspaces,
        isLoading,
        login,
        signup,
        logout,
        refreshUser,
        setCurrentWorkspace,
        updateWorkspace,
        seedDemoData,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
