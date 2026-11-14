import React, { useState } from "react";
import { Download, FileSpreadsheet, ShieldCheck, CheckCircle2 } from "lucide-react";
import { apiClient } from "../../api/client";
import { Button } from "../../components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../../components/ui/Card";

export function Reports() {
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadSuccess, setDownloadSuccess] = useState<string | null>(null);

  const handleDownloadCsv = async (reportType: "trends" | "opportunities") => {
    setIsDownloading(true);
    setDownloadSuccess(null);
    try {
      const response = await apiClient.getRaw("/reports/export.csv", {
        type: reportType,
      });

      if (!response.ok) {
        throw new Error(`Failed to export report: ${response.statusText}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `ecosystem_${reportType}_export_${new Date().toISOString().split("T")[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setDownloadSuccess(`Exported ${reportType} report successfully`);
      setTimeout(() => setDownloadSuccess(null), 4000);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Error generating export");
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Reports & Compliance Exports</h1>
        <p className="text-sm text-slate-500">
          Stream structured data exports and audited reports with mandatory DPDP non-PII headers
        </p>
      </div>

      {downloadSuccess && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 font-semibold flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-600" /> {downloadSuccess}
        </div>
      )}

      {/* DPDP Export Banner */}
      <div className="p-4 rounded-lg border border-slate-200 bg-white shadow-sm flex items-start gap-3">
        <ShieldCheck className="h-5 w-5 text-indigo-600 shrink-0 mt-0.5" />
        <div className="text-xs text-slate-600">
          <span className="font-bold text-slate-800 block mb-0.5">
            Audit-Ready Compliance Header
          </span>
          All exported CSV documents include a standard metadata preamble recording export date, workspace isolation ID, and data license constraints per ASCI and DPDP guidelines.
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Export 1: Trend Signals */}
        <Card className="border-slate-200 shadow-sm p-6 flex flex-col justify-between">
          <div>
            <div className="h-10 w-10 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center mb-3">
              <FileSpreadsheet className="h-5 w-5" />
            </div>
            <CardTitle className="text-base font-bold text-slate-900">
              Trend Momentum & Signals CSV
            </CardTitle>
            <CardDescription className="text-xs text-slate-500 mt-1 leading-relaxed">
              Complete catalog of ranked consumer topics, momentum scores, growth rates, multi-source corroboration counts, and confidence badges.
            </CardDescription>
          </div>
          <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
            <span className="text-[11px] font-mono text-slate-400">Format: UTF-8 CSV</span>
            <Button
              size="sm"
              onClick={() => handleDownloadCsv("trends")}
              isLoading={isDownloading}
              className="gap-1.5"
            >
              <Download className="h-4 w-4" /> Export Trends
            </Button>
          </div>
        </Card>

        {/* Export 2: Opportunities & Briefs */}
        <Card className="border-slate-200 shadow-sm p-6 flex flex-col justify-between">
          <div>
            <div className="h-10 w-10 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center mb-3">
              <FileSpreadsheet className="h-5 w-5" />
            </div>
            <CardTitle className="text-base font-bold text-slate-900">
              Opportunity Briefs & Evidence CSV
            </CardTitle>
            <CardDescription className="text-xs text-slate-500 mt-1 leading-relaxed">
              All saved opportunities, approval statuses, analyst collaboration notes, and linked ground-truth evidence citations.
            </CardDescription>
          </div>
          <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
            <span className="text-[11px] font-mono text-slate-400">Format: UTF-8 CSV</span>
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleDownloadCsv("opportunities")}
              isLoading={isDownloading}
              className="gap-1.5"
            >
              <Download className="h-4 w-4" /> Export Opportunities
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}
