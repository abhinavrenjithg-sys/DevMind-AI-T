import React, { useState, useEffect, useRef } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { api } from '../lib/api';
import type { MessageItem, EvidenceItem, FileContentResponse } from '../types';
import { CodeViewer } from '../components/CodeViewer';
import { 
  Bot, 
  Send, 
  Sparkles, 
  FileCode, 
  CheckCircle2, 
  ArrowRight,
  ShieldCheck,
  User,
  X
} from 'lucide-react';

export const AIAssistantPage: React.FC = () => {
  const { currentRepo } = useWorkspace();
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [inputQuestion, setInputQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Citation inspector modal / side drawer
  const [inspectingEvidence, setInspectingEvidence] = useState<EvidenceItem | null>(null);
  const [fileContent, setFileContent] = useState<FileContentResponse | null>(null);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load conversation history on mount
  useEffect(() => {
    if (!currentRepo?.active_revision_id) return;
    api.getConversations(currentRepo.active_revision_id)
      .then((convs) => {
        if (convs.length > 0 && convs[0].messages.length > 0) {
          setMessages(convs[0].messages);
        } else {
          // Add default welcome message
          setMessages([
            {
              id: 'welcome',
              sender: 'assistant',
              content: (
                `Hello! I am **DevMind AI**, your codebase intelligence and reverse-engineering assistant for **${currentRepo.name}**.\n\n` +
                "I analyze parsed ASTs, call graphs, and indexed symbols to answer questions with verifiable line-level citations. " +
                "Ask me about entry points, authentication, dependencies, or change impact."
              ),
              created_at: new Date().toISOString(),
              evidence: []
            }
          ]);
        }
      })
      .catch(console.error);
  }, [currentRepo]);

  // Load code viewer when evidence citation is clicked
  useEffect(() => {
    if (!inspectingEvidence || !currentRepo?.active_revision_id) return;
    api.getFileContent(currentRepo.active_revision_id, inspectingEvidence.file_path)
      .then(setFileContent)
      .catch((err) => {
        console.error('Failed to load file for citation:', err);
        setFileContent(null);
      });
  }, [inspectingEvidence, currentRepo]);

  const handleAsk = async (questionText = inputQuestion) => {
    if (!currentRepo?.active_revision_id || !questionText.trim()) return;

    const userMessage: MessageItem = {
      id: `u-${Date.now()}`,
      sender: 'user',
      content: questionText.trim(),
      created_at: new Date().toISOString(),
      evidence: []
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputQuestion('');
    setIsLoading(true);

    try {
      const response = await api.askQuestion(currentRepo.active_revision_id, questionText.trim());
      setMessages((prev) => [...prev, response]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: 'assistant',
          content: `Error: ${err.message || 'Failed to generate evidence-grounded answer.'}`,
          created_at: new Date().toISOString(),
          evidence: []
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const samplePrompts = [
    "Where is the application entry point and startup flow?",
    "How does authentication and token verification work?",
    "Which modules and functions depend on the primary service?",
    "Where is input validation or schema definition performed?",
    "Which tests cover the core application business logic?"
  ];

  return (
    <div className="h-[calc(100vh-3.5rem)] flex flex-col p-4 space-y-3">
      {/* Header Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 flex items-center justify-between text-xs shrink-0">
        <div className="flex items-center space-x-2.5">
          <div className="p-1.5 rounded-lg bg-violet-500/20 text-violet-400">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h2 className="font-bold text-slate-100">AI Codebase Intelligence Assistant</h2>
            <p className="text-[11px] text-slate-400">
              Evidence-grounded answers with verified source file and line citations
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 text-[11px] text-emerald-400 bg-emerald-950/60 border border-emerald-800/80 px-2.5 py-1 rounded-full">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Anti-Hallucination Grounding Active</span>
        </div>
      </div>

      {/* Main Split: Chat Area & Citation Code Viewer */}
      <div className="flex-1 flex gap-3 overflow-hidden">
        {/* Chat Thread */}
        <div className="flex-1 bg-slate-900 border border-slate-800 rounded-xl flex flex-col overflow-hidden shadow-lg">
          {/* Messages Scroll Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
            {messages.map((m) => {
              const isAssistant = m.sender === 'assistant';

              return (
                <div
                  key={m.id}
                  className={`flex items-start space-x-3 ${
                    isAssistant ? '' : 'flex-row-reverse space-x-reverse'
                  }`}
                >
                  <div
                    className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
                      isAssistant
                        ? 'bg-violet-950 text-violet-400 border border-violet-800'
                        : 'bg-cyan-950 text-cyan-400 border border-cyan-800'
                    }`}
                  >
                    {isAssistant ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
                  </div>

                  <div className={`space-y-2 max-w-2xl ${isAssistant ? '' : 'text-right'}`}>
                    <div
                      className={`p-3.5 rounded-xl leading-relaxed whitespace-pre-wrap text-left ${
                        isAssistant
                          ? 'bg-slate-950 border border-slate-800 text-slate-200 shadow-sm'
                          : 'bg-cyan-600 text-white font-medium shadow-md shadow-cyan-600/20'
                      }`}
                    >
                      {m.content}
                    </div>

                    {/* Evidence Citations Badges */}
                    {isAssistant && m.evidence && m.evidence.length > 0 && (
                      <div className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800 space-y-1.5 text-left">
                        <div className="text-[10px] font-semibold text-cyan-400 uppercase tracking-wider flex items-center space-x-1">
                          <CheckCircle2 className="w-3 h-3 text-cyan-400" />
                          <span>Verified Source Evidence ({m.evidence.length})</span>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {m.evidence.map((ev, idx) => (
                            <button
                              key={idx}
                              onClick={() => setInspectingEvidence(ev)}
                              className="px-2 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-cyan-800/40 text-cyan-300 font-mono text-[10px] flex items-center space-x-1.5 transition"
                              title={`Inspect ${ev.file_path}:${ev.start_line}-${ev.end_line}`}
                            >
                              <FileCode className="w-3 h-3 text-cyan-400" />
                              <span>{ev.file_path}:{ev.start_line}-{ev.end_line}</span>
                              <ArrowRight className="w-2.5 h-2.5 opacity-60" />
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {isLoading && (
              <div className="flex items-center space-x-2 text-slate-400 text-xs italic py-2">
                <Sparkles className="w-4 h-4 text-violet-400 animate-spin" />
                <span>Retrieving source fragments and validating code evidence...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Prompts Bar */}
          <div className="px-4 py-2 bg-slate-950 border-t border-slate-800 flex items-center space-x-2 overflow-x-auto text-[11px]">
            <span className="text-slate-400 shrink-0 font-medium">Suggested:</span>
            {samplePrompts.map((sp, idx) => (
              <button
                key={idx}
                onClick={() => handleAsk(sp)}
                className="px-2.5 py-1 rounded-full bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 whitespace-nowrap transition"
              >
                {sp}
              </button>
            ))}
          </div>

          {/* Question Input Form */}
          <form
            onSubmit={(e) => { e.preventDefault(); handleAsk(); }}
            className="p-3 bg-slate-900 border-t border-slate-800 flex items-center space-x-2"
          >
            <input
              type="text"
              placeholder={`Ask any question about ${currentRepo?.name || 'this codebase'}...`}
              value={inputQuestion}
              onChange={(e) => setInputQuestion(e.target.value)}
              disabled={isLoading || !currentRepo}
              className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-xs text-slate-100 placeholder-slate-400 focus:outline-none focus:border-cyan-500 font-sans"
            />
            <button
              type="submit"
              disabled={isLoading || !inputQuestion.trim() || !currentRepo}
              className="px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 text-white font-medium text-xs transition shadow-md shadow-cyan-600/20 disabled:opacity-40 flex items-center space-x-1.5"
            >
              <span>Ask</span>
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>

        {/* Live Citation Inspector Drawer */}
        {inspectingEvidence && (
          <div className="w-[480px] bg-slate-900 border border-slate-800 rounded-xl flex flex-col shrink-0 overflow-hidden shadow-2xl">
            <div className="p-3 bg-slate-950 border-b border-slate-800 flex items-center justify-between text-xs">
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-cyan-400" />
                <span className="font-semibold text-slate-200">Citation Evidence Viewer</span>
              </div>
              <button
                onClick={() => setInspectingEvidence(null)}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="flex-1 overflow-hidden p-2">
              {fileContent ? (
                <CodeViewer
                  filePath={fileContent.file_path}
                  language={fileContent.language}
                  content={fileContent.content}
                  symbols={fileContent.symbols}
                  highlightLine={inspectingEvidence.start_line}
                  highlightEndLine={inspectingEvidence.end_line}
                />
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-slate-400 italic">
                  Loading source file...
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
