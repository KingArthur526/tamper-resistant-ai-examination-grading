import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Check, ChevronRight } from "lucide-react";
import { RubricBuilder, QuestionFormItem } from "../components/RubricBuilder";
import { api } from "../api/client";

export const CreateExamWizard: React.FC = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);

  const [name, setName] = useState(
    "Final Semester Examination - Database Systems",
  );
  const [subject, setSubject] = useState("CS302 Database Management Systems");
  const [courseSemester, setCourseSemester] = useState("B.Tech CS - Sem 5");
  const [academicYear, setAcademicYear] = useState("2025-2026");
  const [examDate, setExamDate] = useState("2026-06-10");
  const [description, setDescription] = useState(
    "Descriptive evaluation of relational query optimization and transactions.",
  );

  const [questions, setQuestions] = useState<QuestionFormItem[]>([
    {
      question_number: "1",
      question_text:
        "Explain the ACID properties of database transactions and describe how WAL ensures atomicity and durability.",
      max_marks: 10,
      question_type: "DESCRIPTIVE",
      concepts: [
        {
          concept_code: "C1.1",
          name: "ACID Properties Definition",
          reference_text:
            "ACID stands for Atomicity (all-or-nothing), Consistency (integrity constraints), Isolation (concurrent independence), and Durability (committed persistence).",
          max_marks: 5,
          full_match_threshold: 0.78,
          partial_match_threshold: 0.52,
          keywords: "Atomicity, Consistency, Isolation, Durability",
        },
        {
          concept_code: "C1.2",
          name: "Write-Ahead Logging (WAL) Protocol",
          reference_text:
            "Write-Ahead Logging ensures that log records are written to non-volatile disk before data pages are modified, allowing redo/undo crash recovery.",
          max_marks: 5,
          full_match_threshold: 0.78,
          partial_match_threshold: 0.52,
          keywords:
            "Write-Ahead Logging, log records, redo undo, crash recovery",
        },
      ],
    },
  ]);

  const totalCalculatedMarks = questions.reduce(
    (sum, q) => sum + (Number(q.max_marks) || 0),
    0,
  );

  const handleCreate = async () => {
    for (const q of questions) {
      const cSum = q.concepts.reduce(
        (s, c) => s + (Number(c.max_marks) || 0),
        0,
      );
      if (Math.abs(cSum - q.max_marks) > 0.01) {
        alert(
          `Question ${q.question_number} concepts total (${cSum}) does not match question max (${q.max_marks}). Please fix before saving.`,
        );
        return;
      }
    }

    setSubmitting(true);
    try {
      const payload = {
        name,
        subject,
        course_semester: courseSemester,
        academic_year: academicYear,
        exam_date: examDate,
        description,
        questions: questions.map((q) => ({
          question_number: q.question_number,
          question_text: q.question_text,
          max_marks: q.max_marks,
          question_type: q.question_type,
          rubric_concepts: q.concepts.map((c) => ({
            concept_code: c.concept_code,
            name: c.name,
            reference_text: c.reference_text,
            max_marks: c.max_marks,
            full_match_threshold: c.full_match_threshold,
            partial_match_threshold: c.partial_match_threshold,
            keywords: c.keywords
              ? c.keywords.split(",").map((s) => s.trim())
              : [],
          })),
        })),
      };

      const res = await api.createExam(payload);
      alert("Examination session and rubrics created successfully.");
      navigate(`/answer-sheets?exam=${res.id}`);
    } catch (e: any) {
      alert("Error creating exam: " + e.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-[#121316] border border-zinc-800 rounded-xl p-5 shadow-lg">
        <h1 className="text-xl font-extrabold text-zinc-100 tracking-tight flex items-center gap-2">
          <span>Create Examination</span>
          <span className="text-yellow-400">Session</span>
        </h1>
        <p className="text-xs text-zinc-400 mt-0.5">
          Define examination metadata, questions, and concept grading rubrics.
        </p>
      </div>

      {/* Step Tabs */}
      <div className="grid grid-cols-3 gap-2 bg-[#121316] p-1.5 rounded-xl border border-zinc-800">
        <button
          onClick={() => setStep(1)}
          className={`py-2 px-3 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
            step === 1
              ? "bg-yellow-400 text-zinc-950 font-bold shadow-md shadow-yellow-500/10"
              : "text-zinc-400 hover:text-zinc-100"
          }`}
        >
          <span
            className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] ${step === 1 ? "bg-zinc-950 text-yellow-400 font-extrabold" : "bg-zinc-800 text-zinc-400"}`}
          >
            1
          </span>
          <span>Exam Details</span>
        </button>

        <button
          onClick={() => setStep(2)}
          className={`py-2 px-3 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
            step === 2
              ? "bg-yellow-400 text-zinc-950 font-bold shadow-md shadow-yellow-500/10"
              : "text-zinc-400 hover:text-zinc-100"
          }`}
        >
          <span
            className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] ${step === 2 ? "bg-zinc-950 text-yellow-400 font-extrabold" : "bg-zinc-800 text-zinc-400"}`}
          >
            2
          </span>
          <span>Questions &amp; Rubrics</span>
        </button>

        <button
          onClick={() => setStep(3)}
          className={`py-2 px-3 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
            step === 3
              ? "bg-yellow-400 text-zinc-950 font-bold shadow-md shadow-yellow-500/10"
              : "text-zinc-400 hover:text-zinc-100"
          }`}
        >
          <span
            className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] ${step === 3 ? "bg-zinc-950 text-yellow-400 font-extrabold" : "bg-zinc-800 text-zinc-400"}`}
          >
            3
          </span>
          <span>Review &amp; Finalize</span>
        </button>
      </div>

      {step === 1 && (
        <div className="bg-[#121316] border border-zinc-800 rounded-xl p-6 shadow-lg space-y-4">
          <h2 className="text-sm font-bold text-yellow-400 uppercase tracking-wider">
            Step 1: Examination Details
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="sm:col-span-2">
              <label className="text-zinc-300 block mb-1 font-semibold">
                Examination Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full bg-[#18191D] border border-zinc-700 rounded-lg p-2.5 text-zinc-100 focus:outline-none focus:ring-2 focus:ring-yellow-400/30 focus:border-yellow-400"
                required
              />
            </div>
            <div>
              <label className="text-zinc-300 block mb-1 font-semibold">
                Subject
              </label>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="w-full bg-[#18191D] border border-zinc-700 rounded-lg p-2.5 text-zinc-100 focus:outline-none focus:ring-2 focus:ring-yellow-400/30 focus:border-yellow-400"
                required
              />
            </div>
            <div>
              <label className="text-zinc-300 block mb-1 font-semibold">
                Course / Semester
              </label>
              <input
                type="text"
                value={courseSemester}
                onChange={(e) => setCourseSemester(e.target.value)}
                className="w-full bg-[#18191D] border border-zinc-700 rounded-lg p-2.5 text-zinc-100 focus:outline-none focus:ring-2 focus:ring-yellow-400/30 focus:border-yellow-400"
                required
              />
            </div>
            <div>
              <label className="text-zinc-300 block mb-1 font-semibold">
                Academic Year
              </label>
              <input
                type="text"
                value={academicYear}
                onChange={(e) => setAcademicYear(e.target.value)}
                className="w-full bg-[#18191D] border border-zinc-700 rounded-lg p-2.5 text-zinc-100 font-mono focus:outline-none focus:ring-2 focus:ring-yellow-400/30 focus:border-yellow-400"
                required
              />
            </div>
            <div>
              <label className="text-zinc-300 block mb-1 font-semibold">
                Exam Date
              </label>
              <input
                type="date"
                value={examDate}
                onChange={(e) => setExamDate(e.target.value)}
                className="w-full bg-[#18191D] border border-zinc-700 rounded-lg p-2.5 text-zinc-100 font-mono focus:outline-none focus:ring-2 focus:ring-yellow-400/30 focus:border-yellow-400"
                required
              />
            </div>
            <div className="sm:col-span-2">
              <label className="text-zinc-300 block mb-1 font-semibold">
                Description
              </label>
              <textarea
                rows={3}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full bg-[#18191D] border border-zinc-700 rounded-lg p-2.5 text-zinc-100 focus:outline-none focus:ring-2 focus:ring-yellow-400/30 focus:border-yellow-400"
              />
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t border-zinc-800">
            <button
              type="button"
              onClick={() => setStep(2)}
              className="px-5 py-2.5 bg-yellow-400 hover:bg-yellow-300 text-zinc-950 text-xs font-bold rounded-lg flex items-center gap-1.5 shadow-md shadow-yellow-500/10 transition-all active:scale-[0.98]"
            >
              <span>Continue to Question Rubrics</span>
              <ChevronRight className="w-4 h-4 text-zinc-950" />
            </button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-4">
          <RubricBuilder questions={questions} onChange={setQuestions} />
          <div className="flex justify-between pt-4">
            <button
              type="button"
              onClick={() => setStep(1)}
              className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700 text-xs font-semibold rounded-lg shadow-xs transition-colors"
            >
              Back
            </button>
            <button
              type="button"
              onClick={() => setStep(3)}
              className="px-5 py-2.5 bg-yellow-400 hover:bg-yellow-300 text-zinc-950 text-xs font-bold rounded-lg flex items-center gap-1.5 shadow-md shadow-yellow-500/10 transition-all active:scale-[0.98]"
            >
              <span>Review Examination</span>
              <ChevronRight className="w-4 h-4 text-zinc-950" />
            </button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="bg-[#121316] border border-zinc-800 rounded-xl p-6 shadow-lg space-y-6">
          <h2 className="text-sm font-bold text-yellow-400 uppercase tracking-wider">
            Step 3: Review &amp; Finalize
          </h2>

          <div className="bg-[#18191D] p-4 rounded-lg border border-zinc-800 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div>
              <span className="text-zinc-400 text-[10px] block font-bold uppercase tracking-wider">
                Subject:
              </span>
              <span className="font-semibold text-zinc-100">{subject}</span>
            </div>
            <div>
              <span className="text-zinc-400 text-[10px] block font-bold uppercase tracking-wider">
                Academic Year:
              </span>
              <span className="font-mono text-yellow-400 font-bold">
                {academicYear}
              </span>
            </div>
            <div>
              <span className="text-zinc-400 text-[10px] block font-bold uppercase tracking-wider">
                Total Questions:
              </span>
              <span className="font-extrabold text-zinc-100 font-mono">
                {questions.length}
              </span>
            </div>
            <div>
              <span className="text-zinc-400 text-[10px] block font-bold uppercase tracking-wider">
                Total Marks:
              </span>
              <span className="font-extrabold text-yellow-400 font-mono">
                {totalCalculatedMarks} Marks
              </span>
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="text-xs font-bold text-yellow-400 uppercase tracking-wider">
              Configured Questions:
            </h3>
            {questions.map((q, idx) => (
              <div
                key={idx}
                className="bg-[#18191D] border border-zinc-800 rounded-lg p-3 text-xs space-y-1"
              >
                <div className="flex items-center justify-between font-bold text-zinc-100">
                  <span className="font-mono text-yellow-400">
                    Question {q.question_number}
                  </span>
                  <span className="text-zinc-400 font-medium font-mono">
                    {q.max_marks} marks ({q.concepts.length} concepts)
                  </span>
                </div>
                <p className="text-zinc-300">{q.question_text}</p>
              </div>
            ))}
          </div>

          <div className="flex justify-between pt-4 border-t border-zinc-800">
            <button
              type="button"
              onClick={() => setStep(2)}
              className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700 text-xs font-semibold rounded-lg shadow-xs transition-colors"
            >
              Back
            </button>
            <button
              type="button"
              onClick={handleCreate}
              disabled={submitting}
              className="px-6 py-2.5 bg-yellow-400 hover:bg-yellow-300 text-zinc-950 text-xs font-bold rounded-lg flex items-center gap-2 shadow-md shadow-yellow-500/10 transition-all active:scale-[0.98] disabled:opacity-50"
            >
              <Check className="w-4 h-4 text-zinc-950" />
              <span>
                {submitting
                  ? "Creating Session..."
                  : "Create Examination Session"}
              </span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
