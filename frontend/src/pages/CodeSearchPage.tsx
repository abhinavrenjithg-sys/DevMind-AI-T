import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useWorkspace } from '../context/WorkspaceContext';
import { api } from '../lib/api';
import type { SearchResultItem, FileTreeNode, FileContentResponse } from '../types';
import { CodeViewer } from '../components/CodeViewer';
import { FileTree } from '../components/FileTree';
import { 
  Search, 
  FileCode, 
  Sparkles, 
  FolderTree, 
  Code2
} from 'lucide-react';

export const CodeSearchPage: React.FC = () => {
  const { currentRepo } = useWorkspace();
  const [searchParams] = useSearchParams();

  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [searchType, setSearchType] = useState('all');
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [isLoadingSearch, setIsLoadingSearch] = useState(false);

  // File tree and code viewer state
  const [fileTree, setFileTree] = useState<FileTreeNode[]>([]);
  const [selectedFilePath, setSelectedFilePath] = useState<string>(searchParams.get('file') || '');
  const [fileContentData, setFileContentData] = useState<FileContentResponse | null>(null);
  const [targetLine, setTargetLine] = useState<number | undefined>(undefined);
  const [targetEndLine, setTargetEndLine] = useState<number | undefined>(undefined);
  const [activeTab, setActiveTab] = useState<'search' | 'tree'>('search');

  // Load file tree on repository change
  useEffect(() => {
    if (!currentRepo?.active_revision_id) return;
    api.getFileTree(currentRepo.active_revision_id)
      .then((tree) => {
        setFileTree(tree);
        // Select first file if none selected
        if (!selectedFilePath && tree.length > 0) {
          const findFirstFile = (nodes: FileTreeNode[]): string | null => {
            for (const n of nodes) {
              if (n.type === 'file') return n.path;
              if (n.children) {
                const found = findFirstFile(n.children);
                if (found) return found;
              }
            }
            return null;
          };
          const first = findFirstFile(tree);
          if (first) setSelectedFilePath(first);
        }
      })
      .catch(console.error);
  }, [currentRepo]);

  // Execute initial search if url has query
  useEffect(() => {
    const qParam = searchParams.get('q');
    if (qParam && currentRepo?.active_revision_id) {
      setQuery(qParam);
      handleSearch(qParam);
    }
  }, [searchParams, currentRepo]);

  // Load file content when selectedFilePath changes
  useEffect(() => {
    if (!currentRepo?.active_revision_id || !selectedFilePath) return;
    api.getFileContent(currentRepo.active_revision_id, selectedFilePath)
      .then(setFileContentData)
      .catch((err) => {
        console.error('Failed to load file content:', err);
        setFileContentData(null);
      });
  }, [currentRepo, selectedFilePath]);

  const handleSearch = async (searchQuery = query) => {
    if (!currentRepo?.active_revision_id || !searchQuery.trim()) return;
    setIsLoadingSearch(true);
    try {
      const data = await api.search(currentRepo.active_revision_id, searchQuery.trim(), searchType);
      setResults(data.results);
      setActiveTab('search');
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setIsLoadingSearch(false);
    }
  };

  const handleResultClick = (r: SearchResultItem) => {
    setSelectedFilePath(r.file_path);
    setTargetLine(r.start_line);
    setTargetEndLine(r.end_line);
  };

  return (
    <div className="h-[calc(100vh-3.5rem)] flex flex-col p-4 space-y-3">
      {/* Top Search Controls Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 flex flex-wrap items-center justify-between gap-3 text-xs shrink-0">
        <form
          onSubmit={(e) => { e.preventDefault(); handleSearch(); }}
          className="flex-1 flex items-center space-x-2 min-w-[280px]"
        >
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-cyan-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search symbols, functions, files, or code (e.g. auth, def process, interface User)..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-slate-100 placeholder-slate-400 focus:outline-none focus:border-cyan-500 font-mono text-xs"
            />
          </div>

          <div className="bg-slate-950 px-2 py-1 rounded-lg border border-slate-800 flex items-center space-x-1.5">
            <span className="text-slate-400 text-[11px]">Type:</span>
            <select
              value={searchType}
              onChange={(e) => setSearchType(e.target.value)}
              className="bg-transparent text-slate-200 focus:outline-none cursor-pointer"
            >
              <option value="all" className="bg-slate-900">All</option>
              <option value="symbol" className="bg-slate-900">Symbols</option>
              <option value="file" className="bg-slate-900">Files</option>
              <option value="fulltext" className="bg-slate-900">Full Text</option>
              <option value="regex" className="bg-slate-900">Regex</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={isLoadingSearch}
            className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium transition"
          >
            {isLoadingSearch ? 'Searching...' : 'Search'}
          </button>
        </form>
      </div>

      {/* Main Split Pane: Left (Results/Tree) | Right (CodeViewer) */}
      <div className="flex-1 flex gap-3 overflow-hidden">
        {/* Left Side Pane */}
        <div className="w-80 bg-slate-900 border border-slate-800 rounded-xl flex flex-col shrink-0 overflow-hidden">
          {/* Tabs: Search Results vs File Tree */}
          <div className="flex border-b border-slate-800 bg-slate-950 text-xs">
            <button
              onClick={() => setActiveTab('search')}
              className={`flex-1 py-2 font-medium flex items-center justify-center space-x-1.5 transition ${
                activeTab === 'search'
                  ? 'border-b-2 border-cyan-400 text-cyan-400 font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Search className="w-3.5 h-3.5" />
              <span>Results ({results.length})</span>
            </button>

            <button
              onClick={() => setActiveTab('tree')}
              className={`flex-1 py-2 font-medium flex items-center justify-center space-x-1.5 transition ${
                activeTab === 'tree'
                  ? 'border-b-2 border-cyan-400 text-cyan-400 font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <FolderTree className="w-3.5 h-3.5" />
              <span>File Explorer</span>
            </button>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-y-auto p-2">
            {activeTab === 'search' ? (
              results.length === 0 ? (
                <div className="text-center py-12 text-slate-400 text-xs italic">
                  {query ? 'No matching results found.' : 'Enter a query above to search.'}
                </div>
              ) : (
                <div className="space-y-1">
                  {results.map((r, idx) => (
                    <div
                      key={idx}
                      onClick={() => handleResultClick(r)}
                      className={`p-2 rounded-lg cursor-pointer transition text-xs ${
                        selectedFilePath === r.file_path && targetLine === r.start_line
                          ? 'bg-cyan-950/80 border border-cyan-600/40 text-cyan-200'
                          : 'hover:bg-slate-800/60 text-slate-300'
                      }`}
                    >
                      <div className="flex items-center space-x-2">
                        {r.type === 'symbol' ? (
                          <Sparkles className="w-3.5 h-3.5 text-violet-400 shrink-0" />
                        ) : (
                          <FileCode className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                        )}
                        <span className="font-semibold truncate">{r.title}</span>
                        {r.symbol_kind && (
                          <span className="text-[9px] px-1 py-0.2 rounded bg-slate-800 text-slate-400 uppercase">
                            {r.symbol_kind}
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] font-mono text-slate-400 truncate mt-0.5">
                        {r.file_path}:{r.start_line}
                      </div>
                    </div>
                  ))}
                </div>
              )
            ) : (
              <FileTree
                nodes={fileTree}
                selectedPath={selectedFilePath}
                onSelectFile={(path) => {
                  setSelectedFilePath(path);
                  setTargetLine(undefined);
                  setTargetEndLine(undefined);
                }}
              />
            )}
          </div>
        </div>

        {/* Right Side: Code Viewer */}
        <div className="flex-1 h-full overflow-hidden">
          {fileContentData ? (
            <CodeViewer
              filePath={fileContentData.file_path}
              language={fileContentData.language}
              content={fileContentData.content}
              symbols={fileContentData.symbols}
              highlightLine={targetLine}
              highlightEndLine={targetEndLine}
              onSymbolClick={(sym) => {
                setTargetLine(sym.start_line);
                setTargetEndLine(sym.end_line);
              }}
            />
          ) : (
            <div className="h-full bg-slate-950 border border-slate-800 rounded-lg flex flex-col items-center justify-center text-slate-400 text-xs">
              <Code2 className="w-10 h-10 text-slate-700 mb-2" />
              <span>Select a file or search result to view source code</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
