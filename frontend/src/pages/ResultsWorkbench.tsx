import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Award,
  HelpCircle,
  Edit3,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Search,
  SpellCheck,
  Copy,
  Check,
} from "lucide-react";
import { api } from "../api/client";
import { AnswerSheet, StudentResultCard, QuestionEvaluation } from "../types";
import { WhyThisScoreDrawer } from "../components/WhyThisScoreDrawer";
import { OverrideModal } from "../components/OverrideModal";
import { EvidenceHighlighter } from "../components/EvidenceHighlighter";

export const ResultsWorkbench: React.FC = () => {
  const [searchParams] = useSearchParams();
  const examId = searchParams.get("exam") || "";
  const initialSheetId = searchParams.get("sheet") || "";

  const [sheets, setSheets] = useState<AnswerSheet[]>([]);
  const [activeSheetId, setActiveSheetId] = useState<string>(initialSheetId);
  const [resultCard, setResultCard] = useState<StudentResultCard | null>(null);
  const [loading, setLoading] = useState(false);
  const [isEvaluatingAll, setIsEvaluatingAll] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [copiedHash, setCopiedHash] = useState(false);

  const [selectedQuestionEvalId, setSelectedQuestionEvalId] = useState<
    string | null
  >(null);
  const [overrideTarget, setOverrideTarget] =
    useState<QuestionEvaluation | null>(null);

  useEffect(() => {
    if (examId) loadSheets(examId);
  }, [examId]);

  useEffect(() => {
    if (activeSheetId) loadResultCard(activeSheetId);
  }, [activeSheetId]);

  const loadSheets = async (eId: string) => {
    try {
      const list = await api.getExamAnswerSheets(eId);
      setSheets(list);
      if (list.length > 0 && !activeSheetId) {
        setActiveSheetId(list[0].id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const loadResultCard = async (sId: string) => {
    setLoading(true);
    try {
      const card = await api.getStudentResults(sId);
      setResultCard(card);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluateAll = async () => {
    if (!examId) return;
    setIsEvaluatingAll(true);
    try {
      await api.evaluateExam(examId);
      alert("Evaluation completed for all candidate submissions.");
      await loadSheets(examId);
      if (activeSheetId) await loadResultCard(activeSheetId);
    } catch (err: any) {
      alert("Evaluation error: " + err.message);
    } finally {
      setIsEvaluatingAll(false);
    }
  };

  const handleCopyHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  const filteredSheets = sheets.filter(
    (s) =>
      s.student_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.student_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (s.roll_number &&
        s.roll_number.toLowerCase().includes(searchQuery.toLowerCase())),
  );

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-[#121316] border border-zinc-800 rounded-xl p-5 shadow-lg flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-extrabold text-zinc-100 tracking-tight flex items-center gap-2">
            <span>Examination Results</span>
            <span className="text-yellow-400">&amp; Grading</span>
          </h1>
          <p className="text-xs text-zinc-400 mt-0.5">
            Review candidate answer scripts, inspect evaluation evidence, and
            record official marks.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleEvaluateAll}
            disabled={isEvaluatingAll || !examId}
            className="bg-yellow-400 hover:bg-yellow-300 text-zinc-950 text-xs font-bold px-4 py-2.5 rounded-lg flex items-center gap-2 shadow-md shadow-yellow-500/20 transition-all disabled:opacity-50 active:scale-[0.98]"
          >
            <RefreshCw
              className={`w-3.5 h-3.5 ${isEvaluatingAll ? "animate-spin" : ""}`}
            />
            <span>
              {isEvaluatingAll
                ? "Evaluating..."
                : "Re-Evaluate All Submissions"}
            </span>
          </button>
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Column: Submissions List */}
        <div className="lg:col-span-1 bg-[#121316] border border-zinc-800 rounded-xl p-4 shadow-md flex flex-col h-[780px]">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-xs font-bold text-yellow-400 uppercase tracking-wider">
              Submissions ({sheets.length})
            </h2>
          </div>

          <div className="relative mb-3">
            <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search candidate name or ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[#18191D] border border-zinc-700 rounded-lg pl-8 pr-3 py-1.5 text-xs text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-yellow-400/30 focus:border-yellow-400 transition-all"
            />
          </div>

          <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
            {filteredSheets.length === 0 && (
              <div className="py-8 text-center text-zinc-500 text-xs">
                No submissions found.
              </div>
            )}
            {filteredSheets.map((sheet) => {
              const isSelected = sheet.id === activeSheetId;
              return (
                <button
                  key={sheet.id}
                  onClick={() => setActiveSheetId(sheet.id)}
                  className={`w-full text-left p-3 rounded-lg border transition-all ${
                    isSelected
                      ? "bg-yellow-400/10 border-yellow-400/50 text-zinc-100 shadow-md shadow-yellow-500/5"
                      : "bg-[#18191D]/50 border-zinc-800/80 text-zinc-300 hover:bg-zinc-800/60 hover:border-zinc-700"
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div
                        className={`font-semibold text-xs leading-tight ${isSelected ? "text-yellow-400" : "text-zinc-100"}`}
                      >
                        {sheet.student_name}
                      </div>
                      <span className="font-mono text-[11px] text-zinc-400">
                        {sheet.student_id}
                      </span>
                    </div>
                    {sheet.percentage !== null &&
                    sheet.percentage !== undefined ? (
                      <span
                        className={`font-bold font-mono text-xs px-2 py-0.5 rounded ${
                          sheet.percentage >= 70
                            ? "text-emerald-400 bg-emerald-500/10 border border-emerald-500/30"
                            : sheet.percentage >= 50
                              ? "text-yellow-400 bg-yellow-400/10 border border-yellow-400/30"
                              : "text-rose-400 bg-rose-500/10 border border-rose-500/30"
                        }`}
                      >
                        {sheet.percentage}%
                      </span>
                    ) : (
                      <span className="text-[11px] text-zinc-500">Pending</span>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right Column: Detailed Candidate Workspace */}
        <div className="lg:col-span-3 space-y-5">
          {loading && (
            <div className="bg-[#121316] border border-zinc-800 rounded-xl p-12 text-center text-zinc-400 text-xs shadow-md">
              Loading evaluation results...
            </div>
          )}

          {!loading && !resultCard && (
            <div className="bg-[#121316] border border-zinc-800 rounded-xl p-12 text-center text-zinc-400 text-xs shadow-md">
              Please select a candidate submission from the left list.
            </div>
          )}

          {!loading && resultCard && (
            <>
              {/* Candidate Overview Card */}
              <div className="bg-[#121316] border border-zinc-800 rounded-xl p-6 shadow-md flex flex-col sm:flex-row sm:items-center justify-between gap-6">
                <div>
                  <div className="flex items-center gap-2.5">
                    <h2 className="text-lg font-extrabold text-zinc-100 tracking-tight">
                      {resultCard.student_name}
                    </h2>
                    <span className="font-mono text-xs text-yellow-400 bg-yellow-400/10 border border-yellow-400/30 px-2.5 py-0.5 rounded-full font-semibold">
                      {resultCard.student_id}{" "}
                      {resultCard.roll_number
                        ? `• ${resultCard.roll_number}`
                        : ""}
                    </span>
                  </div>
                  <p className="text-xs text-zinc-400 mt-1">
                    {resultCard.subject} &bull; {resultCard.session_name}
                  </p>
                  <div className="mt-2.5 flex items-center gap-2 text-[11px] text-zinc-400">
                    <span>Checksum:</span>
                    <button
                      onClick={() => handleCopyHash(resultCard.integrity_hash)}
                      className="font-mono text-[10px] text-zinc-300 bg-zinc-900 hover:bg-zinc-800 px-2 py-0.5 rounded border border-zinc-700 flex items-center gap-1 transition-colors"
                      title="Copy file hash"
                    >
                      {resultCard.integrity_hash
                        ? `${resultCard.integrity_hash.slice(0, 16)}...`
                        : "N/A"}
                      {copiedHash ? (
                        <Check className="w-3 h-3 text-yellow-400" />
                      ) : (
                        <Copy className="w-3 h-3 text-zinc-500" />
                      )}
                    </button>
                  </div>
                </div>

                <div className="flex items-center gap-6 bg-[#18191D] border border-zinc-700/80 px-5 py-3.5 rounded-xl shadow-inner">
                  <div className="text-right">
                    <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider block">
                      Awarded Mark
                    </span>
                    <div className="text-2xl font-extrabold text-yellow-400 font-mono">
                      {resultCard.total_teacher_score}
                      <span className="text-sm font-normal text-zinc-400">
                        {" "}
                        / {resultCard.total_max_marks}
                      </span>
                    </div>
                  </div>
                  <div className="text-right pl-6 border-l border-zinc-700">
                    <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider block">
                      Overall Result
                    </span>
                    <div className="text-2xl font-extrabold text-zinc-100 font-mono">
                      {resultCard.percentage}%
                    </div>
                  </div>
                </div>
              </div>

              {/* Questions List */}
              <div className="space-y-4">
                {resultCard.questions.map((qEval) => (
                  <div
                    key={qEval.id}
                    className="bg-[#121316] border border-zinc-800 hover:border-zinc-700/90 rounded-xl p-5 shadow-md space-y-4 transition-colors"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-zinc-800/80 gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-xs text-yellow-400 bg-yellow-400/10 border border-yellow-400/30 px-2.5 py-0.5 rounded font-mono">
                            Question {qEval.question_number}
                          </span>
                          {qEval.is_overridden && (
                            <span className="text-[10px] font-bold bg-yellow-400 text-zinc-950 px-2 py-0.5 rounded">
                              Manually adjusted
                            </span>
                          )}
                          {qEval.spelling_score !== undefined && (
                            <span className="text-[10px] font-medium text-zinc-300 bg-zinc-900 border border-zinc-700 px-2 py-0.5 rounded flex items-center gap-1">
                              <SpellCheck className="w-3 h-3 text-yellow-400" />
                              Spelling: {qEval.spelling_score}%
                            </span>
                          )}
                        </div>
                        <h3 className="text-sm font-medium text-zinc-200 mt-2">
                          "{qEval.question_text}"
                        </h3>
                      </div>

                      <div className="flex items-center gap-3 flex-shrink-0">
                        <div className="text-right">
                          <div className="text-lg font-extrabold text-yellow-400 font-mono">
                            {qEval.teacher_final_score}{" "}
                            <span className="text-xs text-zinc-400 font-normal">
                              / {qEval.max_marks}
                            </span>
                          </div>
                        </div>

                        <button
                          onClick={() => setSelectedQuestionEvalId(qEval.id)}
                          className="px-3.5 py-1.5 bg-yellow-400 hover:bg-yellow-300 text-zinc-950 text-xs font-bold rounded-lg flex items-center gap-1.5 transition-all shadow-md shadow-yellow-500/10 active:scale-[0.98]"
                        >
                          <HelpCircle className="w-3.5 h-3.5 text-zinc-950" />
                          <span>Why this mark?</span>
                        </button>
                        <button
                          onClick={() => setOverrideTarget(qEval)}
                          className="px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700 text-xs font-semibold rounded-lg flex items-center gap-1.5 transition-colors"
                        >
                          <Edit3 className="w-3.5 h-3.5 text-zinc-400" />
                          <span>Change mark</span>
                        </button>
                      </div>
                    </div>

                    {/* Student Answer Text & Evidence */}
                    <div className="space-y-1.5">
                      <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider block">
                        Candidate Answer Text
                      </span>
                      <EvidenceHighlighter
                        studentAnswerText={qEval.student_answer_text}
                        conceptEvaluations={qEval.concept_evaluations}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Why This Mark Drawer */}
      <WhyThisScoreDrawer
        questionEvaluationId={selectedQuestionEvalId}
        onClose={() => setSelectedQuestionEvalId(null)}
      />

      {/* Mark Override Modal */}
      {overrideTarget && (
        <OverrideModal
          questionEval={overrideTarget}
          onClose={() => setOverrideTarget(null)}
          onSuccess={() => {
            if (activeSheetId) loadResultCard(activeSheetId);
            if (examId) loadSheets(examId);
          }}
        />
      )}
    </div>
  );
};
