import React, { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { OCRViewer } from "../components/OCRViewer";
import { api } from "../api/client";
import { OCRReviewData } from "../types";

export const OCRReview: React.FC = () => {
  const [searchParams] = useSearchParams();
  const sheetId = searchParams.get("sheet") || "";
  const examId = searchParams.get("exam") || "";
  const navigate = useNavigate();

  const [reviewData, setReviewData] = useState<OCRReviewData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (sheetId) {
      loadReview(sheetId);
    } else if (examId) {
      loadFirstSheet(examId);
    }
  }, [sheetId, examId]);

  const loadFirstSheet = async (eId: string) => {
    try {
      const sheets = await api.getExamAnswerSheets(eId);
      if (sheets.length > 0) {
        loadReview(sheets[0].id);
      } else {
        setLoading(false);
      }
    } catch (e) {
      console.error(e);
      setLoading(false);
    }
  };

  const loadReview = async (id: string) => {
    setLoading(true);
    try {
      const data = await api.getOCRReview(id);
      setReviewData(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveCorrections = async (corrections: any[]) => {
    if (!sheetId && !reviewData) return;
    const targetId = sheetId || (reviewData ? reviewData.answer_sheet_id : "");
    await api.submitOCRCorrections(targetId, corrections, true);
    await loadReview(targetId);
  };

  const handleSaveEntireSheet = async (entireText: string) => {
    if (!sheetId && !reviewData) return;
    const targetId = sheetId || (reviewData ? reviewData.answer_sheet_id : "");
    await api.submitEntireRawOCR(targetId, entireText, true);
    await loadReview(targetId);
  };

  const handleApprove = async () => {
    if (!sheetId && !reviewData) return;
    const targetId = sheetId || (reviewData ? reviewData.answer_sheet_id : "");
    await api.approveOCR(targetId);
    navigate(`/results?sheet=${targetId}`);
  };

  const handleRerunOCR = async () => {
    if (!sheetId && !reviewData) return;
    const targetId = sheetId || (reviewData ? reviewData.answer_sheet_id : "");
    await api.processOCR(targetId);
    await loadReview(targetId);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="bg-[#121316] border border-zinc-800 rounded-xl p-5 shadow-lg">
        <h1 className="text-xl font-extrabold text-zinc-100 tracking-tight flex items-center gap-2">
          <span>OCR &amp; Handwriting</span>
          <span className="text-yellow-400">Review</span>
        </h1>
        <p className="text-xs text-zinc-400 mt-0.5">
          Side-by-side inspection of candidate handwritten scripts versus
          transcribed answers.
        </p>
      </div>

      {loading && (
        <div className="py-20 text-center text-zinc-400 text-xs bg-[#121316] border border-zinc-800 rounded-xl">
          Loading scanned answer script and transcription data...
        </div>
      )}

      {!loading && !reviewData && (
        <div className="bg-[#121316] border border-zinc-800 rounded-xl p-12 text-center text-zinc-400 space-y-2 shadow-md">
          <p className="text-sm font-bold text-zinc-100">
            No Submission Selected for Review
          </p>
          <p className="text-xs text-zinc-400">
            Select a candidate submission from the Submissions page or click
            "Load Demo Examination".
          </p>
        </div>
      )}

      {!loading && reviewData && (
        <OCRViewer
          reviewData={reviewData}
          onSaveCorrections={handleSaveCorrections}
          onSaveEntireSheet={handleSaveEntireSheet}
          onApprove={handleApprove}
          onRerunOCR={handleRerunOCR}
        />
      )}
    </div>
  );
};
