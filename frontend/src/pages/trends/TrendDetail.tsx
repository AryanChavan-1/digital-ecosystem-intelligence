import React, { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
  ArrowLeft,
  Sparkles,
  Layers,
  Database,
  Users,
  ExternalLink,
  ShieldCheck,
} from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import { apiClient } from "../../api/client";
import { TrendDetail as TrendDetailType, Opportunity } from "../../types";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../../components/ui/Card";
import { ErrorState } from "../../components/ui/ErrorState";
import { formatNumber, formatPercent } from "../../lib/utils";

export function TrendDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [createError, setCreateError] = useState<string | null>(null);

  const {
    data: detail,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<TrendDetailType>({
    queryKey: ["trend-detail", id],
    queryFn: () => apiClient.get<TrendDetailType>(`/trends/${id}`),
    enabled: !!id,
  });

  const createOpportunityMutation = useMutation({
    mutationFn: async () => {
      if (!detail) throw new Error("Trend detail not loaded");
      return apiClient.post<Opportunity>("/opportunities", {
        topic_id: detail.topic_id,
        title: `Opportunity: ${detail.topic_name}`,
      });
    },
    onSuccess: (opp) => {
      navigate(`/app/opportunities/${opp.id}`);
    },
    onError: (err: Error) => {
      setCreateError(err.message || "Failed to create opportunity");
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 w-48 bg-slate-200 rounded" />
        <div className="h-40 bg-slate-200 rounded-lg" />
        <div className="h-64 bg-slate-200 rounded-lg" />
      </div>
    );
  }

  if (isError || !detail) {
    return (
      <ErrorState
        title="Could not find trend"
        message={error instanceof Error ? error.message : "Trend record not found or inaccessible"}
        onRetry={() => refetch()}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Back button and Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <button
            onClick={() => navigate("/app/trends")}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 mb-2 transition"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Back to Trends
          </button>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-slate-900">{detail.topic_name}</h1>
            {detail.is_cold_start ? (
              <Badge variant="coldStart">Low / Single-Source Snapshot</Badge>
            ) : (
              <Badge
                variant={
                  detail.confidence === "high"
                    ? "success"
                    : detail.confidence === "medium"
                    ? "default"
                    : "warning"
                }
              >
                {detail.confidence.toUpperCase()} CONFIDENCE
              </Badge>
            )}
            <Badge variant="outline">{detail.category || "General D2C"}</Badge>
          </div>
        </div>

        <div>
          <Button
            onClick={() => createOpportunityMutation.mutate()}
            isLoading={createOpportunityMutation.isPending}
            className="gap-2 shadow-sm"
          >
            <Sparkles className="h-4 w-4" /> Create Opportunity Brief
          </Button>
          {createError && <p className="text-xs text-rose-600 mt-1">{createError}</p>}
        </div>
      </div>

      {/* Plain Language Summary & Key Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 border-slate-200 shadow-sm p-6">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-2">
            Signal Summary & Consumer Context
          </h2>
          <p className="text-slate-700 text-sm leading-relaxed">{detail.summary}</p>

          <div className="mt-6 pt-6 border-t border-slate-100 grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div>
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Momentum</span>
              <p className="text-xl font-extrabold text-indigo-600">
                {detail.momentum_score.toFixed(1)}/100
              </p>
            </div>
            <div>
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Mentions</span>
              <p className="text-xl font-extrabold text-slate-900">
                {formatNumber(detail.mention_count)}
              </p>
            </div>
            <div>
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Growth vs Prev</span>
              <p
                className={`text-xl font-extrabold ${
                  (detail.change_pct ?? 0) >= 0 ? "text-emerald-600" : "text-rose-600"
                }`}
              >
                {detail.change_pct !== null && detail.change_pct !== undefined
                  ? `${detail.change_pct >= 0 ? "+" : ""}${formatPercent(detail.change_pct)}`
                  : "—"}
              </p>
            </div>
            <div>
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Source Count</span>
              <p className="text-xl font-extrabold text-slate-900">{detail.source_count}</p>
            </div>
          </div>
        </Card>

        {/* Source Coverage Breakdown */}
        <Card className="border-slate-200 shadow-sm p-6 flex flex-col justify-between">
          <div>
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-1.5">
              <Database className="h-4 w-4 text-indigo-500" /> Source Distribution
            </h2>
            <div className="space-y-3">
              {Object.entries(detail.source_breakdown || {}).map(([src, count]) => (
                <div key={src} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-semibold text-slate-700 capitalize">{src}</span>
                    <span className="text-slate-500 font-mono">{count} records</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                    <div
                      className="bg-indigo-600 h-1.5 rounded-full"
                      style={{
                        width: `${Math.min(
                          100,
                          (count / Math.max(1, detail.mention_count)) * 100
                        )}%`,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center gap-1.5 text-[11px] text-slate-400">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
            <span>Permitted social signals & public catalog mentions only</span>
          </div>
        </Card>
      </div>

      {/* Recharts Velocity Timeline */}
      <Card className="border-slate-200 shadow-sm p-6">
        <CardHeader className="p-0 pb-4">
          <CardTitle className="text-base font-bold text-slate-900">
            Mention Velocity & Momentum Timeline
          </CardTitle>
          <CardDescription className="text-xs text-slate-500">
            Daily frequency and algorithmic momentum trajectory across the selected window
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0 h-64 w-full">
          {detail.timeline && detail.timeline.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={detail.timeline} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorMentions" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#4f46e5" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#ffffff",
                    borderColor: "#e2e8f0",
                    borderRadius: "0.5rem",
                    fontSize: "12px",
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="mention_count"
                  name="Mentions"
                  stroke="#4f46e5"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorMentions)"
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-xs text-slate-400">
              No historical timeline points recorded for this snapshot window.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Related Topics & Associated Interest Clusters */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Related Topics */}
        <Card className="border-slate-200 shadow-sm p-6">
          <h3 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-1.5">
            <Layers className="h-4 w-4 text-slate-500" /> Co-occurring Topics & Relations
          </h3>
          <div className="space-y-2">
            {detail.related_topics && detail.related_topics.length > 0 ? (
              detail.related_topics.map((rel) => (
                <div
                  key={rel.topic_id}
                  className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-xs"
                >
                  <span className="font-semibold text-slate-800">{rel.name}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-slate-400 capitalize">{rel.relation_type}</span>
                    <Badge variant="secondary">{(rel.strength * 100).toFixed(0)}% corr</Badge>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-400 py-2">No co-occurring relations mapped yet.</p>
            )}
          </div>
        </Card>

        {/* Associated Audiences */}
        <Card className="border-slate-200 shadow-sm p-6">
          <h3 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-1.5">
            <Users className="h-4 w-4 text-slate-500" /> Associated Interest Clusters
          </h3>
          <div className="space-y-2">
            {detail.associated_audiences && detail.associated_audiences.length > 0 ? (
              detail.associated_audiences.map((aud) => (
                <div
                  key={aud.cluster_id}
                  className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-xs"
                >
                  <span className="font-semibold text-slate-800">{aud.name}</span>
                  <Badge variant="default">{(aud.weight * 100).toFixed(0)}% affinity</Badge>
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-400 py-2">No cluster affinities linked yet.</p>
            )}
          </div>
        </Card>
      </div>

      {/* Ground Truth Evidence Snippets (Non-PII) */}
      <Card className="border-slate-200 shadow-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <CardTitle className="text-sm font-bold text-slate-900">
              Representative Evidence Snippets
            </CardTitle>
            <CardDescription className="text-xs text-slate-500 mt-0.5">
              Sanitized ground-truth source citations. User identifiers stripped per DPDP principles.
            </CardDescription>
          </div>
          <span className="text-xs font-mono bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
            {detail.evidence_snippets?.length || 0} snippets
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {detail.evidence_snippets && detail.evidence_snippets.length > 0 ? (
            detail.evidence_snippets.map((snip) => (
              <div
                key={snip.id}
                className="p-4 rounded-lg border border-slate-200 bg-white shadow-xs flex flex-col justify-between text-xs space-y-2"
              >
                <p className="text-slate-700 italic leading-relaxed">
                  &ldquo;{snip.content_text}&rdquo;
                </p>
                <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-[11px] text-slate-400 font-mono">
                  <span>
                    {snip.source_type} • ID: {snip.id.substring(0, 8)}
                  </span>
                  {snip.url && (
                    <a
                      href={snip.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-indigo-600 hover:underline flex items-center gap-1 font-sans"
                    >
                      Source <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                </div>
              </div>
            ))
          ) : (
            <p className="text-xs text-slate-400 col-span-2 py-4 text-center">
              No evidence snippets available for this snapshot.
            </p>
          )}
        </div>
      </Card>
    </div>
  );
}
