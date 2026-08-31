import React, { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import {
  Upload,
  FileText,
  CheckCircle2,
  AlertTriangle,
  Play,
  ArrowRight,
} from "lucide-react";
import { api } from "../api/client";
import { AnswerSheet } from "../types";

export const AnswerSheetUpload: React.FC = () => {
  const [searchParams] = useSearchParams();
  const examId = searchParams.get("exam") || "";
  const navigate = useNavigate();

  const [sheets, setSheets] = useState<AnswerSheet[]>([]);
  const [uploading, setUploading] = useState(false);
  const [studentId, setStudentId] = useState("");
  const [studentName, setStudentName] = useState("");
  const [rollNumber, setRollNumber] = useState("");
  const [file, setFile] = useState<File | null>(null);

  useEffect(() => {
    if (examId) loadSheets(examId);
  }, [examId]);

  const loadSheets = async (id: string) => {
    try {
      const res = await api.getExamAnswerSheets(id);
      setSheets(res);
    } catch (e) {
      console.error(e);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !examId) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("student_id", studentId);
      formData.append("student_name", studentName);
      formData.append("roll_number", rollNumber);

      await api.uploadAnswerSheet(examId, formData);
      alert("Answer sheet uploaded successfully.");
      setFile(null);
      setStudentId("");
      setStudentName("");
      setRollNumber("");
      await loadSheets(examId);
    } catch (err: any) {
      alert("Upload error: " + err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleProcessAllOCR = async () => {
    try {
      await api.processAllOCR(examId);
      alert("OCR processing started for all submissions.");
      await loadSheets(examId);
    } catch (e: any) {
      alert("OCR Error: " + e.message);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-[#121316] border border-zinc-800 rounded-xl p-5 shadow-lg flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-extrabold text-zinc-100 tracking-tight flex items-center gap-2">
            <span>Candidate</span>
            <span className="text-yellow-400">Submissions</span>
          </h1>
          <p className="text-xs text-zinc-400 mt-0.5">
            Upload scanned answer scripts and monitor evaluation status.
          </p>
        </div>
        {sheets.length > 0 && (
          <button
            onClick={handleProcessAllOCR}
            className="bg-yellow-400 hover:bg-yellow-300 text-zinc-950 text-xs font-bold px-4 py-2.5 rounded-lg flex items-center gap-1.5 shadow-md shadow-yellow-500/10 transition-all active:scale-[0.98]"
          >
            <Play className="w-3.5 h-3.5 text-zinc-950" />
            <span>Process OCR for All</span>
          </button>
        )}
      </div>

      {/* Upload Form Card */}
      <div className="bg-[#121316] border border-zinc-800 rounded-xl p-5 shadow-lg">
        <h2 className="text-xs font-bold text-yellow-400 uppercase tracking-wider mb-4 flex items-center gap-2">
          <Upload className="w-4 h-4 text-yellow-400" />
          Upload Scanned Answer Script (PDF / PNG / JPG)
        </h2>

        <form
          onSubmit={handleUpload}
          className="grid grid-cols-1 sm:grid-cols-4 gap-4 text-xs"
        >
          <div>
            <label className="text-zinc-300 block mb-1 font-semibold">
              Student ID
            </label>
            <input
              type="text"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
              className="w-full bg-[#18191D] border border-zinc-700 rounded-lg p-2 text-zinc-100 font-mono focus:outline-none focus:ring-2 focus:ring-yellow-400/30 focus:border-yellow-400"
              placeholder="e.g. STU-107"
              required
            />
          </div>
          <div>
            <label className="text-zinc-300 block mb-1 font-semibold">
              Candidate Name
            </label>
            <input
              type="text"
              value={studentName}
              onChange={(e) => setStudentName(e.target.value)}
              className="w-full bg-[#18191D] border border-zinc-700 rounded-lg p-2 text-zinc-100 focus:outline-none focus:ring-2 focus:ring-yellow-400/30 focus:border-yellow-400"
              placeholder="e.g. Grace Hopper"
              required
            />
          </div>
          <div>
            <label className="text-zinc-300 block mb-1 font-semibold">
              Roll Number
            </label>
            <input
              type="text"
              value={rollNumber}
              onChange={(e) => setRollNumber(e.target.value)}
              className="w-full bg-[#18191D] border border-zinc-700 rounded-lg p-2 text-zinc-100 font-mono focus:outline-none focus:ring-2 focus:ring-yellow-400/30 focus:border-yellow-400"
              placeholder="e.g. CS2026-007"
            />
          </div>
          <div>
            <label className="text-zinc-300 block mb-1 font-semibold">
              File
            </label>
            <input
              type="file"
              accept=".png,.jpg,.jpeg,.pdf"
              onChange={(e) =>
                setFile(e.target.files ? e.target.files[0] : null)
              }
              className="w-full bg-[#18191D] border border-zinc-700 rounded-lg p-1.5 text-zinc-300 text-xs file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-yellow-400 file:text-zinc-950 file:font-bold"
              required
            />
          </div>
          <div className="sm:col-span-4 flex justify-end">
            <button
              type="submit"
              disabled={uploading || !examId}
              className="px-5 py-2.5 bg-yellow-400 hover:bg-yellow-300 text-zinc-950 font-bold rounded-lg text-xs flex items-center gap-1.5 shadow-md shadow-yellow-500/10 transition-all active:scale-[0.98] disabled:opacity-50"
            >
              <Upload className="w-3.5 h-3.5 text-zinc-950" />
              <span>{uploading ? "Uploading..." : "Upload Submission"}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Submissions Table */}
      <div className="bg-[#121316] border border-zinc-800 rounded-xl overflow-hidden shadow-lg">
        <div className="p-4 border-b border-zinc-800 flex items-center justify-between">
          <h2 className="text-xs font-bold text-yellow-400 uppercase tracking-wider">
            Uploaded Scripts ({sheets.length})
          </h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-zinc-300">
            <thead className="bg-zinc-900/90 text-zinc-400 uppercase text-[10px] font-bold tracking-wider border-b border-zinc-800">
              <tr>
                <th className="py-3 px-4">Candidate</th>
                <th className="py-3 px-4">File Name</th>
                <th className="py-3 px-4 font-mono">Hash</th>
                <th className="py-3 px-4">OCR Confidence</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/70 font-sans">
              {sheets.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-zinc-500">
                    No submissions uploaded for this examination yet.
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
                      {sheet.student_id} ({sheet.roll_number || "N/A"})
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-zinc-300 font-mono text-[11px]">
                    {sheet.original_filename}
                  </td>
                  <td className="py-3.5 px-4 font-mono text-[10px] text-zinc-500">
                    {sheet.sha256_hash.slice(0, 16)}...
                  </td>
                  <td className="py-3.5 px-4 font-mono text-xs">
                    {sheet.ocr_confidence_avg > 0 ? (
                      <span
                        className={
                          sheet.ocr_confidence_avg >= 0.75
                            ? "text-emerald-400 font-bold"
                            : "text-yellow-400 font-bold"
                        }
                      >
                        {(sheet.ocr_confidence_avg * 100).toFixed(1)}%
                      </span>
                    ) : (
                      <span className="text-zinc-500">-</span>
                    )}
                  </td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full ${
                        sheet.processing_status === "EVALUATED"
                          ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                          : sheet.processing_status === "OCR_COMPLETED"
                            ? "bg-yellow-400/15 text-yellow-400 border border-yellow-400/30"
                            : sheet.processing_status === "NEEDS_OCR_REVIEW"
                              ? "bg-yellow-400/15 text-yellow-400 border border-yellow-400/30"
                              : "bg-zinc-800 text-zinc-400 border border-zinc-700"
                      }`}
                    >
                      {sheet.processing_status === "EVALUATED"
                        ? "Evaluated"
                        : sheet.processing_status === "OCR_COMPLETED"
                          ? "OCR Ready"
                          : sheet.processing_status === "NEEDS_OCR_REVIEW"
                            ? "Needs Review"
                            : sheet.processing_status}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-right space-x-2">
                    <button
                      onClick={() => navigate(`/ocr-review?sheet=${sheet.id}`)}
                      className="px-3 py-1 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700 rounded-lg text-xs font-semibold transition-colors"
                    >
                      OCR Review
                    </button>
                    <button
                      onClick={() => navigate(`/results?sheet=${sheet.id}`)}
                      className="px-3 py-1 bg-yellow-400/10 hover:bg-yellow-400/20 text-yellow-400 border border-yellow-400/30 rounded-lg text-xs font-semibold transition-colors"
                    >
                      Results
                    </button>
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
