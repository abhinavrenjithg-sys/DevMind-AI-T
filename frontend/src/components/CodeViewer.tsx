import React, { useEffect, useRef } from 'react';
import type { SymbolItem } from '../types';
import { FileCode, Hash, Sparkles } from 'lucide-react';

interface CodeViewerProps {
  filePath: string;
  language: string;
  content: string;
  symbols?: SymbolItem[];
  highlightLine?: number;
  highlightEndLine?: number;
  onSymbolClick?: (symbol: SymbolItem) => void;
}

export const CodeViewer: React.FC<CodeViewerProps> = ({
  filePath,
  language,
  content,
  symbols = [],
  highlightLine,
  highlightEndLine,
  onSymbolClick
}) => {
  const lineRefs = useRef<{ [key: number]: HTMLDivElement | null }>({});
  const lines = content.split('\n');

  // Scroll to highlightLine if supplied
  useEffect(() => {
    if (highlightLine && lineRefs.current[highlightLine]) {
      lineRefs.current[highlightLine]?.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
      });
    }
  }, [highlightLine, content]);

  return (
    <div className="flex flex-col h-full bg-slate-950 border border-slate-800 rounded-lg overflow-hidden">
      {/* File Header */}
      <div className="h-10 bg-slate-900 border-b border-slate-800 px-4 flex items-center justify-between text-xs shrink-0">
        <div className="flex items-center space-x-2 truncate">
          <FileCode className="w-4 h-4 text-cyan-400 shrink-0" />
          <span className="font-mono font-medium text-slate-200 truncate">{filePath}</span>
        </div>
        <div className="flex items-center space-x-3 text-slate-400">
          <span className="uppercase text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
            {language}
          </span>
          <span>{lines.length} lines</span>
          <span>{symbols.length} symbols</span>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Main Code View with Line Numbers */}
        <div className="flex-1 overflow-auto font-mono text-xs p-2 select-text">
          {lines.map((lineText, idx) => {
            const lineNum = idx + 1;
            const isHighlighted =
              highlightLine &&
              lineNum >= highlightLine &&
              lineNum <= (highlightEndLine || highlightLine);

            return (
              <div
                key={lineNum}
                ref={(el) => { lineRefs.current[lineNum] = el; }}
                className={`flex items-start group hover:bg-slate-900/80 transition-colors ${
                  isHighlighted ? 'bg-cyan-950/60 border-l-2 border-cyan-400' : ''
                }`}
              >
                {/* Line number gutter */}
                <span className="w-12 text-right pr-4 text-slate-400 select-none shrink-0 group-hover:text-slate-400">
                  {lineNum}
                </span>

                {/* Code line text */}
                <pre className="text-slate-200 whitespace-pre font-mono leading-relaxed">
                  {lineText || ' '}
                </pre>
              </div>
            );
          })}
        </div>

        {/* Symbols sidebar in the code viewer */}
        {symbols.length > 0 && (
          <div className="w-48 bg-slate-900/60 border-l border-slate-800 p-2 overflow-y-auto hidden md:block shrink-0">
            <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center space-x-1">
              <Sparkles className="w-3 h-3 text-cyan-400" />
              <span>Symbols ({symbols.length})</span>
            </div>
            <div className="space-y-1">
              {symbols.map((sym) => (
                <div
                  key={sym.id}
                  onClick={() => onSymbolClick && onSymbolClick(sym)}
                  className="px-2 py-1 rounded text-[11px] font-mono cursor-pointer hover:bg-slate-800 text-slate-300 hover:text-cyan-300 truncate transition"
                  title={`${sym.signature || sym.name} (Line ${sym.start_line})`}
                >
                  <span className="text-[9px] text-cyan-400 mr-1 uppercase">
                    {sym.kind[0]}
                  </span>
                  <span>{sym.name}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
