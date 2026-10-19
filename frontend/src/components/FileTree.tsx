import React, { useState } from 'react';
import type { FileTreeNode } from '../types';
import { 
  Folder, 
  FolderOpen, 
  FileCode, 
  FileText, 
  ChevronRight, 
  ChevronDown 
} from 'lucide-react';

interface FileTreeProps {
  nodes: FileTreeNode[];
  selectedPath?: string;
  onSelectFile: (path: string) => void;
}

const TreeNodeItem: React.FC<{
  node: FileTreeNode;
  selectedPath?: string;
  onSelectFile: (path: string) => void;
  depth?: number;
}> = ({ node, selectedPath, onSelectFile, depth = 0 }) => {
  const [isOpen, setIsOpen] = useState(depth < 2);
  const isSelected = selectedPath === node.path;
  const isDirectory = node.type === 'directory';

  const handleClick = () => {
    if (isDirectory) {
      setIsOpen(!isOpen);
    } else {
      onSelectFile(node.path);
    }
  };

  const getFileIcon = (lang?: string) => {
    if (lang === 'python') return <span className="text-yellow-400 font-bold text-[10px]">PY</span>;
    if (lang === 'typescript' || lang === 'typescript-react') return <span className="text-blue-400 font-bold text-[10px]">TS</span>;
    if (lang === 'javascript' || lang === 'javascript-react') return <span className="text-amber-300 font-bold text-[10px]">JS</span>;
    if (lang === 'json') return <span className="text-emerald-400 font-bold text-[10px]">{}</span>;
    return <FileCode className="w-3.5 h-3.5 text-slate-400" />;
  };

  return (
    <div>
      <div
        onClick={handleClick}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
        className={`flex items-center justify-between py-1 pr-2 text-xs cursor-pointer select-none rounded transition ${
          isSelected
            ? 'bg-cyan-950/70 text-cyan-300 font-medium border-l-2 border-cyan-400'
            : 'text-slate-300 hover:bg-slate-800/60 hover:text-slate-100'
        }`}
      >
        <div className="flex items-center space-x-1.5 truncate">
          {isDirectory ? (
            <>
              {isOpen ? (
                <ChevronDown className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              ) : (
                <ChevronRight className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              )}
              {isOpen ? (
                <FolderOpen className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
              ) : (
                <Folder className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
              )}
            </>
          ) : (
            <div className="w-4 flex items-center justify-center shrink-0">
              {getFileIcon(node.language)}
            </div>
          )}
          <span className="truncate">{node.name}</span>
        </div>

        {!isDirectory && node.lines !== undefined && (
          <span className="text-[10px] text-slate-400 shrink-0 ml-2">
            {node.lines} L
          </span>
        )}
      </div>

      {isDirectory && isOpen && node.children && (
        <div>
          {node.children.map((child) => (
            <TreeNodeItem
              key={child.path}
              node={child}
              selectedPath={selectedPath}
              onSelectFile={onSelectFile}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export const FileTree: React.FC<FileTreeProps> = ({ nodes, selectedPath, onSelectFile }) => {
  return (
    <div className="h-full overflow-y-auto py-2 font-mono">
      {nodes.length === 0 ? (
        <div className="text-slate-400 text-xs italic px-3 py-2">No files discovered</div>
      ) : (
        nodes.map((node) => (
          <TreeNodeItem
            key={node.path}
            node={node}
            selectedPath={selectedPath}
            onSelectFile={onSelectFile}
          />
        ))
      )}
    </div>
  );
};
