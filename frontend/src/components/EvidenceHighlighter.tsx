import React from "react";
import { ConceptEvaluation } from "../types";

interface EvidenceHighlighterProps {
  studentAnswerText: string;
  conceptEvaluations: ConceptEvaluation[];
}

export const EvidenceHighlighter: React.FC<EvidenceHighlighterProps> = ({
  studentAnswerText,
  conceptEvaluations,
}) => {
  if (!studentAnswerText) {
    return (
      <span className="text-zinc-500 italic text-xs">
        No answer submitted / unattempted.
      </span>
    );
  }

  const matchedSnippets = conceptEvaluations
    .filter((c) => c.matched_evidence && c.semantic_status !== "MISSING")
    .map((c) => ({
      code: c.concept_code,
      name: c.concept_name,
      status: c.semantic_status,
      evidence: c.matched_evidence!.trim(),
    }));

  return (
    <div className="font-sans text-xs text-zinc-200 leading-relaxed space-y-2">
      <div className="p-3.5 bg-[#18191D] rounded-lg border border-zinc-800 font-normal leading-relaxed text-zinc-200 shadow-inner">
        {studentAnswerText}
      </div>

      {matchedSnippets.length > 0 && (
        <div className="pt-1 flex flex-wrap gap-1.5 items-center">
          <span className="text-[10px] text-zinc-400 font-bold uppercase tracking-wider mr-1">
            Matched Concepts:
          </span>
          {matchedSnippets.map((snip, idx) => (
            <span
              key={idx}
              className={`text-[11px] px-2 py-0.5 rounded border ${
                snip.status === "FULL_MATCH"
                  ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30 font-medium"
                  : "bg-yellow-400/15 text-yellow-400 border-yellow-400/30 font-medium"
              }`}
            >
              <b className="font-mono">{snip.code}</b>: "
              {snip.evidence.slice(0, 40)}..."
            </span>
          ))}
        </div>
      )}
    </div>
  );
};
