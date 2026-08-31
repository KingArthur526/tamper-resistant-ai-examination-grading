import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Layers,
  Upload,
  Award,
  CheckCircle2,
  Plus,
  ArrowRight,
  AlertCircle,
} from "lucide-react";
import { api } from "../api/client";
import { DashboardStats } from "../types";

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    setLoading(true);
    try {
      const res = await api.getDashboardStats();
      setStats(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header Banner */}
      <div className="bg-[#121316] border border-zinc-800 rounded-xl p-6 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-zinc-100 tracking-tight flex items-center gap-2">
            <span>Examination</span>
            <span className="text-yellow-400">Grading Dashboard</span>
          </h1>
          <p className="text-xs text-zinc-400 mt-1">
            Review submissions, evaluate answers, and verify results across
            active academic sessions.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/create-exam"
            className="bg-yellow-400 hover:bg-yellow-300 text-zinc-950 text-xs font-bold px-4 py-2.5 rounded-lg flex items-center gap-2 shadow-md shadow-yellow-500/20 transition-all active:scale-[0.98]"
          >
            <Plus className="w-4 h-4 text-zinc-950" />
            <span>New Examination</span>
          </Link>
          <Link
            to="/exams"
            className="bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-zinc-100 border border-zinc-700 text-xs font-semibold px-4 py-2.5 rounded-lg transition-colors"
          >
            <span>All Examinations</span>
          </Link>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-[#121316] border border-zinc-800 rounded-xl p-4 shadow-md flex flex-col justify-between hover:border-zinc-700 transition-colors">
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-zinc-400">
              Active Examinations
            </span>
            <div className="w-7 h-7 rounded-lg bg-yellow-400/10 border border-yellow-400/20 flex items-center justify-center text-yellow-400">
              <Layers className="w-3.5 h-3.5" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-extrabold text-zinc-100 font-mono">
              {stats?.total_exams ?? 0}
            </div>
            <p className="text-xs text-zinc-400 mt-0.5">
              {stats?.active_exams ?? 0} in progress
            </p>
          </div>
        </div>

        <div className="bg-[#121316] border border-zinc-800 rounded-xl p-4 shadow-md flex flex-col justify-between hover:border-zinc-700 transition-colors">
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-zinc-400">
              Submissions
            </span>
            <div className="w-7 h-7 rounded-lg bg-zinc-800 flex items-center justify-center text-zinc-300">
              <Upload className="w-3.5 h-3.5" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-extrabold text-zinc-100 font-mono">
              {stats?.total_answer_sheets ?? 0}
            </div>
            <p className="text-xs text-zinc-400 mt-0.5">Across all sessions</p>
          </div>
        </div>

        <div className="bg-[#121316] border border-zinc-800 rounded-xl p-4 shadow-md flex flex-col justify-between hover:border-zinc-700 transition-colors">
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-zinc-400">
              Evaluated
            </span>
            <div className="w-7 h-7 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <CheckCircle2 className="w-3.5 h-3.5" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-extrabold text-emerald-400 font-mono">
              {stats?.completed_evaluations ?? 0}
            </div>
            <p className="text-xs text-zinc-400 mt-0.5">Graded and recorded</p>
          </div>
        </div>

        <div className="bg-[#121316] border border-zinc-800 rounded-xl p-4 shadow-md flex flex-col justify-between hover:border-zinc-700 transition-colors">
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-zinc-400">
              Items for Review
            </span>
            <div className="w-7 h-7 rounded-lg bg-yellow-400/10 border border-yellow-400/20 flex items-center justify-center text-yellow-400">
              <AlertCircle className="w-3.5 h-3.5" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-extrabold text-yellow-400 font-mono">
              {stats?.pending_evaluations ?? 0}
            </div>
            <p className="text-xs text-zinc-400 mt-0.5">
              Awaiting verification
            </p>
          </div>
        </div>

        <div className="bg-[#121316] border border-zinc-800 rounded-xl p-4 shadow-md flex flex-col justify-between hover:border-zinc-700 transition-colors">
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-zinc-400">
              Average Mark
            </span>
            <div className="w-7 h-7 rounded-lg bg-yellow-400/15 border border-yellow-400/30 flex items-center justify-center text-yellow-400">
              <Award className="w-3.5 h-3.5" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-extrabold text-yellow-400 font-mono">
              {stats?.average_marks_percentage ?? 0}%
            </div>
            <p className="text-xs text-zinc-400 mt-0.5">Cohort overall mean</p>
          </div>
        </div>
      </div>

      {/* Examinations Table */}
      <div className="bg-[#121316] border border-zinc-800 rounded-xl shadow-lg overflow-hidden">
        <div className="p-5 border-b border-zinc-800 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-zinc-100 flex items-center gap-2">
              <span>Recent Examinations</span>
            </h2>
            <p className="text-xs text-zinc-400 mt-0.5">
              Current assessment sessions and evaluation status
            </p>
          </div>
          <Link
            to="/exams"
            className="text-xs font-semibold text-yellow-400 hover:text-yellow-300 flex items-center gap-1 transition-colors"
          >
            <span>View all</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-zinc-300">
            <thead className="bg-zinc-900/90 text-zinc-400 uppercase text-[10px] font-bold tracking-wider border-b border-zinc-800">
              <tr>
                <th className="py-3 px-4">Examination</th>
                <th className="py-3 px-4">Course / Subject</th>
                <th className="py-3 px-4">Date</th>
                <th className="py-3 px-4">Total Marks</th>
                <th className="py-3 px-4">Submissions</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/70">
              {stats?.recent_exams?.length === 0 && (
                <tr>
                  <td
                    colSpan={7}
                    className="py-8 text-center text-zinc-500 text-xs"
                  >
                    No examination sessions created yet. Click "Load Demo
                    Examination" in the sidebar to load demo data.
                  </td>
                </tr>
              )}
              {stats?.recent_exams?.map((exam) => (
                <tr
                  key={exam.id}
                  className="hover:bg-zinc-800/40 transition-colors"
                >
                  <td className="py-3.5 px-4 font-semibold text-zinc-100">
                    {exam.name}
                  </td>
                  <td className="py-3.5 px-4 text-zinc-300">
                    <div className="font-medium text-zinc-200">
                      {exam.subject}
                    </div>
                    <span className="text-[11px] text-zinc-400">
                      {exam.course_semester}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-zinc-400 font-mono text-[11px]">
                    {exam.exam_date}
                  </td>
                  <td className="py-3.5 px-4 font-bold text-zinc-100 font-mono">
                    {exam.total_marks}
                  </td>
                  <td className="py-3.5 px-4 text-zinc-300 font-mono">
                    {exam.total_answer_sheets || 0}
                  </td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`inline-flex items-center gap-1.5 text-[11px] font-semibold px-2.5 py-0.5 rounded-full ${
                        exam.status === "COMPLETED"
                          ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                          : exam.status === "READY"
                            ? "bg-yellow-400/15 text-yellow-400 border border-yellow-400/30"
                            : "bg-zinc-800 text-zinc-400 border border-zinc-700"
                      }`}
                    >
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          exam.status === "COMPLETED"
                            ? "bg-emerald-400"
                            : "bg-yellow-400"
                        }`}
                      ></span>
                      {exam.status === "COMPLETED"
                        ? "Evaluated"
                        : exam.status === "READY"
                          ? "Ready"
                          : exam.status}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-right space-x-2">
                    <button
                      onClick={() => navigate(`/results?exam=${exam.id}`)}
                      className="px-3 py-1 bg-yellow-400/10 hover:bg-yellow-400/20 text-yellow-400 border border-yellow-400/30 rounded-lg text-xs font-semibold transition-colors"
                    >
                      View Results
                    </button>
                    <button
                      onClick={() => navigate(`/ocr-review?exam=${exam.id}`)}
                      className="px-3 py-1 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700 rounded-lg text-xs font-semibold transition-colors"
                    >
                      OCR Review
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
