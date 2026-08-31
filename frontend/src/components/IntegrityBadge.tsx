import React from 'react';
import { ShieldCheck, AlertOctagon, Clock } from 'lucide-react';

interface IntegrityBadgeProps {
  status: 'VERIFIED' | 'COMPROMISED' | 'PENDING' | string;
}

export const IntegrityBadge: React.FC<IntegrityBadgeProps> = ({ status }) => {
  if (status === 'VERIFIED') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
        <ShieldCheck className="w-3.5 h-3.5" />
        <span>SHA-256 VERIFIED</span>
      </span>
    );
  }
  if (status === 'COMPROMISED') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30 animate-pulse">
        <AlertOctagon className="w-3.5 h-3.5" />
        <span>INTEGRITY COMPROMISED</span>
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
      <Clock className="w-3.5 h-3.5" />
      <span>PENDING SCAN</span>
    </span>
  );
};
