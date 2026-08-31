import React, { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { AlertCircle } from "lucide-react";
import { api } from "../api/client";
import { WhyThisScoreDrawer } from "../components/WhyThisScoreDrawer";

export const ManualReviewQueue: React.FC = () => {
  const [searchParams] = useSearchParams();
  const examId = searchParams.get("exam") || "";
  const navigate = useNavigate();

  const [queue, setQueue] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEvalId, setSelectedEvalId] = useState<string | null>(null);

  useEffect(() => {
    if (examId) loadQueue(examId);
  }, [examId]);

  const loadQueue = async (eId: string) => {
    setLoading(true);
    try {
      const data = await api.getNeedsReviewQueue(eId);
      setQueue(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-[#121316] border border-zinc-800 rounded-xl p-5 shadow-lg">
        <h1 className="text-xl font-extrabold text-zinc-100 tracking-tight flex items-center gap-2">
          <span>Examiner</span>
          <span className="text-yellow-400">Review Queue</span>
        </h1>
        <p className="text-xs text-zinc-400 mt-0.5">
          Submissions flagged for examiner confirmation due to low OCR
          confidence or borderline scores.
        </p>
      </div>

      <div className="bg-[#121316] border border-zinc-800 rounded-xl overflow-hidden shadow-lg">
        <div className="p-4 border-b border-zinc-800 flex items-center justify-between">
          <h2 className="text-xs font-bold text-yellow-400 uppercase tracking-wider flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-yellow-400" />
            Flagged Items Awaiting Review ({queue.length})
          </h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-zinc-300">
            <thead className="bg-zinc-900/90 text-zinc-400 uppercase text-[10px] font-bold tracking-wider border-b border-zinc-800">
              <tr>
                <th className="py-3 px-4">Candidate</th>
                <th className="py-3 px-4">Question</th>
                <th className="py-3 px-4">Awarded Mark</th>
                <th className="py-3 px-4">Confidence</th>
                <th className="py-3 px-4">Flag Reasons</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/70 font-sans">
              {queue.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-zinc-500">
                    {loading
                      ? "Loading review queue..."
                      : "No items requiring review. All evaluations have high confidence."}
                  </td>
                </tr>
              )}
              {queue.map((item, idx) => (
                <tr
                  key={idx}
                  className="hover:bg-zinc-800/40 transition-colors"
                >
                  <td className="py-3.5 px-4 font-semibold text-zinc-100">
                    <div>{item.student_name}</div>
                    <span className="font-mono text-[11px] text-zinc-400 font-normal">
                      {item.student_id}
                    </span>
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="font-bold text-yellow-400 font-mono">
                      Question {item.question_number}
                    </span>
                    <p className="text-xs text-zinc-400 truncate max-w-xs">
                      {item.question_text}
                    </p>
                  </td>
                  <td className="py-3.5 px-4 font-extrabold text-zinc-100 font-mono">
                    {item.teacher_score}
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-yellow-400/15 text-yellow-400 border border-yellow-400/30">
                      {item.confidence_level}
                    </span>
                  </td>
                  <td className="py-3.5 px-4">
                    <ul className="list-disc list-inside text-xs text-rose-400 space-y-0.5">
                      {item.review_reasons?.map((r: string, rIdx: number) => (
                        <li key={rIdx}>{r}</li>
                      ))}
                    </ul>
                  </td>
                  <td className="py-3.5 px-4 text-right space-x-2">
                    <button
                      onClick={() =>
                        setSelectedEvalId(item.question_evaluation_id)
                      }
                      className="px-3 py-1 bg-yellow-400/10 hover:bg-yellow-400/20 text-yellow-400 border border-yellow-400/30 rounded-lg text-xs font-bold transition-colors"
                    >
                      Why this mark?
                    </button>
                    <button
                      onClick={() =>
                        navigate(`/results?sheet=${item.answer_sheet_id}`)
                      }
                      className="px-3 py-1 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700 rounded-lg text-xs font-semibold transition-colors"
                    >
                      View Script
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <WhyThisScoreDrawer
        questionEvaluationId={selectedEvalId}
        onClose={() => setSelectedEvalId(null)}
      />
    </div>
  );
};
