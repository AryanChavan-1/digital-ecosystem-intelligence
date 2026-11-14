import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { BarChart3, Upload, Layers, ArrowUpRight, ShieldCheck, DollarSign } from "lucide-react";
import { apiClient } from "../../api/client";
import { Campaign, CampaignSummary } from "../../types";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../../components/ui/Card";
import { CampaignUploadModal } from "../../components/campaigns/CampaignUploadModal";
import { TableSkeleton } from "../../components/ui/Skeleton";
import { ErrorState } from "../../components/ui/ErrorState";
import { EmptyState } from "../../components/ui/EmptyState";
import { formatCurrency, formatNumber, formatPercent } from "../../lib/utils";

export function CampaignAnalytics() {
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [selectedCampaignId, setSelectedCampaignId] = useState<string | null>(null);

  const {
    data: campaigns,
    isLoading: isLoadingCampaigns,
    isError: isCampaignsError,
    error: campaignsError,
    refetch: refetchCampaigns,
  } = useQuery<Campaign[]>({
    queryKey: ["campaigns"],
    queryFn: () => apiClient.get<Campaign[]>("/campaigns"),
  });

  const activeId = selectedCampaignId || (campaigns && campaigns.length > 0 ? campaigns[0].id : null);

  const {
    data: summary,
    isLoading: isLoadingSummary,
    isError: isSummaryError,
  } = useQuery<CampaignSummary>({
    queryKey: ["campaign-summary", activeId],
    queryFn: () => apiClient.get<CampaignSummary>(`/campaigns/${activeId}/summary`),
    enabled: !!activeId,
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Campaign Analytics & Ingestion</h1>
          <p className="text-sm text-slate-500">
            Audit Meta Ads, Google Ads, and Shopify performance with Indian currency and zero-denominator safety
          </p>
        </div>

        <Button onClick={() => setIsUploadModalOpen(true)} className="gap-2 shadow-sm">
          <Upload className="h-4 w-4" /> Upload Ad Performance CSV
        </Button>
      </div>

      {isLoadingCampaigns && <TableSkeleton rows={4} cols={4} />}

      {isCampaignsError && (
        <ErrorState
          title="Failed to load campaigns"
          message={campaignsError instanceof Error ? campaignsError.message : "Error querying campaigns"}
          onRetry={() => refetchCampaigns()}
        />
      )}

      {!isLoadingCampaigns && !isCampaignsError && (!campaigns || campaigns.length === 0) && (
        <EmptyState
          title="No campaigns uploaded yet"
          description="Upload an ad performance CSV export from Meta, Google, or Shopify to calculate audited CTR, CPC, CPA, and ROAS."
          actionText="Upload Campaign CSV"
          onAction={() => setIsUploadModalOpen(true)}
        />
      )}

      {!isLoadingCampaigns && !isCampaignsError && campaigns && campaigns.length > 0 && (
        <div className="space-y-6">
          {/* Campaign Selector Pills */}
          <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-slate-200">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider whitespace-nowrap">
              Campaigns:
            </span>
            {campaigns.map((camp) => (
              <button
                key={camp.id}
                onClick={() => setSelectedCampaignId(camp.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition ${
                  activeId === camp.id
                    ? "bg-indigo-600 text-white shadow-xs"
                    : "bg-white border border-slate-200 text-slate-700 hover:bg-slate-50"
                }`}
              >
                {camp.name} ({camp.channel})
              </button>
            ))}
          </div>

          {/* Active Campaign KPI Grid (Guarded: "—" when null) */}
          {summary && (
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-600">
                  Performance Metrics ({summary.currency})
                </h3>
                <span className="text-[11px] text-slate-400 flex items-center gap-1 font-mono">
                  <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
                  Exact Decimal Calculations • Null Safe
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                {/* CTR = (clicks / impressions) * 100 */}
                <Card className="p-4 border-slate-200">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    CTR (Click-Through)
                  </span>
                  <div className="text-xl font-black text-slate-900 mt-1">
                    {summary.ctr !== null && summary.ctr !== undefined
                      ? formatPercent(summary.ctr)
                      : "—"}
                  </div>
                  <span className="text-[10px] text-slate-400 mt-0.5 block">clicks / impr</span>
                </Card>

                {/* CPC = spend / clicks */}
                <Card className="p-4 border-slate-200">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    CPC (Cost Per Click)
                  </span>
                  <div className="text-xl font-black text-slate-900 mt-1">
                    {summary.cpc !== null && summary.cpc !== undefined
                      ? formatCurrency(summary.cpc, summary.currency)
                      : "—"}
                  </div>
                  <span className="text-[10px] text-slate-400 mt-0.5 block">spend / clicks</span>
                </Card>

                {/* CPM = (spend / impressions) * 1000 */}
                <Card className="p-4 border-slate-200">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    CPM (Mille Cost)
                  </span>
                  <div className="text-xl font-black text-slate-900 mt-1">
                    {summary.cpm !== null && summary.cpm !== undefined
                      ? formatCurrency(summary.cpm, summary.currency)
                      : "—"}
                  </div>
                  <span className="text-[10px] text-slate-400 mt-0.5 block">per 1,000 impr</span>
                </Card>

                {/* CPA = spend / conversions */}
                <Card className="p-4 border-slate-200">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    CPA (Cost Per Acq)
                  </span>
                  <div className="text-xl font-black text-slate-900 mt-1">
                    {summary.cpa !== null && summary.cpa !== undefined
                      ? formatCurrency(summary.cpa, summary.currency)
                      : "—"}
                  </div>
                  <span className="text-[10px] text-slate-400 mt-0.5 block">spend / orders</span>
                </Card>

                {/* ROAS = attributed_revenue / spend */}
                <Card className="p-4 border-slate-200 bg-indigo-50/30 border-indigo-200">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-700">
                    ROAS (Return on Ad Spend)
                  </span>
                  <div className="text-xl font-black text-indigo-600 mt-1">
                    {summary.roas !== null && summary.roas !== undefined
                      ? `${typeof summary.roas === "number" ? summary.roas.toFixed(2) : summary.roas}x`
                      : "—"}
                  </div>
                  <span className="text-[10px] text-indigo-500 mt-0.5 block">revenue / spend</span>
                </Card>
              </div>

              {/* Volume Summary Strip */}
              <div className="mt-4 p-4 bg-white border border-slate-200 rounded-lg grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
                <div>
                  <span className="text-slate-400 uppercase text-[10px] block">Total Spend</span>
                  <span className="font-bold text-slate-800 text-sm">
                    {formatCurrency(summary.total_spend, summary.currency)}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 uppercase text-[10px] block">Attributed Revenue</span>
                  <span className="font-bold text-slate-800 text-sm">
                    {formatCurrency(summary.total_attributed_revenue, summary.currency)}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 uppercase text-[10px] block">Total Impressions</span>
                  <span className="font-bold text-slate-800 text-sm">
                    {formatNumber(summary.total_impressions)}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 uppercase text-[10px] block">Total Conversions</span>
                  <span className="font-bold text-slate-800 text-sm">
                    {formatNumber(summary.total_conversions)}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Campaigns Overview Table */}
          <Card className="border-slate-200 shadow-sm">
            <CardHeader className="p-5 pb-3">
              <CardTitle className="text-sm font-bold text-slate-900">
                Uploaded Campaign Registry
              </CardTitle>
              <CardDescription className="text-xs text-slate-500">
                All campaign feeds configured for this workspace
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-y border-slate-200 bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold">
                      <th className="px-5 py-3">Campaign Name</th>
                      <th className="px-4 py-3">Channel</th>
                      <th className="px-4 py-3">External ID</th>
                      <th className="px-4 py-3">Currency</th>
                      <th className="px-4 py-3">Ingested At</th>
                      <th className="px-5 py-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-mono">
                    {campaigns.map((camp) => (
                      <tr key={camp.id} className="hover:bg-slate-50 transition">
                        <td className="px-5 py-3.5 font-sans font-bold text-slate-900">
                          {camp.name}
                        </td>
                        <td className="px-4 py-3.5 font-sans">
                          <Badge variant="secondary">{camp.channel}</Badge>
                        </td>
                        <td className="px-4 py-3.5 text-slate-500">{camp.external_campaign_id}</td>
                        <td className="px-4 py-3.5 text-slate-700">{camp.currency}</td>
                        <td className="px-4 py-3.5 text-slate-500 font-sans text-xs">
                          {new Date(camp.created_at).toLocaleDateString("en-IN")}
                        </td>
                        <td className="px-5 py-3.5 text-right font-sans">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setSelectedCampaignId(camp.id)}
                            className="text-indigo-600 hover:text-indigo-700 text-xs"
                          >
                            Inspect KPIs
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Upload Wizard Modal */}
      <CampaignUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onSuccess={() => {
          refetchCampaigns();
        }}
      />
    </div>
  );
}
