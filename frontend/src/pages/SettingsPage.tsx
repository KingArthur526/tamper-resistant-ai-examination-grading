import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Save } from "lucide-react";
import { api } from "../api/client";
import { EvaluationConfig } from "../types";

export const SettingsPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const examId = searchParams.get("exam") || "";

  const [config, setConfig] = useState<EvaluationConfig | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (examId) loadConfig(examId);
  }, [examId]);

  const loadConfig = async (eId: string) => {
    try {
      const cfg = await api.getConfig(eId);
      setConfig(cfg);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!config || !examId) return;
    setSaving(true);
    try {
      await api.updateConfig(examId, {
        model_name: config.model_name,
        full_match_threshold: config.full_match_threshold,
        partial_match_threshold: config.partial_match_threshold,
        or_selection_policy: config.or_selection_policy,
      });
      alert("Evaluation configuration updated.");
    } catch (err: any) {
      alert("Save Error: " + err.message);
    } finally {
      setSaving(false);
    }
  };

  if (!config)
    return (
      <div className="text-zinc-500 text-xs py-8">Loading configuration...</div>
    );

  return (
    <div className="max-w-3xl space-y-6">
      {/* Header */}
      <div className="bg-[#121316] border border-zinc-800 rounded-xl p-5 shadow-lg">
        <h1 className="text-xl font-extrabold text-zinc-100 tracking-tight flex items-center gap-2">
          <span>Evaluation</span>
          <span className="text-yellow-400">Settings</span>
        </h1>
        <p className="text-xs text-zinc-400 mt-0.5">
          Configure semantic evaluation thresholds, question resolution rules,
          and scoring parameters.
        </p>
      </div>

      <form
        onSubmit={handleSave}
        className="bg-[#121316] border border-zinc-800 rounded-xl p-6 space-y-5 shadow-lg"
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div>
            <label className="text-zinc-300 block mb-1 font-semibold">
              Semantic Model
            </label>
            <select
              value={config.model_name}
              onChange={(e) =>
                setConfig({ ...config, model_name: e.target.value })
              }
              className="w-full bg-[#18191D] border border-zinc-700 rounded-lg p-2.5 text-zinc-100 font-mono focus:outline-none focus:ring-2 focus:ring-yellow-400/30 focus:border-yellow-400"
            >
              <option value="all-MiniLM-L6-v2">
                all-MiniLM-L6-v2 (Sentence-BERT)
              </option>
              <option value="paraphrase-MiniLM-L6-v2">
                paraphrase-MiniLM-L6-v2 (Paraphrase)
              </option>
              <option value="Deterministic-TFIDF">
                Deterministic N-Gram Vector
              </option>
            </select>
          </div>

          <div>
            <label className="text-zinc-300 block mb-1 font-semibold">
              OR-Question Selection Policy
            </label>
            <select
              value={config.or_selection_policy}
              onChange={(e) =>
                setConfig({ ...config, or_selection_policy: e.target.value })
              }
              className="w-full bg-[#18191D] border border-zinc-700 rounded-lg p-2.5 text-zinc-100 focus:outline-none focus:ring-2 focus:ring-yellow-400/30 focus:border-yellow-400"
            >
              <option value="best_attempted">
                Best Attempted Mark (Recommended)
              </option>
              <option value="first_attempted">First Attempted Question</option>
            </select>
          </div>

          <div>
            <label className="text-zinc-300 block mb-1 font-semibold">
              Full Match Threshold (0.0 - 1.0)
            </label>
            <input
              type="number"
              step="0.01"
              min="0.50"
              max="1.0"
              value={config.full_match_threshold}
              onChange={(e) =>
                setConfig({
                  ...config,
                  full_match_threshold: parseFloat(e.target.value) || 0.78,
                })
              }
              className="w-full bg-[#18191D] border border-zinc-700 rounded-lg p-2.5 text-zinc-100 font-mono focus:outline-none focus:ring-2 focus:ring-yellow-400/30 focus:border-yellow-400"
            />
            <span className="text-[11px] text-zinc-500 mt-1 block">
              Default: 0.78 (≥78% similarity receives full mark)
            </span>
          </div>

          <div>
            <label className="text-zinc-300 block mb-1 font-semibold">
              Partial Match Threshold (0.0 - 1.0)
            </label>
            <input
              type="number"
              step="0.01"
              min="0.20"
              max="0.80"
              value={config.partial_match_threshold}
              onChange={(e) =>
                setConfig({
                  ...config,
                  partial_match_threshold: parseFloat(e.target.value) || 0.52,
                })
              }
              className="w-full bg-[#18191D] border border-zinc-700 rounded-lg p-2.5 text-zinc-100 font-mono focus:outline-none focus:ring-2 focus:ring-yellow-400/30 focus:border-yellow-400"
            />
            <span className="text-[11px] text-zinc-500 mt-1 block">
              Default: 0.52 (52%-78% receives partial mark)
            </span>
          </div>
        </div>

        <div className="flex justify-end pt-4 border-t border-zinc-800">
          <button
            type="submit"
            disabled={saving}
            className="px-5 py-2 bg-yellow-400 hover:bg-yellow-300 text-zinc-950 text-xs font-bold rounded-lg flex items-center gap-1.5 shadow-md shadow-yellow-500/10 transition-all active:scale-[0.98] disabled:opacity-50"
          >
            <Save className="w-3.5 h-3.5 text-zinc-950" />
            <span>{saving ? "Saving..." : "Save Settings"}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
