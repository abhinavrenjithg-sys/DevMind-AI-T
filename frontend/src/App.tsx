import React, { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { WorkspaceProvider } from './context/WorkspaceContext';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { SearchModal } from './components/SearchModal';
import { ImportModal } from './components/ImportModal';

// Pages
import { DashboardPage } from './pages/DashboardPage';
import { RepositoriesPage } from './pages/RepositoriesPage';
import { ArchitecturePage } from './pages/ArchitecturePage';
import { DependencyGraphPage } from './pages/DependencyGraphPage';
import { CodeSearchPage } from './pages/CodeSearchPage';
import { AIAssistantPage } from './pages/AIAssistantPage';
import { ChangeImpactPage } from './pages/ChangeImpactPage';
import { SecurityQualityPage } from './pages/SecurityQualityPage';
import { RevisionComparePage } from './pages/RevisionComparePage';
import { ArchitectureReportPage } from './pages/ArchitectureReportPage';
import { SettingsPage } from './pages/SettingsPage';

const queryClient = new QueryClient();

export function App() {
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isImportOpen, setIsImportOpen] = useState(false);

  return (
    <QueryClientProvider client={queryClient}>
      <WorkspaceProvider>
        <BrowserRouter>
          <div className="flex flex-col h-screen bg-[#0b0f19] text-slate-100 overflow-hidden font-sans">
            {/* Top Navigation */}
            <Navbar
              onOpenSearch={() => setIsSearchOpen(true)}
              onOpenImport={() => setIsImportOpen(true)}
            />

            {/* Main Application Body */}
            <div className="flex flex-1 overflow-hidden">
              {/* Left Navigation Sidebar */}
              <Sidebar />

              {/* Main Content View */}
              <main className="flex-1 overflow-y-auto bg-slate-950">
                <Routes>
                  <Route path="/" element={<DashboardPage />} />
                  <Route
                    path="/repositories"
                    element={<RepositoriesPage onOpenImport={() => setIsImportOpen(true)} />}
                  />
                  <Route path="/architecture" element={<ArchitecturePage />} />
                  <Route path="/graph" element={<DependencyGraphPage />} />
                  <Route path="/search" element={<CodeSearchPage />} />
                  <Route path="/ai" element={<AIAssistantPage />} />
                  <Route path="/impact" element={<ChangeImpactPage />} />
                  <Route path="/security" element={<SecurityQualityPage />} />
                  <Route path="/compare" element={<RevisionComparePage />} />
                  <Route path="/report" element={<ArchitectureReportPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                </Routes>
              </main>
            </div>

            {/* Global Modals */}
            <SearchModal
              isOpen={isSearchOpen}
              onClose={() => setIsSearchOpen(false)}
            />
            <ImportModal
              isOpen={isImportOpen}
              onClose={() => setIsImportOpen(false)}
            />
          </div>
        </BrowserRouter>
      </WorkspaceProvider>
    </QueryClientProvider>
  );
}

export default App;
