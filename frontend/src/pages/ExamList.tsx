import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Plus, Search, Trash2, ArrowRight } from "lucide-react";
import { api } from "../api/client";
import { ExamSession } from "../types";

export const ExamList: React.FC = () => {
  const [exams, setExams] = useState<ExamSession[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadExams();
  }, []);

  const loadExams = async () => {
    setLoading(true);
    try {
      const list = await api.listExams();
      setExams(list);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (
      confirm(
        "Delete this examination session and all associated files/evaluations?",
      )
    ) {
      try {
        await api.deleteExam(id);
        await loadExams();
      } catch (e: any) {
        alert("Error: " + e.message);
      }
    }
  };

  const filtered = exams.filter(
    (e) =>
      e.name.toLowerCase().includes(search.toLowerCase()) ||
      e.subject.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-[#121316] border border-zinc-800 rounded-xl p-5 shadow-lg flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-extrabold text-zinc-100 tracking-tight flex items-center gap-2">
            <span>Examination</span>
            <span className="text-yellow-400">Sessions</span>
          </h1>
          <p className="text-xs text-zinc-400 mt-0.5">
            Manage assessment sessions, rubrics, and candidate grading.
          </p>
        </div>
        <Link
          to="/create-exam"
          className="bg-yellow-400 hover:bg-yellow-300 text-zinc-950 text-xs font-bold px-4 py-2.5 rounded-lg flex items-center gap-1.5 shadow-md shadow-yellow-500/10 transition-all active:scale-[0.98]"
        >
          <Plus className="w-4 h-4 text-zinc-950" />
          <span>New Examination</span>
        </Link>
      </div>

      {/* Main Container */}
      <div className="bg-[#121316] border border-zinc-800 rounded-xl p-5 shadow-lg space-y-4">
        <div>
          <div className="relative">
            <Search className="w-4 h-4 text-zinc-500 absolute left-3 top-2.5" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search examinations by title or subject..."
              className="w-full bg-[#18191D] border border-zinc-700 rounded-lg pl-9 pr-4 py-2 text-xs text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-yellow-400/30 focus:border-yellow-400"
            />
          </div>
        </div>

        {loading && (
          <div className="py-12 text-center text-zinc-500 text-xs">
            Loading examination sessions...
          </div>
        )}

        {!loading && filtered.length === 0 && (
          <div className="py-12 text-center text-zinc-500 text-xs">
            No examinations found. Click "New Examination" or load the demo
            session.
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((exam) => (
            <div
              key={exam.id}
              className="bg-[#18191D] border border-zinc-800 hover:border-zinc-700 rounded-xl p-4 flex flex-col justify-between space-y-4 transition-colors"
            >
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-yellow-400 bg-yellow-400/10 border border-yellow-400/30 px-2 py-0.5 rounded font-bold">
                    {exam.academic_year}
                  </span>
                  <span
                    className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full ${
                      exam.status === "COMPLETED"
                        ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                        : "bg-yellow-400/15 text-yellow-400 border border-yellow-400/30"
                    }`}
                  >
                    {exam.status === "COMPLETED" ? "Completed" : "Active"}
                  </span>
                </div>
                <h2 className="font-extrabold text-sm text-zinc-100 leading-snug">
                  {exam.name}
                </h2>
                <p className="text-xs text-zinc-300">{exam.subject}</p>
                <p className="text-[11px] text-zinc-500">
                  {exam.course_semester}
                </p>
              </div>

              <div className="pt-3 border-t border-zinc-800 grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-zinc-400 text-[10px] block font-bold uppercase tracking-wider">
                    Max Marks:
                  </span>
                  <span className="font-extrabold text-yellow-400 font-mono">
                    {exam.total_marks}
                  </span>
                </div>
                <div>
                  <span className="text-zinc-400 text-[10px] block font-bold uppercase tracking-wider">
                    Submissions:
                  </span>
                  <span className="text-zinc-300 font-bold font-mono">
                    {exam.total_answer_sheets || 0}
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between pt-1">
                <button
                  onClick={() => handleDelete(exam.id)}
                  className="p-1.5 text-zinc-500 hover:text-rose-400 rounded-md hover:bg-zinc-800 transition-colors"
                  title="Delete Session"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => navigate(`/results?exam=${exam.id}`)}
                  className="px-3 py-1.5 bg-yellow-400 hover:bg-yellow-300 text-zinc-950 text-xs font-bold rounded-lg flex items-center gap-1 shadow-md shadow-yellow-500/10 transition-all active:scale-[0.98]"
                >
                  <span>Open Session</span>
                  <ArrowRight className="w-3 h-3 text-zinc-950" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
