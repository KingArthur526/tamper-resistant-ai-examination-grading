import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Play,
  ShieldCheck,
} from "lucide-react";
import { api } from "../api/client";
import { AuditLog, IntegrityVerificationResult } from "../types";
import { AuditTrailTable } from "../components/AuditTrailTable";

export const AuditIntegrity: React.FC = () => {
  const [searchParams] = useSearchParams();
  const examId = searchParams.get("exam") || "";

  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [verification, setVerification] =
    useState<IntegrityVerificationResult | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [isTampering, setIsTampering] = useState(false);

  useEffect(() => {
    if (examId) loadData(examId);
  }, [examId]);

  const loadData = async (eId: string) => {
    try {
      const [logsData, verRes] = await Promise.all([
        api.getAuditLogs(eId),
        api.verifyIntegrity(eId),
      ]);
      setLogs(logsData);
      setVerification(verRes);
    } catch (e) {
      console.error(e);
    }
  };

  const handleRunVerification = async () => {
    if (!examId) return;
    setIsVerifying(true);
    try {
      const res = await api.verifyIntegrity(examId);
      setVerification(res);
      const logsData = await api.getAuditLogs(examId);
      setLogs(logsData);
    } catch (e: any) {
      alert("Verification error: " + e.message);
    } finally {
      setIsVerifying(false);
    }
  };

  const handleSimulateTamper = async () => {
    if (!verification || !examId) return;
    if (
      confirm(
        "Simulate physical disk file alteration to test integrity scanner?",
      )
    ) {
      setIsTampering(true);
      try {
        const sheets = await api.getExamAnswerSheets(examId);
        if (sheets.length > 0) {
          await api.simulateTamper(sheets[0].id);
          alert(
            "1-byte file alteration written to disk. Running integrity check...",
          );
          await handleRunVerification();
        }
      } catch (e: any) {
        alert("Tamper test error: " + e.message);
      } finally {
        setIsTampering(false);
      }
    }
  };

  const handleRestoreTamper = async () => {
    if (!examId) return;
    setIsTampering(true);
    try {
      const sheets = await api.getExamAnswerSheets(examId);
      if (sheets.length > 0) {
        await api.restoreTamper(sheets[0].id);
        alert("Pristine file restored from backup. Running integrity check...");
        await handleRunVerification();
      }
    } catch (e: any) {
      alert("Restore error: " + e.message);
    } finally {
      setIsTampering(false);
    }
  };

  const isCompromised = verification?.overall_status === "COMPROMISED";
  const isVerified = !isCompromised;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-[#121316] border border-zinc-800 rounded-xl p-5 shadow-lg flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-extrabold text-zinc-100 tracking-tight flex items-center gap-2">
            <span>Audit Log &amp;</span>
            <span className="text-yellow-400">Integrity Verification</span>
          </h1>
          <p className="text-xs text-zinc-400 mt-0.5">
            Validation of stored submission checksums and sequential audit
            history.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          {isCompromised && (
            <button
              onClick={handleRestoreTamper}
              disabled={isTampering || !examId}
              className="px-3.5 py-2 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-colors disabled:opacity-50"
            >
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Restore Clean File</span>
            </button>
          )}

          <button
            onClick={handleSimulateTamper}
            disabled={isTampering || !examId}
            className="px-3.5 py-2 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 text-rose-400" />
            <span>Simulate File Tamper</span>
          </button>

          <button
            onClick={handleRunVerification}
            disabled={isVerifying || !examId}
            className="px-4 py-2 bg-yellow-400 hover:bg-yellow-300 text-zinc-950 rounded-lg text-xs font-bold flex items-center gap-1.5 shadow-md shadow-yellow-500/10 transition-all active:scale-[0.98] disabled:opacity-50"
          >
            <RefreshCw
              className={`w-3.5 h-3.5 ${isVerifying ? "animate-spin" : ""}`}
            />
            <span>Verify Integrity</span>
          </button>
        </div>
      </div>

      {/* Main Integrity Card */}
      <div
        className={`p-6 rounded-xl border shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-6 transition-all ${
          isCompromised
            ? "bg-rose-950/30 border-rose-500/40"
            : "bg-[#121316] border-zinc-800"
        }`}
      >
        <div className="flex items-center gap-4">
          <div
            className={`w-12 h-12 rounded-xl flex items-center justify-center ${
              isCompromised
                ? "bg-rose-500/20 text-rose-400 border border-rose-500/40"
                : "bg-yellow-400/15 text-yellow-400 border border-yellow-400/30"
            }`}
          >
            {isCompromised ? (
              <AlertTriangle className="w-7 h-7" />
            ) : (
              <CheckCircle2 className="w-7 h-7" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-extrabold text-zinc-100">
                {isCompromised
                  ? "Submission Integrity: Compromised"
                  : "Submission Integrity: Verified"}
              </h2>
              <span
                className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full font-mono ${
                  isCompromised
                    ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                    : "bg-yellow-400/15 text-yellow-400 border border-yellow-400/30"
                }`}
              >
                {verification?.overall_status || "VERIFIED"}
              </span>
            </div>
            <p className="text-xs text-zinc-400 mt-0.5">
              {isCompromised
                ? "File alteration detected. A stored submission file does not match its registered checksum."
                : "All submission files match their recorded SHA-256 checksums and the sequential audit chain is unbroken."}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3 text-xs">
          <div className="bg-[#18191D] p-3 rounded-lg border border-zinc-800 text-center">
            <span className="text-[10px] text-zinc-400 block font-bold uppercase tracking-wider">
              Files Checked
            </span>
            <span className="font-extrabold text-zinc-100 text-base font-mono">
              {verification?.total_files_checked ?? 0}
            </span>
          </div>
          <div className="bg-[#18191D] p-3 rounded-lg border border-zinc-800 text-center">
            <span className="text-[10px] text-zinc-400 block font-bold uppercase tracking-wider">
              Audit Events
            </span>
            <span className="font-extrabold text-yellow-400 text-base font-mono">
              {verification?.total_audit_events ?? 0}
            </span>
          </div>
          <div className="bg-[#18191D] p-3 rounded-lg border border-zinc-800 text-center">
            <span className="text-[10px] text-zinc-400 block font-bold uppercase tracking-wider">
              Discrepancies
            </span>
            <span
              className={`font-extrabold text-base font-mono ${verification?.files_tampered ? "text-rose-400" : "text-emerald-400"}`}
            >
              {verification?.files_tampered ?? 0}
            </span>
          </div>
        </div>
      </div>

      <AuditTrailTable
        logs={logs}
        sessionId={examId}
        onRefresh={() => loadData(examId)}
      />
    </div>
  );
};
