import React, { useState, useEffect } from "react";
import {
  FileText,
  Image as ImageIcon,
  CheckCircle,
  Save,
  Layers,
  RefreshCw,
  Check,
} from "lucide-react";
import { OCRReviewData, AnswerSheetPage } from "../types";

interface OCRViewerProps {
  reviewData: OCRReviewData;
  onSaveCorrections: (
    corrections: Array<{ student_answer_id: string; edited_text: string }>,
  ) => Promise<void>;
  onSaveEntireSheet?: (entireText: string) => Promise<void>;
  onApprove: () => Promise<void>;
  onRerunOCR?: () => Promise<void>;
}

export const OCRViewer: React.FC<OCRViewerProps> = ({
  reviewData,
  onSaveCorrections,
  onSaveEntireSheet,
  onApprove,
  onRerunOCR,
}) => {
  const pages: AnswerSheetPage[] =
    reviewData.pages && reviewData.pages.length > 0
      ? reviewData.pages
      : [
          {
            page_number: 1,
            sheet_id: reviewData.answer_sheet_id,
            image_url: reviewData.original_image_url,
            preprocessed_image_url: reviewData.preprocessed_image_url,
            filename: reviewData.original_filename,
            sha256_hash: reviewData.sha256_hash,
          },
        ];

  const [selectedPageIndex, setSelectedPageIndex] = useState(0);
  const activePage = pages[selectedPageIndex] || pages[0];

  const [editorMode, setEditorMode] = useState<"questions" | "entire_sheet">(
    "questions",
  );

  const [editedAnswers, setEditedAnswers] = useState<{ [id: string]: string }>(
    () => {
      const initial: { [id: string]: string } = {};
      reviewData.answers.forEach((a) => {
        initial[a.id] =
          a.teacher_edited_text || a.cleaned_text || a.raw_ocr_text;
      });
      return initial;
    },
  );

  const [entireText, setEntireText] = useState<string>(() => {
    if (reviewData.raw_entire_sheet_text)
      return reviewData.raw_entire_sheet_text;
    return reviewData.answers
      .map(
        (a) =>
          `Question ${a.question_number}:\n${a.teacher_edited_text || a.cleaned_text || a.raw_ocr_text}`,
      )
      .join("\n\n");
  });

  useEffect(() => {
    const initial: { [id: string]: string } = {};
    reviewData.answers.forEach((a) => {
      initial[a.id] = a.teacher_edited_text || a.cleaned_text || a.raw_ocr_text;
    });
    setEditedAnswers(initial);
    if (reviewData.raw_entire_sheet_text) {
      setEntireText(reviewData.raw_entire_sheet_text);
    } else {
      setEntireText(
        reviewData.answers
          .map(
            (a) =>
              `Question ${a.question_number}:\n${a.teacher_edited_text || a.cleaned_text || a.raw_ocr_text}`,
          )
          .join("\n\n"),
      );
    }
  }, [reviewData]);

  const [isSaving, setIsSaving] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [isRerunning, setIsRerunning] = useState(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);

  const handleTextChange = (id: string, text: string) => {
    setEditedAnswers((prev) => ({ ...prev, [id]: text }));
  };

  const handleSaveAndReEvaluate = async () => {
    setIsSaving(true);
    setSaveSuccessMsg(null);
    try {
      if (editorMode === "entire_sheet" && onSaveEntireSheet) {
        await onSaveEntireSheet(entireText);
        setSaveSuccessMsg("Transcription updated and answer marks recomputed.");
      } else {
        const payload = Object.entries(editedAnswers).map(
          ([student_answer_id, edited_text]) => ({
            student_answer_id,
            edited_text,
          }),
        );
        await onSaveCorrections(payload);
        setSaveSuccessMsg("Corrections saved and marks recomputed.");
      }
      setTimeout(() => setSaveSuccessMsg(null), 4000);
    } catch (e: any) {
      alert("Error saving corrections: " + e.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleApproveClick = async () => {
    setIsApproving(true);
    try {
      // 1. First save any edited answers if present
      if (editorMode === "entire_sheet" && onSaveEntireSheet) {
        await onSaveEntireSheet(entireText);
      } else {
        const payload = Object.entries(editedAnswers).map(
          ([student_answer_id, edited_text]) => ({
            student_answer_id,
            edited_text,
          }),
        );
        if (payload.length > 0) {
          await onSaveCorrections(payload);
        }
      }

      // 2. Mark approved
      await onApprove();
      setSaveSuccessMsg(
        "Transcription approved. Answer sheet verified and graded.",
      );
      setTimeout(() => setSaveSuccessMsg(null), 4000);
    } catch (e: any) {
      alert("Error approving transcription: " + e.message);
    } finally {
      setIsApproving(false);
    }
  };

  const handleRerunOCRClick = async () => {
    if (!onRerunOCR) return;
    setIsRerunning(true);
    try {
      await onRerunOCR();
      setSaveSuccessMsg("Deep learning OCR executed successfully.");
      setTimeout(() => setSaveSuccessMsg(null), 4000);
    } catch (e: any) {
      alert("Error re-running OCR: " + e.message);
    } finally {
      setIsRerunning(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-full max-w-7xl mx-auto">
      {/* Left: Scanned Document Canvas */}
      <div className="bg-[#121316] border border-zinc-800 rounded-xl p-4 flex flex-col h-[800px] shadow-lg">
        {/* Top Header */}
        <div className="flex items-center justify-between pb-3 border-b border-zinc-800 mb-3">
          <div className="flex items-center gap-2">
            <ImageIcon className="w-4 h-4 text-yellow-400" />
            <span className="text-xs font-bold text-yellow-400 uppercase tracking-wider">
              Scanned Answer Script ({pages.length}{" "}
              {pages.length === 1 ? "Page" : "Pages"})
            </span>
          </div>
          <span className="font-mono text-[10px] text-zinc-400 bg-zinc-900 border border-zinc-700 px-2 py-0.5 rounded">
            Checksum: {activePage.sha256_hash.slice(0, 16)}...
          </span>
        </div>

        {/* Multi-Page Tabs */}
        {pages.length > 1 && (
          <div className="flex items-center gap-2 mb-3 overflow-x-auto pb-1">
            <span className="text-[10px] text-zinc-400 font-bold uppercase mr-1">
              Pages:
            </span>
            {pages.map((p, idx) => (
              <button
                key={p.sheet_id || idx}
                onClick={() => setSelectedPageIndex(idx)}
                className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                  selectedPageIndex === idx
                    ? "bg-yellow-400/10 text-yellow-400 font-bold border border-yellow-400/40"
                    : "bg-zinc-900 text-zinc-400 hover:bg-zinc-800 border border-zinc-800"
                }`}
              >
                Page {p.page_number || idx + 1}
              </button>
            ))}
          </div>
        )}

        {/* Document Canvas */}
        <div className="flex-1 bg-[#090A0B] rounded-lg border border-zinc-800/80 overflow-hidden flex items-center justify-center p-3 relative">
          {activePage.filename.toLowerCase().endsWith(".pdf") ? (
            <iframe
              src={activePage.image_url}
              title={`Answer Sheet Page ${selectedPageIndex + 1}`}
              className="w-full h-full rounded border-0 bg-white"
            />
          ) : (
            <img
              src={activePage.image_url}
              alt={`Candidate Answer Sheet Page ${selectedPageIndex + 1}`}
              className="max-h-full max-w-full object-contain rounded shadow-lg"
              onError={(e) => {
                if (activePage.preprocessed_image_url) {
                  (e.target as HTMLImageElement).src =
                    activePage.preprocessed_image_url;
                }
              }}
            />
          )}

          <div className="absolute bottom-3 left-3 bg-zinc-900/90 backdrop-blur-xs border border-zinc-700 px-2.5 py-1 rounded text-[11px] text-zinc-300 font-mono shadow-md">
            {activePage.filename} &bull; Page {selectedPageIndex + 1} of{" "}
            {pages.length}
          </div>
        </div>
      </div>

      {/* Right: Transcription Editor */}
      <div className="bg-[#121316] border border-zinc-800 rounded-xl p-4 flex flex-col h-[800px] shadow-lg">
        {/* Editor Controls Header */}
        <div className="flex items-center justify-between pb-3 border-b border-zinc-800 mb-3">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-yellow-400" />
            <div className="flex bg-[#18191D] p-0.5 rounded-lg border border-zinc-700">
              <button
                onClick={() => setEditorMode("questions")}
                className={`px-3 py-1 rounded-md text-xs font-semibold transition-all ${
                  editorMode === "questions"
                    ? "bg-yellow-400 text-zinc-950 font-bold shadow-xs"
                    : "text-zinc-400 hover:text-zinc-100"
                }`}
              >
                By Question ({reviewData.answers.length})
              </button>
              <button
                onClick={() => setEditorMode("entire_sheet")}
                className={`px-3 py-1 rounded-md text-xs font-semibold transition-all ${
                  editorMode === "entire_sheet"
                    ? "bg-yellow-400 text-zinc-950 font-bold shadow-xs"
                    : "text-zinc-400 hover:text-zinc-100"
                }`}
              >
                Full Transcript
              </button>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {onRerunOCR && (
              <button
                onClick={handleRerunOCRClick}
                disabled={isRerunning}
                title="Re-run deep-learning EasyOCR & PyMuPDF on the uploaded scan"
                className="px-2.5 py-1 bg-zinc-800 hover:bg-zinc-700 text-yellow-400 border border-zinc-700 hover:border-yellow-400/40 text-xs font-semibold rounded-md transition-all flex items-center gap-1.5 shadow-xs disabled:opacity-50"
              >
                <RefreshCw className={`w-3 h-3 text-yellow-400 ${isRerunning ? "animate-spin" : ""}`} />
                <span>{isRerunning ? "Recognizing..." : "Re-run AI OCR"}</span>
              </button>
            )}
            <span className="text-[11px] text-yellow-400 bg-yellow-400/10 border border-yellow-400/30 px-2.5 py-1 rounded-md font-bold font-mono">
              OCR Quality: {(reviewData.ocr_confidence_avg * 100).toFixed(1)}%
            </span>
          </div>
        </div>

        {/* Success Alert */}
        {saveSuccessMsg && (
          <div className="mb-3 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg flex items-center gap-2 text-xs text-emerald-400 animate-fadeIn">
            <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{saveSuccessMsg}</span>
          </div>
        )}

        {/* Main Editor Body */}
        {editorMode === "questions" ? (
          <div className="flex-1 overflow-y-auto space-y-3.5 pr-1">
            {reviewData.answers.map((ans) => (
              <div
                key={ans.id}
                className="bg-[#18191D] border border-zinc-800 hover:border-zinc-700 rounded-lg p-3.5 space-y-2 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-yellow-400 font-mono">
                    Question {ans.question_number} ({ans.max_marks} marks)
                  </span>
                  <span className="text-[10px] font-mono text-zinc-400 bg-zinc-900 border border-zinc-700 px-1.5 py-0.5 rounded">
                    {(editedAnswers[ans.id] || "").length} characters
                  </span>
                </div>
                <p className="text-xs text-zinc-400 font-medium italic">
                  "{ans.question_text}"
                </p>
                <textarea
                  rows={4}
                  value={editedAnswers[ans.id] || ""}
                  onChange={(e) => handleTextChange(ans.id, e.target.value)}
                  className="w-full bg-[#121316] border border-zinc-700 rounded-lg p-2.5 text-xs text-zinc-100 leading-relaxed focus:outline-none focus:ring-2 focus:ring-yellow-400/30 focus:border-yellow-400 transition-all font-sans"
                  placeholder="Transcribed text for this question. Edit any recognition errors..."
                />
              </div>
            ))}
          </div>
        ) : (
          <div className="flex-1 flex flex-col space-y-2">
            <div className="flex items-center justify-between text-xs text-zinc-400">
              <span>
                Full transcript (questions delimited by 'Question 1:', 'Question
                2:'):
              </span>
              <span className="font-mono text-[10px] text-zinc-400">
                {entireText.length} characters
              </span>
            </div>
            <textarea
              value={entireText}
              onChange={(e) => setEntireText(e.target.value)}
              className="flex-1 w-full bg-[#18191D] border border-zinc-700 rounded-lg p-3 text-xs text-zinc-100 leading-relaxed resize-none focus:outline-none focus:ring-2 focus:ring-yellow-400/30 focus:border-yellow-400 font-sans"
              placeholder="Paste or edit the full candidate answer transcript..."
            />
          </div>
        )}

        {/* Action Buttons */}
        <div className="pt-3 border-t border-zinc-800 flex items-center justify-between gap-3 mt-2">
          <span className="text-[11px] text-zinc-400">
            Saving updates semantic evaluation and spelling scores.
          </span>

          <div className="flex items-center gap-2">
            <button
              onClick={handleSaveAndReEvaluate}
              disabled={isSaving}
              className="px-3.5 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700 text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5 shadow-xs disabled:opacity-50"
            >
              {isSaving ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin text-zinc-400" />
              ) : (
                <Save className="w-3.5 h-3.5 text-zinc-400" />
              )}
              <span>{isSaving ? "Saving..." : "Save Corrections"}</span>
            </button>

            <button
              onClick={handleApproveClick}
              disabled={isApproving}
              className="px-4 py-2 bg-yellow-400 hover:bg-yellow-300 text-zinc-950 text-xs font-bold rounded-lg transition-all flex items-center gap-1.5 shadow-md shadow-yellow-500/10 active:scale-[0.98] disabled:opacity-50"
            >
              <Check className="w-3.5 h-3.5 text-zinc-950" />
              <span>
                {isApproving ? "Approving..." : "Approve Transcription"}
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
