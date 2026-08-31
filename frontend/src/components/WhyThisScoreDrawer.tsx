import React, { useEffect, useState } from "react";
import {
  X,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  SpellCheck,
  ArrowRight,
} from "lucide-react";
import { api } from "../api/client";
import { WhyThisScoreData } from "../types";

interface WhyThisScoreDrawerProps {
  questionEvaluationId: string | null;
  onClose: () => void;
}

export const WhyThisScoreDrawer: React.FC<WhyThisScoreDrawerProps> = ({
  questionEvaluationId,
  onClose,
}) => {
  const [data, setData] = useState<WhyThisScoreData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (questionEvaluationId) {
      loadData(questionEvaluationId);
    } else {
      setData(null);
    }
  }, [questionEvaluationId]);

  const loadData = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getWhyThisScore(id);
      setData(res);
    } catch (err: any) {
      setError(err.message || "Failed to load evaluation explanation");
    } finally {
      setLoading(false);
    }
  };

  if (!questionEvaluationId) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/70 backdrop-blur-xs flex justify-end transition-opacity">
      {/* Sliding Drawer Container */}
      <div className="w-full max-w-2xl bg-[#121316] border-l border-zinc-800 h-full shadow-2xl flex flex-col transform transition-transform duration-200 ease-out animate-in slide-in-from-right">
        {/* Drawer Header */}
        <div className="p-5 bg-[#18191D] border-b border-zinc-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-yellow-400/15 text-yellow-400 border border-yellow-400/30 flex items-center justify-center font-bold text-sm">
              <HelpCircle className="w-5 h-5 text-yellow-400" />
            </div>
            <div>
              <h2 className="text-base font-extrabold text-zinc-100 leading-tight flex items-center gap-2">
                <span>Why this mark?</span>
              </h2>
              <p className="text-xs text-zinc-400 mt-0.5">
                Question {data?.question_number || ""} &bull; Marking scheme
                breakdown and evidence
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Drawer Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {loading && (
            <div className="flex flex-col items-center justify-center py-20 text-zinc-400 space-y-3 text-xs">
              <div className="w-6 h-6 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin"></div>
              <p>Loading marking breakdown...</p>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
              {error}
            </div>
          )}

          {data && !loading && (
            <>
              {/* Question Summary & Final Mark */}
              <div className="bg-[#18191D] rounded-xl p-5 border border-zinc-800 flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <span className="text-xs font-bold text-yellow-400 uppercase tracking-wider block font-mono">
                    Question {data.question_number}
                  </span>
                  <p className="text-sm text-zinc-200 font-medium leading-relaxed">
                    "{data.question_text}"
                  </p>
                </div>
                <div className="text-right flex-shrink-0 bg-zinc-900 border border-zinc-700/80 px-4 py-2.5 rounded-xl shadow-inner">
                  <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider block">
                    Awarded Mark
                  </span>
                  <div className="text-2xl font-extrabold text-yellow-400 font-mono">
                    {data.is_overridden
                      ? data.teacher_final_score
                      : data.ai_score}
                    <span className="text-xs font-normal text-zinc-400 font-sans">
                      {" "}
                      / {data.question_max_marks}
                    </span>
                  </div>
                  {data.is_overridden && (
                    <span className="text-[10px] font-bold text-zinc-950 bg-yellow-400 px-1.5 py-0.5 rounded inline-block mt-1">
                      Manually adjusted
                    </span>
                  )}
                </div>
              </div>

              {/* 1. Mark Breakdown by Concept */}
              <div className="space-y-3">
                <h3 className="text-xs font-bold text-yellow-400 uppercase tracking-wider">
                  Mark Breakdown
                </h3>

                <div className="border border-zinc-800 rounded-xl overflow-hidden shadow-xs">
                  <table className="w-full text-left text-xs text-zinc-300">
                    <thead className="bg-zinc-900/90 text-zinc-400 font-bold border-b border-zinc-800 text-[10px] uppercase tracking-wider">
                      <tr>
                        <th className="py-2.5 px-3.5">Criterion / Concept</th>
                        <th className="py-2.5 px-3.5">Similarity</th>
                        <th className="py-2.5 px-3.5 text-right">Marks</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800/70">
                      {data.calculation_breakdown.map((concept) => (
                        <tr
                          key={concept.concept_code}
                          className="hover:bg-zinc-800/40 transition-colors"
                        >
                          <td className="py-2.5 px-3.5 font-medium text-zinc-200">
                            <span className="font-semibold text-zinc-100">
                              {concept.concept_name}
                            </span>
                            <span className="text-[11px] text-yellow-400/80 block font-mono">
                              ({concept.concept_code})
                            </span>
                          </td>
                          <td className="py-2.5 px-3.5 font-mono text-[11px] text-zinc-400">
                            {(concept.similarity_score * 100).toFixed(1)}%
                          </td>
                          <td className="py-2.5 px-3.5 text-right font-bold font-mono text-yellow-400">
                            {concept.awarded_marks} / {concept.max_marks}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* 2. Reasoning & Concept Explanations */}
              <div className="space-y-3">
                <h3 className="text-xs font-bold text-yellow-400 uppercase tracking-wider">
                  Reasoning
                </h3>

                <div className="space-y-2.5">
                  {data.calculation_breakdown.map((concept) => (
                    <div
                      key={concept.concept_code}
                      className="bg-[#18191D] border border-zinc-800 rounded-xl p-3.5 space-y-1.5 text-xs"
                    >
                      <div className="font-semibold text-zinc-100 flex items-center justify-between">
                        <span>{concept.concept_name}</span>
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                            concept.status === "FULL_MATCH"
                              ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                              : concept.status === "PARTIAL_MATCH"
                                ? "bg-yellow-400/15 text-yellow-400 border border-yellow-400/30"
                                : "bg-rose-500/15 text-rose-400 border border-rose-500/30"
                          }`}
                        >
                          {concept.status === "FULL_MATCH"
                            ? "Full Credit"
                            : concept.status === "PARTIAL_MATCH"
                              ? "Partial Credit"
                              : "Missing"}
                        </span>
                      </div>
                      <p className="text-zinc-300 leading-relaxed">
                        {concept.explanation}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* 3. Evidence from Candidate Answer */}
              <div className="space-y-3">
                <h3 className="text-xs font-bold text-yellow-400 uppercase tracking-wider">
                  Evidence from Candidate Answer
                </h3>

                <div className="space-y-2">
                  {data.calculation_breakdown
                    .filter((c) => c.matched_evidence)
                    .map((concept) => (
                      <div
                        key={concept.concept_code}
                        className="bg-[#18191D] border-l-3 border-yellow-400 border-y border-r border-zinc-800 rounded-lg p-3 text-xs"
                      >
                        <span className="text-[10px] font-bold text-yellow-400 uppercase tracking-wider block mb-1">
                          Matched for {concept.concept_name}:
                        </span>
                        <p className="text-zinc-200 italic leading-relaxed font-serif">
                          "{concept.matched_evidence}"
                        </p>
                      </div>
                    ))}
                </div>
              </div>

              {/* 4. Missing Elements */}
              {data.calculation_breakdown.some(
                (c) => c.missing_evidence && c.missing_evidence.length > 0,
              ) && (
                <div className="space-y-3">
                  <h3 className="text-xs font-bold text-rose-400 uppercase tracking-wider">
                    Missing Elements
                  </h3>

                  <div className="bg-rose-500/10 border border-rose-500/25 rounded-xl p-4 text-xs space-y-2">
                    {data.calculation_breakdown.map((concept) =>
                      concept.missing_evidence &&
                      concept.missing_evidence.length > 0 ? (
                        <div key={concept.concept_code} className="space-y-1">
                          <span className="font-semibold text-rose-300">
                            {concept.concept_name}:
                          </span>
                          <ul className="list-disc pl-5 space-y-0.5 text-rose-200">
                            {concept.missing_evidence.map((miss, idx) => (
                              <li key={idx}>{miss}</li>
                            ))}
                          </ul>
                        </div>
                      ) : null,
                    )}
                  </div>
                </div>
              )}

              {/* 5. Spelling & Linguistic Quality */}
              {data.spelling_score !== undefined && (
                <div className="bg-[#18191D] rounded-xl p-4 border border-zinc-800 space-y-3 text-xs">
                  <div className="flex items-center justify-between">
                    <h3 className="font-bold text-zinc-200 uppercase tracking-wider text-xs flex items-center gap-1.5">
                      <SpellCheck className="w-4 h-4 text-yellow-400" />
                      Spelling Accuracy
                    </h3>
                    <span className="font-bold text-yellow-400 bg-yellow-400/10 border border-yellow-400/30 px-2.5 py-0.5 rounded text-[11px] font-mono">
                      Accuracy: {data.spelling_score}%
                      {data.spelling_penalty_deducted
                        ? ` (-${data.spelling_penalty_deducted} mark)`
                        : ""}
                    </span>
                  </div>

                  {data.spelling_errors && data.spelling_errors.length > 0 ? (
                    <div className="space-y-1.5">
                      {data.spelling_errors.map((err, idx) => (
                        <div
                          key={idx}
                          className="bg-zinc-900 border border-zinc-800 rounded-lg p-2.5 flex items-center justify-between text-xs"
                        >
                          <div className="flex items-center gap-2">
                            <span className="line-through text-rose-400 font-mono">
                              {err.word}
                            </span>
                            <ArrowRight className="w-3 h-3 text-zinc-500" />
                            <span className="text-emerald-400 font-bold font-mono">
                              {err.suggested_correction}
                            </span>
                          </div>
                          <span className="text-[11px] text-zinc-400 italic max-w-xs truncate">
                            "{err.context}"
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-[11px] text-emerald-400 flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      All words and terms spelled correctly.
                    </p>
                  )}
                </div>
              )}

              {/* 6. Technical Evaluation Details */}
              <div className="bg-[#18191D] rounded-xl p-4 border border-zinc-800 space-y-2 text-xs">
                <h3 className="font-bold text-zinc-400 uppercase tracking-wider text-[10px]">
                  Evaluation Details
                </h3>
                <div className="grid grid-cols-2 gap-2 text-zinc-300 text-[11px]">
                  <div>
                    <span className="font-semibold text-zinc-400 block text-[10px] uppercase">
                      Method:
                    </span>
                    <span>Semantic evaluation</span>
                  </div>
                  <div>
                    <span className="font-semibold text-zinc-400 block text-[10px] uppercase">
                      Model:
                    </span>
                    <span className="font-mono text-[10px] text-yellow-400">
                      {data.semantic_model}
                    </span>
                  </div>
                  <div>
                    <span className="font-semibold text-zinc-400 block text-[10px] uppercase">
                      Confidence:
                    </span>
                    <span className="font-medium text-emerald-400">
                      {data.confidence_level}
                    </span>
                  </div>
                  <div>
                    <span className="font-semibold text-zinc-400 block text-[10px] uppercase">
                      Aggregation:
                    </span>
                    <span className="font-mono text-[10px]">
                      {data.calculation_formula}
                    </span>
                  </div>
                </div>
                {data.evaluation_hash && (
                  <div className="pt-2 border-t border-zinc-800 font-mono text-[10px] text-zinc-500 break-all">
                    Checksum: {data.evaluation_hash}
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* Drawer Footer */}
        <div className="p-4 bg-[#18191D] border-t border-zinc-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-yellow-400 hover:bg-yellow-300 text-zinc-950 text-xs font-bold rounded-lg transition-all shadow-md shadow-yellow-500/10 active:scale-[0.98]"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
