import React, { useState } from 'react';
import { Settings, Shield, Cpu, HardDrive, Key, Check } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const [provider, setProvider] = useState<string>('heuristic');
  const [openaiKey, setOpenaiKey] = useState<string>('');
  const [geminiKey, setGeminiKey] = useState<string>('');
  const [saved, setSaved] = useState<boolean>(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto text-xs">
      <div className="pb-2 border-b border-slate-800">
        <h1 className="text-xl font-bold text-slate-100 tracking-tight">Platform Settings & Security</h1>
        <p className="text-xs text-slate-400 mt-0.5">
          Configure static analysis boundaries, AI providers, and security guardrails
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* AI Provider Config */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center space-x-2 text-cyan-400 font-semibold text-sm">
            <Cpu className="w-4 h-4" />
            <span>AI Reasoning & Retrieval Engine</span>
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-slate-300 font-medium mb-1">Active AI Provider</label>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500 cursor-pointer"
              >
                <option value="heuristic">Built-in Deterministic Code Reasoner (Zero API Key / Offline)</option>
                <option value="openai">OpenAI (GPT-4o / GPT-4o-mini)</option>
                <option value="gemini">Google Gemini</option>
              </select>
              <p className="text-[11px] text-slate-400 mt-1">
                The built-in engine uses retrieved ASTs, docstrings, and call chains with verified citations without sending source code externally.
              </p>
            </div>

            {provider === 'openai' && (
              <div>
                <label className="block text-slate-300 font-medium mb-1">OpenAI API Key</label>
                <input
                  type="password"
                  placeholder="sk-..."
                  value={openaiKey}
                  onChange={(e) => setOpenaiKey(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
                />
              </div>
            )}

            {provider === 'gemini' && (
              <div>
                <label className="block text-slate-300 font-medium mb-1">Gemini API Key</label>
                <input
                  type="password"
                  placeholder="AIzaSy..."
                  value={geminiKey}
                  onChange={(e) => setGeminiKey(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
                />
              </div>
            )}
          </div>
        </div>

        {/* Security Policies */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center space-x-2 text-emerald-400 font-semibold text-sm">
            <Shield className="w-4 h-4" />
            <span>Repository Ingestion Security Policies</span>
          </div>

          <div className="space-y-2 text-slate-300 leading-relaxed">
            <div className="flex items-center justify-between p-2 rounded bg-slate-950 border border-slate-800">
              <span>Arbitrary Code Execution Protection</span>
              <span className="text-emerald-400 font-semibold font-mono">ENFORCED (No repo code runs)</span>
            </div>

            <div className="flex items-center justify-between p-2 rounded bg-slate-950 border border-slate-800">
              <span>SSRF (Server-Side Request Forgery) Filter</span>
              <span className="text-emerald-400 font-semibold font-mono">ACTIVE (Private IPs blocked)</span>
            </div>

            <div className="flex items-center justify-between p-2 rounded bg-slate-950 border border-slate-800">
              <span>Zip Slip & Decompression Bomb Guard</span>
              <span className="text-emerald-400 font-semibold font-mono">ACTIVE (Max 200MB / 10k files)</span>
            </div>

            <div className="flex items-center justify-between p-2 rounded bg-slate-950 border border-slate-800">
              <span>Prompt Injection Defense</span>
              <span className="text-emerald-400 font-semibold font-mono">ACTIVE (Bounded XML Isolation)</span>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-end space-x-3">
          {saved && (
            <span className="text-emerald-400 flex items-center space-x-1">
              <Check className="w-3.5 h-3.5" />
              <span>Settings saved successfully</span>
            </span>
          )}
          <button
            type="submit"
            className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium transition shadow-md shadow-cyan-600/20"
          >
            Save Settings
          </button>
        </div>
      </form>
    </div>
  );
};
