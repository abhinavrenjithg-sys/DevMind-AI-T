import React, { createContext, useContext, useState, useEffect } from 'react';
import type { Workspace, Repository } from '../types';
import { api } from '../lib/api';

interface WorkspaceContextType {
  workspaces: Workspace[];
  currentWorkspace: Workspace | null;
  setCurrentWorkspace: (ws: Workspace | null) => void;
  repositories: Repository[];
  currentRepo: Repository | null;
  setCurrentRepo: (repo: Repository | null) => void;
  isLoading: boolean;
  refreshWorkspaces: () => Promise<void>;
  refreshRepositories: () => Promise<void>;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export const WorkspaceProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [currentWorkspace, setCurrentWorkspace] = useState<Workspace | null>(null);
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [currentRepo, setCurrentRepo] = useState<Repository | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refreshWorkspaces = async () => {
    try {
      const list = await api.getWorkspaces();
      setWorkspaces(list);
      if (list.length > 0 && !currentWorkspace) {
        setCurrentWorkspace(list[0]);
      }
    } catch (err) {
      console.error('Failed to load workspaces:', err);
    }
  };

  const refreshRepositories = async () => {
    if (!currentWorkspace) return;
    try {
      const list = await api.getRepositories(currentWorkspace.id);
      setRepositories(list);
      if (list.length > 0) {
        // Keep current if still exists, else pick first
        setCurrentRepo(prev => {
          if (prev && list.some(r => r.id === prev.id)) {
            return list.find(r => r.id === prev.id) || list[0];
          }
          return list[0];
        });
      } else {
        setCurrentRepo(null);
      }
    } catch (err) {
      console.error('Failed to load repositories:', err);
    }
  };

  useEffect(() => {
    const init = async () => {
      setIsLoading(true);
      await refreshWorkspaces();
      setIsLoading(false);
    };
    init();
  }, []);

  useEffect(() => {
    if (currentWorkspace) {
      refreshRepositories();
    }
  }, [currentWorkspace]);

  return (
    <WorkspaceContext.Provider
      value={{
        workspaces,
        currentWorkspace,
        setCurrentWorkspace,
        repositories,
        currentRepo,
        setCurrentRepo,
        isLoading,
        refreshWorkspaces,
        refreshRepositories
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
};

export const useWorkspace = () => {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error('useWorkspace must be used within a WorkspaceProvider');
  }
  return context;
};
