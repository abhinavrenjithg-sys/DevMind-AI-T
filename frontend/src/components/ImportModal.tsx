import React, { useState } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { api } from '../lib/api';
import { GitBranch, Upload, X, AlertCircle, CheckCircle2 } from 'lucide-react';

interface ImportModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ImportModal: React.FC<ImportModalProps> = ({ isOpen, onClose }) => {
  const { currentWorkspace, refreshRepositories, setCurrentRepo } = useWorkspace();
  const [tab, setTab] = useState<'git' | 'zip'>('git');
  const [repoName, setRepoName] = useState('');
  const [gitUrl, setGitUrl] = useState('');
  const [branch, setBranch] = useState('main');
  const [file, setFile] = useState<File | null>(null);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentWorkspace) {
      setError('No active workspace selected.');
      return;
    }

    if (!repoName.trim()) {
      setError('Please provide a repository name.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setSuccessMsg(null);

    try {
      let createdRepo;
      if (tab === 'git') {
        if (!gitUrl.trim()) {
          throw new Error('Please enter a valid Git repository URL.');
        }
        createdRepo = await api.importGitRepo(currentWorkspace.id, repoName.trim(), gitUrl.trim(), branch.trim());
      } else {
        if (!file) {
          throw new Error('Please select a .zip archive to upload.');
        }
        createdRepo = await api.uploadZipRepo(currentWorkspace.id, repoName.trim(), file);
      }

      setSuccessMsg(`Repository "${createdRepo.name}" ingested successfully! Starting analysis...`);
      await refreshRepositories();
      setCurrentRepo(createdRepo);

      // Start analysis job immediately
      try {
        await api.startAnalysis(createdRepo.id);
      } catch (analysisErr) {
        console.warn('Initial analysis job trigger notice:', analysisErr);
      }

      setTimeout(() => {
        onClose();
        setRepoName('');
        setGitUrl('');
        setFile(null);
        setSuccessMsg(null);
      }, 1200);

    } catch (err: any) {
      setError(err.message || 'Failed to import repository.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-lg shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="p-1.5 rounded-md bg-cyan-500/20 text-cyan-400">
              <GitBranch className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-bold text-sm text-slate-100">Import Codebase Repository</h2>
              <p className="text-[11px] text-slate-400">Ingest for dependency mapping & code intelligence</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-200">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Selection */}
        <div className="flex border-b border-slate-800 bg-slate-950 px-4 text-xs">
          <button
            type="button"
            onClick={() => { setTab('git'); setError(null); }}
            className={`py-2.5 px-3 font-medium border-b-2 transition ${
              tab === 'git'
                ? 'border-cyan-400 text-cyan-400 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Public Git URL
          </button>
          <button
            type="button"
            onClick={() => { setTab('zip'); setError(null); }}
            className={`py-2.5 px-3 font-medium border-b-2 transition ${
              tab === 'zip'
                ? 'border-cyan-400 text-cyan-400 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Repository ZIP Upload
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-4 space-y-3.5 text-xs">
          {error && (
            <div className="p-2.5 rounded-lg bg-rose-950/70 border border-rose-800 text-rose-300 flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {successMsg && (
            <div className="p-2.5 rounded-lg bg-emerald-950/70 border border-emerald-800 text-emerald-300 flex items-start space-x-2">
              <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{successMsg}</span>
            </div>
          )}

          <div>
            <label className="block text-slate-300 font-medium mb-1">Repository Name</label>
            <input
              type="text"
              placeholder="e.g. devmind-core"
              value={repoName}
              onChange={(e) => setRepoName(e.target.value)}
              required
              className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-slate-100 placeholder-slate-400 focus:outline-none focus:border-cyan-500"
            />
          </div>

          {tab === 'git' ? (
            <>
              <div>
                <label className="block text-slate-300 font-medium mb-1">Git Repository URL</label>
                <input
                  type="url"
                  placeholder="https://github.com/org/repo.git"
                  value={gitUrl}
                  onChange={(e) => {
                    setGitUrl(e.target.value);
                    if (!repoName && e.target.value) {
                      const parts = e.target.value.split('/');
                      const last = parts[parts.length - 1].replace('.git', '');
                      setRepoName(last);
                    }
                  }}
                  required
                  className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-slate-100 placeholder-slate-400 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">Branch</label>
                <input
                  type="text"
                  placeholder="main"
                  value={branch}
                  onChange={(e) => setBranch(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-slate-100 placeholder-slate-400 focus:outline-none focus:border-cyan-500"
                />
              </div>
            </>
          ) : (
            <div>
              <label className="block text-slate-300 font-medium mb-1">Select Repository ZIP</label>
              <div className="border-2 border-dashed border-slate-800 hover:border-cyan-500/50 rounded-lg p-6 text-center bg-slate-950 cursor-pointer">
                <input
                  type="file"
                  accept=".zip"
                  onChange={(e) => {
                    const selected = e.target.files?.[0] || null;
                    setFile(selected);
                    if (selected && !repoName) {
                      setRepoName(selected.name.replace('.zip', ''));
                    }
                  }}
                  className="hidden"
                  id="zip-upload"
                />
                <label htmlFor="zip-upload" className="cursor-pointer flex flex-col items-center">
                  <Upload className="w-8 h-8 text-cyan-400 mb-2" />
                  <span className="text-slate-200 font-medium">
                    {file ? file.name : "Click to select a .zip archive"}
                  </span>
                  <span className="text-[11px] text-slate-400 mt-1">
                    Max size: 100 MB • Safe decompression protected
                  </span>
                </label>
              </div>
            </div>
          )}

          <div className="pt-2 flex items-center justify-end space-x-2 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 rounded-md border border-slate-800 text-slate-300 hover:bg-slate-800 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-1.5 rounded-md bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 text-white font-medium transition disabled:opacity-50"
            >
              {isLoading ? 'Ingesting Codebase...' : 'Ingest & Start Analysis'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
