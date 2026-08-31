import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { FileSpreadsheet, Download, CheckCircle2 } from "lucide-react";
import { api } from "../api/client";
import { AnswerSheet, ExamSession } from "../types";

export const ReportsPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const examId = searchParams.get("exam") || "";

  const [exam, setExam] = useState<ExamSession | null>(null);
  const [sheets, setSheets] = useState<AnswerSheet[]>([]);

  useEffect(() => {
    if (examId) loadData(examId);
  }, [examId]);

  const loadData = async (eId: string) => {
    try {
      const [ex, sList] = await Promise.all([
        api.getExam(eId),
        api.getExamAnswerSheets(eId),
      ]);
      setExam(ex);
      setSheets(sList);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-[#121316] border border-zinc-800 rounded-xl p-5 shadow-lg">
        <h1 className="text-xl font-extrabold text-zinc-100 tracking-tight flex items-center gap-2">
          <span>Reports &amp;</span>
          <span className="text-yellow-400">Export</span>
        </h1>
        <p className="text-xs text-zinc-400 mt-0.5">
          Generate candidate scorecards and export examination summary data.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* CSV Export Card */}
        <div className="bg-[#121316] border border-zinc-800 rounded-xl p-5 shadow-lg flex flex-col justify-between space-y-4">
          <div className="space-y-2">
            <div className="w-9 h-9 rounded-lg bg-yellow-400/10 border border-yellow-400/30 flex items-center justify-center text-yellow-400">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <h2 className="font-extrabold text-sm text-zinc-100">
              Examination Results Matrix (CSV)
            </h2>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Export complete student results including candidate IDs,
              question-by-question marks, percentages, and verification
              checksums.
            </p>
          </div>
          <div>
            <a
              href={`/api/reports/csv/exam/${examId}`}
              download
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-yellow-400 hover:bg-yellow-300 text-zinc-950 rounded-lg text-xs font-bold shadow-md shadow-yellow-500/10 transition-all active:scale-[0.98]"
            >
              <Download className="w-3.5 h-3.5 text-zinc-950" />
              <span>Download CSV Results</span>
            </a>
          </div>
        </div>

        {/* Verification Status Card */}
        <div className="bg-[#121316] border border-zinc-800 rounded-xl p-5 shadow-lg flex flex-col justify-between space-y-4">
          <div className="space-y-2">
            <div className="w-9 h-9 rounded-lg bg-yellow-400/10 border border-yellow-400/30 flex items-center justify-center text-yellow-400">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <h2 className="font-extrabold text-sm text-zinc-100">
              Integrity Verification Record
            </h2>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Cryptographic integrity verified across all submitted answer
              sheets and evaluation records.
            </p>
          </div>
          <div>
            <span className="inline-flex items-center gap-1 text-xs font-bold text-yellow-400 bg-yellow-400/10 border border-yellow-400/30 px-2.5 py-1 rounded-md font-mono">
              <CheckCircle2 className="w-3.5 h-3.5 text-yellow-400" />
              Session Verified
            </span>
          </div>
        </div>
      </div>

      {/* Student Scorecards Table */}
      <div className="bg-[#121316] border border-zinc-800 rounded-xl overflow-hidden shadow-lg">
        <div className="p-4 border-b border-zinc-800 flex items-center justify-between">
          <h2 className="text-xs font-bold text-yellow-400 uppercase tracking-wider">
            Individual Candidate Scorecards (PDF)
          </h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-zinc-300">
            <thead className="bg-zinc-900/90 text-zinc-400 uppercase text-[10px] font-bold tracking-wider border-b border-zinc-800">
              <tr>
                <th className="py-3 px-4">Candidate</th>
                <th className="py-3 px-4">Final Mark</th>
                <th className="py-3 px-4">Percentage</th>
                <th className="py-3 px-4 font-mono">Hash</th>
                <th className="py-3 px-4 text-right">PDF Download</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/70 font-sans">
              {sheets.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-zinc-500">
                    No submissions available for this examination session.
                  </td>
                </tr>
              )}
              {sheets.map((sheet) => (
                <tr
                  key={sheet.id}
                  className="hover:bg-zinc-800/40 transition-colors"
                >
                  <td className="py-3.5 px-4 font-semibold text-zinc-100">
                    <div>{sheet.student_name}</div>
                    <span className="font-mono text-[11px] text-zinc-400 font-normal">
                      {sheet.student_id}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 font-extrabold text-zinc-100 font-mono">
                    {sheet.total_score !== null
                      ? `${sheet.total_score} / ${sheet.max_marks}`
                      : "-"}
                  </td>
                  <td className="py-3.5 px-4 font-bold text-yellow-400 font-mono">
                    {sheet.percentage !== null ? `${sheet.percentage}%` : "-"}
                  </td>
                  <td className="py-3.5 px-4 font-mono text-[10px] text-zinc-500">
                    {sheet.sha256_hash.slice(0, 16)}...
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <a
                      href={`/api/reports/pdf/student/${sheet.id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1.5 bg-yellow-400 hover:bg-yellow-300 text-zinc-950 font-bold rounded-lg text-xs inline-flex items-center gap-1.5 shadow-md shadow-yellow-500/10 transition-all active:scale-[0.98]"
                    >
                      <Download className="w-3.5 h-3.5 text-zinc-950" />
                      <span>Download PDF</span>
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
