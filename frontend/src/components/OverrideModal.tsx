import React, { useState } from "react";
import { X, Edit3 } from "lucide-react";
import { api } from "../api/client";
import { QuestionEvaluation } from "../types";

interface OverrideModalProps {
  questionEval: QuestionEvaluation | null;
  onClose: () => void;
  onSuccess: () => void;
}

export const OverrideModal: React.FC<OverrideModalProps> = ({
  questionEval,
  onClose,
  onSuccess,
}) => {
  const [newScore, setNewScore] = useState<string>(
    questionEval ? String(questionEval.teacher_final_score) : "",
  );
  const [reason, setReason] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!questionEval) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const scoreNum = parseFloat(newScore);
    if (isNaN(scoreNum) || scoreNum < 0 || scoreNum > questionEval.max_marks) {
      setError(`Mark must be a number between 0 and ${questionEval.max_marks}`);
      return;
    }
    if (!reason || reason.trim().length < 5) {
      setError(
        "A reason of at least 5 characters is required for audit records.",
      );
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await api.applyOverride(questionEval.id, {
        new_score: scoreNum,
        override_reason: reason.trim(),
      });
      alert("Mark adjusted and recorded to the audit log.");
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to apply override");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/75 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-[#121316] border border-zinc-800 rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95">
        {/* Header */}
        <div className="p-4 bg-[#18191D] border-b border-zinc-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-yellow-400/15 border border-yellow-400/30 flex items-center justify-center text-yellow-400">
              <Edit3 className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-zinc-100">
                Change Awarded Mark
              </h3>
              <p className="text-xs text-zinc-400">
                Question {questionEval.question_number} &bull; Maximum:{" "}
                {questionEval.max_marks} marks
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-zinc-100 p-1 rounded-md transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-3 bg-[#18191D] p-3 rounded-lg border border-zinc-800 text-xs">
            <div>
              <span className="text-zinc-400 text-[10px] font-bold uppercase tracking-wider block">
                Initial Mark:
              </span>
              <span className="font-extrabold text-zinc-300 text-base font-mono">
                {questionEval.ai_score} / {questionEval.max_marks}
              </span>
            </div>
            <div>
              <span className="text-zinc-400 text-[10px] font-bold uppercase tracking-wider block">
                Current Mark:
              </span>
              <span className="font-extrabold text-yellow-400 text-base font-mono">
                {questionEval.teacher_final_score} / {questionEval.max_marks}
              </span>
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-zinc-300 block mb-1">
              New Mark (0 - {questionEval.max_marks})
            </label>
            <input
              type="number"
              step="0.25"
              min="0"
              max={questionEval.max_marks}
              value={newScore}
              onChange={(e) => setNewScore(e.target.value)}
              className="w-full bg-[#18191D] border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 font-bold font-mono focus:outline-none focus:ring-2 focus:ring-yellow-400/30 focus:border-yellow-400"
              placeholder="e.g. 8.5"
              required
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-zinc-300 block mb-1">
              Reason for Override
            </label>
            <textarea
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full bg-[#18191D] border border-zinc-700 rounded-lg p-2.5 text-xs text-zinc-200 placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-yellow-400/30 focus:border-yellow-400"
              placeholder="Provide reason for adjustment (recorded in audit log)..."
              required
            />
          </div>

          <div className="pt-2 flex items-center justify-end gap-2.5">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-2 text-xs font-semibold text-zinc-400 hover:text-zinc-100 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 bg-yellow-400 hover:bg-yellow-300 text-zinc-950 font-bold text-xs rounded-lg transition-all shadow-md shadow-yellow-500/10 active:scale-[0.98] disabled:opacity-50"
            >
              {submitting ? "Saving..." : "Save Override"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
