import React, { useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  CheckCircle2,
  LayoutDashboard,
  Upload,
  CheckSquare,
  Award,
  AlertCircle,
  Settings,
  FileSpreadsheet,
  Layers,
  PlusCircle,
  RefreshCw,
  ChevronRight,
  User,
} from "lucide-react";
import { api } from "../api/client";
import { ExamSession } from "../types";

interface LayoutProps {
  children: React.ReactNode;
  selectedExamId?: string;
  onSelectExam?: (id: string) => void;
}

export const Layout: React.FC<LayoutProps> = ({
  children,
  selectedExamId,
  onSelectExam,
}) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [exams, setExams] = useState<ExamSession[]>([]);
  const [currentExamId, setCurrentExamId] = useState<string>(
    selectedExamId || "",
  );
  const [isSeeding, setIsSeeding] = useState(false);

  useEffect(() => {
    loadExams();
  }, []);

  const loadExams = async () => {
    try {
      const list = await api.listExams();
      setExams(list);
      if (list.length > 0 && !currentExamId) {
        const id = list[0].id;
        setCurrentExamId(id);
        if (onSelectExam) onSelectExam(id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleExamChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newId = e.target.value;
    setCurrentExamId(newId);
    if (onSelectExam) onSelectExam(newId);
  };

  const handleSeedDemo = async () => {
    if (confirm("Load demo examination and candidate answer sheets?")) {
      setIsSeeding(true);
      try {
        const res = await api.seedDemo();
        alert("Demo examination loaded successfully.");
        await loadExams();
        setCurrentExamId(res.exam_id);
        navigate(`/results?exam=${res.exam_id}`);
      } catch (err: any) {
        alert("Error loading demo: " + err.message);
      } finally {
        setIsSeeding(false);
      }
    }
  };

  const navItems = [
    { name: "Dashboard", path: "/", icon: LayoutDashboard },
    { name: "Examinations", path: "/exams", icon: Layers },
    { name: "New Examination", path: "/create-exam", icon: PlusCircle },
    {
      name: "Submissions",
      path: currentExamId
        ? `/answer-sheets?exam=${currentExamId}`
        : "/answer-sheets",
      icon: Upload,
    },
    {
      name: "OCR Review",
      path: currentExamId ? `/ocr-review?exam=${currentExamId}` : "/ocr-review",
      icon: CheckSquare,
    },
    {
      name: "Results",
      path: currentExamId ? `/results?exam=${currentExamId}` : "/results",
      icon: Award,
    },
    {
      name: "Review Queue",
      path: currentExamId
        ? `/review-queue?exam=${currentExamId}`
        : "/review-queue",
      icon: AlertCircle,
    },
    {
      name: "Audit Log",
      path: currentExamId ? `/audit?exam=${currentExamId}` : "/audit",
      icon: CheckCircle2,
    },
    {
      name: "Reports & Export",
      path: currentExamId ? `/reports?exam=${currentExamId}` : "/reports",
      icon: FileSpreadsheet,
    },
    {
      name: "Settings",
      path: currentExamId ? `/settings?exam=${currentExamId}` : "/settings",
      icon: Settings,
    },
  ];

  const activeExam = exams.find((e) => e.id === currentExamId);

  return (
    <div className="flex h-screen bg-[#090A0B] text-zinc-100 overflow-hidden font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-[#121316] border-r border-zinc-800/90 flex flex-col flex-shrink-0 z-20">
        {/* Brand Header */}
        <div className="p-4 border-b border-zinc-800 flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-yellow-400 text-zinc-950 flex items-center justify-center font-extrabold text-sm shadow-md shadow-yellow-500/20">
            EG
          </div>
          <div>
            <h1 className="font-bold text-sm text-zinc-100 leading-tight flex items-center gap-1.5">
              <span>Examination</span>
              <span className="text-yellow-400">Grading</span>
            </h1>
            <p className="text-[11px] text-zinc-400">Academic Assessment</p>
          </div>
        </div>

        {/* Active Exam Selector */}
        <div className="p-3 border-b border-zinc-800 bg-zinc-900/60">
          <label className="text-[10px] font-bold text-yellow-400 uppercase tracking-wider block mb-1">
            Active Examination
          </label>
          <select
            value={currentExamId}
            onChange={handleExamChange}
            className="w-full bg-[#18191D] border border-zinc-700 rounded-lg px-2.5 py-1.5 text-xs text-zinc-100 font-medium focus:outline-none focus:ring-2 focus:ring-yellow-400/30 focus:border-yellow-400 transition-all cursor-pointer truncate shadow-sm"
          >
            {exams.length === 0 && (
              <option value="">No examinations available</option>
            )}
            {exams.map((ex) => (
              <option
                key={ex.id}
                value={ex.id}
                className="bg-zinc-900 text-zinc-100"
              >
                {ex.name}
              </option>
            ))}
          </select>
          {activeExam && (
            <div className="mt-1.5 flex items-center justify-between text-[11px] text-zinc-400 font-medium px-0.5">
              <span className="truncate max-w-[130px]">
                {activeExam.subject}
              </span>
              <span className="font-bold text-yellow-400">
                {activeExam.total_marks} marks
              </span>
            </div>
          )}
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 px-3 py-3 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path.split("?")[0];
            return (
              <Link
                key={item.name}
                to={item.path}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs transition-all ${
                  isActive
                    ? "bg-yellow-400/10 text-yellow-400 font-bold border border-yellow-400/30 shadow-xs"
                    : "text-zinc-400 hover:bg-zinc-800/70 hover:text-zinc-100 font-medium"
                }`}
              >
                <Icon
                  className={`w-4 h-4 ${isActive ? "text-yellow-400" : "text-zinc-400"}`}
                />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* Action Button & System Status */}
        <div className="p-3 border-t border-zinc-800 bg-[#0E0F12] space-y-2.5">
          <button
            onClick={handleSeedDemo}
            disabled={isSeeding}
            className="w-full bg-yellow-400 hover:bg-yellow-300 text-zinc-950 font-bold text-xs py-2 px-3 rounded-lg flex items-center justify-center gap-1.5 transition-all shadow-md shadow-yellow-500/10 disabled:opacity-50 active:scale-[0.98]"
          >
            <RefreshCw
              className={`w-3.5 h-3.5 ${isSeeding ? "animate-spin" : ""}`}
            />
            <span>{isSeeding ? "Loading..." : "Load Demo Examination"}</span>
          </button>

          <div className="flex items-center justify-between text-[11px] text-zinc-400 px-1">
            <span className="flex items-center gap-1.5 text-zinc-300">
              <span className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse"></span>
              Semantic evaluation
            </span>
            <span className="text-zinc-500 font-mono">v1.2</span>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 bg-[#090A0B] overflow-hidden">
        {/* Top Header */}
        <header className="h-14 bg-[#121316] border-b border-zinc-800 px-6 flex items-center justify-between z-10">
          <div className="flex items-center gap-2 text-xs text-zinc-400">
            <span className="font-medium text-zinc-300">
              University Examination Board
            </span>
            <ChevronRight className="w-3.5 h-3.5 text-zinc-600" />
            <span className="text-yellow-400 font-semibold truncate max-w-sm">
              {activeExam?.name || "Examination Management"}
            </span>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5 bg-zinc-900 border border-yellow-400/25 px-3 py-1 rounded-full text-xs text-yellow-400 font-semibold shadow-xs">
              <CheckCircle2 className="w-3.5 h-3.5 text-yellow-400" />
              <span className="text-[11px]">Integrity verified</span>
            </div>

            <div className="flex items-center gap-2 pl-3 border-l border-zinc-800 text-xs">
              <div className="w-7 h-7 rounded-full bg-yellow-400/20 text-yellow-400 border border-yellow-400/40 flex items-center justify-center font-bold text-xs">
                AT
              </div>
              <div className="hidden sm:block">
                <p className="text-xs font-semibold text-zinc-200 leading-tight">
                  Prof. Alan Turing
                </p>
                <p className="text-[10px] text-zinc-400">Chief Examiner</p>
              </div>
            </div>
          </div>
        </header>

        {/* Page Body */}
        <main className="flex-1 overflow-y-auto p-6 bg-[#090A0B]">
          {children}
        </main>
      </div>
    </div>
  );
};
