import React from "react";
import { Plus, Trash2 } from "lucide-react";

export interface ConceptFormItem {
  concept_code: string;
  name: string;
  reference_text: string;
  max_marks: number;
  full_match_threshold: number;
  partial_match_threshold: number;
  keywords: string;
}

export interface QuestionFormItem {
  question_number: string;
  question_text: string;
  max_marks: number;
  question_type: string;
  concepts: ConceptFormItem[];
}

interface RubricBuilderProps {
  questions: QuestionFormItem[];
  onChange: (questions: QuestionFormItem[]) => void;
}

export const RubricBuilder: React.FC<RubricBuilderProps> = ({
  questions,
  onChange,
}) => {
  const addQuestion = () => {
    const nextNum = String(questions.length + 1);
    const newQ: QuestionFormItem = {
      question_number: nextNum,
      question_text: "",
      max_marks: 10,
      question_type: "DESCRIPTIVE",
      concepts: [
        {
          concept_code: `C${nextNum}.1`,
          name: "Core Concept & Definition",
          reference_text: "",
          max_marks: 5,
          full_match_threshold: 0.78,
          partial_match_threshold: 0.52,
          keywords: "",
        },
      ],
    };
    onChange([...questions, newQ]);
  };

  const removeQuestion = (qIdx: number) => {
    onChange(questions.filter((_, idx) => idx !== qIdx));
  };

  const updateQuestion = (qIdx: number, field: string, val: any) => {
    const updated = [...questions];
    updated[qIdx] = { ...updated[qIdx], [field]: val };
    onChange(updated);
  };

  const addConcept = (qIdx: number) => {
    const updated = [...questions];
    const q = updated[qIdx];
    const cNum = q.concepts.length + 1;
    q.concepts.push({
      concept_code: `C${q.question_number}.${cNum}`,
      name: `Concept ${cNum}`,
      reference_text: "",
      max_marks: 2,
      full_match_threshold: 0.78,
      partial_match_threshold: 0.52,
      keywords: "",
    });
    onChange(updated);
  };

  const removeConcept = (qIdx: number, cIdx: number) => {
    const updated = [...questions];
    updated[qIdx].concepts = updated[qIdx].concepts.filter(
      (_, idx) => idx !== cIdx,
    );
    onChange(updated);
  };

  const updateConcept = (
    qIdx: number,
    cIdx: number,
    field: string,
    val: any,
  ) => {
    const updated = [...questions];
    updated[qIdx].concepts[cIdx] = {
      ...updated[qIdx].concepts[cIdx],
      [field]: val,
    };
    onChange(updated);
  };

  return (
    <div className="space-y-6">
      {questions.map((q, qIdx) => {
        const conceptSum = q.concepts.reduce(
          (sum, c) => sum + (Number(c.max_marks) || 0),
          0,
        );
        const marksMatch = Math.abs(conceptSum - q.max_marks) < 0.01;

        return (
          <div
            key={qIdx}
            className="bg-[#121316] border border-zinc-800 rounded-xl p-5 shadow-lg space-y-4"
          >
            <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
              <div className="flex items-center gap-3">
                <span className="font-extrabold text-sm text-zinc-100 flex items-center gap-1.5">
                  <span>Question</span>
                  <span className="text-yellow-400 font-mono">
                    {q.question_number}
                  </span>
                </span>
                <span
                  className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border font-mono ${
                    marksMatch
                      ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"
                      : "bg-rose-500/15 text-rose-400 border border-rose-500/30"
                  }`}
                >
                  Concepts Total: {conceptSum} / {q.max_marks} marks
                </span>
              </div>
              {questions.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeQuestion(qIdx)}
                  className="text-zinc-500 hover:text-rose-400 p-1 rounded transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
              <div className="sm:col-span-1">
                <label className="text-zinc-300 block mb-1 font-semibold">
                  Question Number
                </label>
                <input
                  type="text"
                  value={q.question_number}
                  onChange={(e) =>
                    updateQuestion(qIdx, "question_number", e.target.value)
                  }
                  className="w-full bg-[#18191D] border border-zinc-700 rounded-lg p-2 text-zinc-100 font-mono focus:outline-none focus:ring-2 focus:ring-yellow-400/30 focus:border-yellow-400"
                  required
                />
              </div>
              <div className="sm:col-span-1">
                <label className="text-zinc-300 block mb-1 font-semibold">
                  Max Marks
                </label>
                <input
                  type="number"
                  step="0.5"
                  value={q.max_marks}
                  onChange={(e) =>
                    updateQuestion(
                      qIdx,
                      "max_marks",
                      parseFloat(e.target.value) || 0,
                    )
                  }
                  className="w-full bg-[#18191D] border border-zinc-700 rounded-lg p-2 text-zinc-100 font-bold font-mono focus:outline-none focus:ring-2 focus:ring-yellow-400/30 focus:border-yellow-400"
                  required
                />
              </div>
              <div className="sm:col-span-2">
                <label className="text-zinc-300 block mb-1 font-semibold">
                  Question Type
                </label>
                <select
                  value={q.question_type}
                  onChange={(e) =>
                    updateQuestion(qIdx, "question_type", e.target.value)
                  }
                  className="w-full bg-[#18191D] border border-zinc-700 rounded-lg p-2 text-zinc-100 focus:outline-none focus:ring-2 focus:ring-yellow-400/30 focus:border-yellow-400"
                >
                  <option value="DESCRIPTIVE">Descriptive / Analytical</option>
                  <option value="SHORT_ANSWER">Short Answer</option>
                  <option value="ESSAY">Essay</option>
                </select>
              </div>

              <div className="sm:col-span-4">
                <label className="text-zinc-300 block mb-1 font-semibold">
                  Question Prompt
                </label>
                <textarea
                  rows={2}
                  value={q.question_text}
                  onChange={(e) =>
                    updateQuestion(qIdx, "question_text", e.target.value)
                  }
                  placeholder="State the prompt given to students..."
                  className="w-full bg-[#18191D] border border-zinc-700 rounded-lg p-2 text-zinc-100 focus:outline-none focus:ring-2 focus:ring-yellow-400/30 focus:border-yellow-400"
                  required
                />
              </div>
            </div>

            {/* Concepts Sub-list */}
            <div className="pt-2 space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-yellow-400 uppercase tracking-wider">
                  Grading Rubric Concepts ({q.concepts.length})
                </h4>
                <button
                  type="button"
                  onClick={() => addConcept(qIdx)}
                  className="text-yellow-400 hover:text-yellow-300 text-xs font-bold flex items-center gap-1 transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add Concept</span>
                </button>
              </div>

              <div className="space-y-3">
                {q.concepts.map((c, cIdx) => (
                  <div
                    key={cIdx}
                    className="bg-[#18191D] border border-zinc-800 rounded-lg p-3.5 space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-yellow-400 bg-yellow-400/10 border border-yellow-400/30 px-2 py-0.5 rounded">
                          {c.concept_code}
                        </span>
                        <input
                          type="text"
                          value={c.name}
                          onChange={(e) =>
                            updateConcept(qIdx, cIdx, "name", e.target.value)
                          }
                          placeholder="Concept name (e.g. ACID Properties)"
                          className="bg-[#121316] border border-zinc-700 rounded px-2 py-1 text-xs text-zinc-100 font-semibold focus:outline-none focus:ring-1 focus:ring-yellow-400"
                        />
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="flex items-center gap-1 text-xs">
                          <label className="text-zinc-400 text-[10px] font-bold uppercase tracking-wider">
                            Marks:
                          </label>
                          <input
                            type="number"
                            step="0.5"
                            value={c.max_marks}
                            onChange={(e) =>
                              updateConcept(
                                qIdx,
                                cIdx,
                                "max_marks",
                                parseFloat(e.target.value) || 0,
                              )
                            }
                            className="w-16 bg-[#121316] border border-zinc-700 rounded px-2 py-0.5 text-xs text-yellow-400 font-bold font-mono focus:outline-none focus:ring-1 focus:ring-yellow-400"
                          />
                        </div>
                        {q.concepts.length > 1 && (
                          <button
                            type="button"
                            onClick={() => removeConcept(qIdx, cIdx)}
                            className="text-zinc-500 hover:text-rose-400 p-1 rounded transition-colors"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </div>

                    <div>
                      <label className="text-zinc-400 block mb-1 text-[10px] font-bold uppercase tracking-wider">
                        Reference Benchmark Answer:
                      </label>
                      <textarea
                        rows={2}
                        value={c.reference_text}
                        onChange={(e) =>
                          updateConcept(
                            qIdx,
                            cIdx,
                            "reference_text",
                            e.target.value,
                          )
                        }
                        placeholder="Expected benchmark answer for semantic similarity matching..."
                        className="w-full bg-[#121316] border border-zinc-700 rounded p-2 text-xs text-zinc-100 focus:outline-none focus:ring-1 focus:ring-yellow-400"
                        required
                      />
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
                      <div>
                        <label className="text-zinc-400 block text-[10px]">
                          Full Match Threshold (0.1 - 1.0)
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          min="0.1"
                          max="1.0"
                          value={c.full_match_threshold}
                          onChange={(e) =>
                            updateConcept(
                              qIdx,
                              cIdx,
                              "full_match_threshold",
                              parseFloat(e.target.value) || 0.78,
                            )
                          }
                          className="w-full bg-[#121316] border border-zinc-700 rounded p-1.5 text-zinc-100 text-xs font-mono"
                        />
                      </div>
                      <div>
                        <label className="text-zinc-400 block text-[10px]">
                          Partial Match Threshold (0.1 - 1.0)
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          min="0.1"
                          max="1.0"
                          value={c.partial_match_threshold}
                          onChange={(e) =>
                            updateConcept(
                              qIdx,
                              cIdx,
                              "partial_match_threshold",
                              parseFloat(e.target.value) || 0.52,
                            )
                          }
                          className="w-full bg-[#121316] border border-zinc-700 rounded p-1.5 text-zinc-100 text-xs font-mono"
                        />
                      </div>
                      <div>
                        <label className="text-zinc-400 block text-[10px]">
                          Mandatory Keywords (comma-separated)
                        </label>
                        <input
                          type="text"
                          value={c.keywords}
                          onChange={(e) =>
                            updateConcept(
                              qIdx,
                              cIdx,
                              "keywords",
                              e.target.value,
                            )
                          }
                          placeholder="e.g. Atomicity, Isolation"
                          className="w-full bg-[#121316] border border-zinc-700 rounded p-1.5 text-zinc-100 text-xs"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );
      })}

      <button
        type="button"
        onClick={addQuestion}
        className="w-full py-3 border-2 border-dashed border-zinc-700 hover:border-yellow-400 hover:bg-yellow-400/5 rounded-xl text-xs font-bold text-zinc-400 hover:text-yellow-400 transition-all flex items-center justify-center gap-1.5"
      >
        <Plus className="w-4 h-4 text-yellow-400" />
        <span>Add Another Question</span>
      </button>
    </div>
  );
};
