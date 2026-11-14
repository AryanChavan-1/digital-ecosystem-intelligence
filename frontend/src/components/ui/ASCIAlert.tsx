import React from "react";
import { ShieldAlert, Info } from "lucide-react";

export function ASCIAlert() {
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 mb-6">
      <div className="flex items-start gap-3">
        <ShieldAlert className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
        <div className="text-sm">
          <p className="font-semibold text-amber-900">
            ASCI Compliance & Paid Partnership Disclosure Mandatory
          </p>
          <p className="mt-1 text-amber-800">
            Per the Advertising Standards Council of India (ASCI) Guidelines for Influencer Advertising, any creator collaborations or promotional campaigns derived from this brief must prominently display disclosures such as <code className="bg-amber-100 px-1 py-0.5 rounded font-mono font-semibold">#Ad</code>, <code className="bg-amber-100 px-1 py-0.5 rounded font-mono font-semibold">#Sponsored</code>, <code className="bg-amber-100 px-1 py-0.5 rounded font-mono font-semibold">#PaidCollaboration</code>, or <code className="bg-amber-100 px-1 py-0.5 rounded font-mono font-semibold">#Partnership</code> within the first two lines or visible video frame.
          </p>
        </div>
      </div>
    </div>
  );
}

export function AISynthesizedBanner() {
  return (
    <div className="rounded-lg border border-indigo-200 bg-indigo-50/80 p-3.5 mb-6 flex items-center justify-between">
      <div className="flex items-center gap-2.5 text-xs text-indigo-900">
        <Info className="h-4 w-4 text-indigo-600 shrink-0" />
        <span>
          <strong className="font-semibold">AI-Synthesized Draft</strong> — Verify against linked evidence before commercial execution. All claims are grounded in connected workspace source records.
        </span>
      </div>
      <span className="text-[11px] font-medium bg-indigo-200 text-indigo-800 px-2 py-0.5 rounded-full shrink-0">
        DPDP-Compliant / Non-PII
      </span>
    </div>
  );
}
