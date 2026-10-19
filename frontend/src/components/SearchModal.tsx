import React, { useState, useEffect } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { api } from '../lib/api';
import type { SearchResultItem } from '../types';
import { Search, X, FileCode, Sparkles, FileText, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface SearchModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SearchModal: React.FC<SearchModalProps> = ({ isOpen, onClose }) => {
  const { currentRepo } = useWorkspace();
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [searchType, setSearchType] = useState('all');
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
        else onClose(); // parent handles toggling
      }
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const handleSearch = async () => {
    if (!currentRepo?.active_revision_id || !query.trim()) return;
    setIsLoading(true);
    try {
      const data = await api.search(currentRepo.active_revision_id, query.trim(), searchType);
      setResults(data.results);
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      if (query.trim().length >= 2) {
        handleSearch();
      } else {
        setResults([]);
      }
    }, 250);
    return () => clearTimeout(delayDebounce);
  }, [query, searchType]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-start justify-center pt-20 p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[80vh]">
        {/* Search Input Bar */}
        <div className="p-3 border-b border-slate-800 flex items-center space-x-3">
          <Search className="w-5 h-5 text-cyan-400 shrink-0" />
          <input
            type="text"
            placeholder={currentRepo ? `Search in ${currentRepo.name} (e.g. auth, User, def process)...` : "Select a repository to search..."}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-400 focus:outline-none"
            autoFocus
          />
          {query && (
            <button onClick={() => setQuery('')} className="text-slate-400 hover:text-slate-200">
              <X className="w-4 h-4" />
            </button>
          )}
          <kbd className="text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded border border-slate-700">ESC</kbd>
        </div>

        {/* Filter Pills */}
        <div className="px-3 py-2 bg-slate-950 border-b border-slate-800 flex items-center space-x-2 text-xs">
          {['all', 'symbol', 'file', 'fulltext'].map((t) => (
            <button
              key={t}
              onClick={() => setSearchType(t)}
              className={`px-2.5 py-1 rounded-md uppercase text-[10px] font-semibold transition ${
                searchType === t
                  ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        {/* Results List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {isLoading ? (
            <div className="text-center py-8 text-xs text-slate-400">Searching codebase...</div>
          ) : results.length === 0 ? (
            <div className="text-center py-8 text-xs text-slate-400">
              {query ? 'No matching symbols, files, or code found' : 'Type to search across symbols, files, and source code'}
            </div>
          ) : (
            results.map((r, idx) => (
              <div
                key={idx}
                onClick={() => {
                  onClose();
                  navigate(`/search?q=${encodeURIComponent(r.title)}`);
                }}
                className="p-2.5 rounded-lg hover:bg-slate-800/80 cursor-pointer flex items-start justify-between group transition"
              >
                <div className="flex items-start space-x-2.5 truncate">
                  <div className="mt-0.5">
                    {r.type === 'symbol' ? (
                      <Sparkles className="w-4 h-4 text-violet-400" />
                    ) : r.type === 'file' ? (
                      <FileCode className="w-4 h-4 text-cyan-400" />
                    ) : (
                      <FileText className="w-4 h-4 text-slate-400" />
                    )}
                  </div>
                  <div className="truncate">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-xs text-slate-100 group-hover:text-cyan-300">
                        {r.title}
                      </span>
                      {r.symbol_kind && (
                        <span className="text-[10px] px-1 py-0.2 rounded bg-slate-800 text-slate-400 uppercase">
                          {r.symbol_kind}
                        </span>
                      )}
                    </div>
                    <div className="text-[11px] text-slate-400 font-mono truncate mt-0.5">
                      {r.file_path}:{r.start_line}
                    </div>
                    {r.excerpt && (
                      <pre className="text-[11px] text-slate-400 font-mono mt-1 bg-slate-950 p-1.5 rounded border border-slate-800 truncate">
                        {r.excerpt}
                      </pre>
                    )}
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-cyan-400 shrink-0 ml-2" />
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
