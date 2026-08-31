import React from "react";
import { CheckCircle2, Link2 } from "lucide-react";
import { AuditLog } from "../types";

interface AuditTrailTableProps {
  logs: AuditLog[];
  sessionId: string;
  onRefresh: () => void;
}

export const AuditTrailTable: React.FC<AuditTrailTableProps> = ({ logs }) => {
  return (
    <div className="bg-[#121316] border border-zinc-800 rounded-xl overflow-hidden shadow-lg">
      <div className="p-4 border-b border-zinc-800 flex items-center justify-between">
        <div>
          <h2 className="text-xs font-bold text-yellow-400 uppercase tracking-wider flex items-center gap-1.5">
            <Link2 className="w-4 h-4 text-yellow-400" />
            Audit History &amp; Sequential Log ({logs.length} Records)
          </h2>
          <p className="text-xs text-zinc-400 mt-0.5">
            Cryptographically chained action log recording grading events, mark
            overrides, and approvals.
          </p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-zinc-300">
          <thead className="bg-zinc-900/90 text-zinc-400 uppercase text-[10px] font-bold tracking-wider border-b border-zinc-800">
            <tr>
              <th className="py-3 px-4">Timestamp</th>
              <th className="py-3 px-4">Action</th>
              <th className="py-3 px-4">Entity</th>
              <th className="py-3 px-4">User</th>
              <th className="py-3 px-4 font-mono">Previous Hash</th>
              <th className="py-3 px-4 font-mono">Event Hash</th>
              <th className="py-3 px-4">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/70 font-sans">
            {logs.length === 0 && (
              <tr>
                <td
                  colSpan={7}
                  className="py-8 text-center text-zinc-500 text-xs"
                >
                  No audit events recorded yet.
                </td>
              </tr>
            )}
            {logs.map((log) => (
              <tr
                key={log.id}
                className="hover:bg-zinc-800/40 transition-colors"
              >
                <td className="py-3 px-4 text-zinc-400 whitespace-nowrap text-[11px] font-mono">
                  {new Date(log.timestamp).toLocaleString()}
                </td>
                <td className="py-3 px-4 font-semibold text-zinc-100">
                  <span className="bg-zinc-900 border border-zinc-700 text-yellow-400 px-2 py-0.5 rounded text-[11px] font-mono">
                    {log.action}
                  </span>
                </td>
                <td className="py-3 px-4 text-zinc-300 font-medium">
                  {log.entity_type}
                </td>
                <td className="py-3 px-4 text-zinc-400">
                  {log.user_name || "System"}
                </td>
                <td className="py-3 px-4 font-mono text-[10px] text-zinc-500">
                  {log.previous_hash.slice(0, 10)}...
                  {log.previous_hash.slice(-6)}
                </td>
                <td className="py-3 px-4 font-mono text-[10px] text-zinc-300 font-semibold">
                  {log.event_hash.slice(0, 10)}...{log.event_hash.slice(-6)}
                </td>
                <td className="py-3 px-4">
                  <span className="inline-flex items-center gap-1 text-[11px] text-yellow-400 bg-yellow-400/10 border border-yellow-400/30 px-2 py-0.5 rounded font-bold font-mono">
                    <CheckCircle2 className="w-3.5 h-3.5 text-yellow-400" />
                    Verified
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
