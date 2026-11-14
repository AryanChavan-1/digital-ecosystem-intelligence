import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  TrendingUp,
  Lightbulb,
  Database,
  Layers,
  ArrowUpRight,
  Clock,
  Sparkles,
  Upload,
} from "lucide-react";
import { apiClient } from "../../api/client";
import { DashboardSummary } from "../../types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { TableSkeleton } from "../../components/ui/Skeleton";
import { ErrorState } from "../../components/ui/ErrorState";
import { EmptyState } from "../../components/ui/EmptyState";
import { formatNumber, formatPercent } from "../../lib/utils";

export function Overview() {
  const navigate = useNavigate();

  const {
    data: summary,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<DashboardSummary>({
    queryKey: ["dashboard-summary"],
    queryFn: () => apiClient.get<DashboardSummary>("/dashboard/summary"),
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Workspace Overview</h1>
          <p className="text-sm text-slate-500">Loading intelligence signals and trend momentum...</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-28 rounded-lg border border-slate-200 bg-white p-5 animate-pulse" />
          ))}
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-6">
          <TableSkeleton rows={5} cols={5} />
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <ErrorState
        title="Unable to load dashboard overview"
        message={error instanceof Error ? error.message : "Failed to fetch workspace summary"}
        onRetry={() => refetch()}
      />
    );
  }

  const trackedCount = summary?.tracked_topics ?? summary?.tracked_topics_count ?? 0;
  const risingCount = summary?.rising_topics ?? summary?.rising_topics_count ?? 0;
  const savedCount = summary?.saved_opportunities ?? summary?.saved_opportunities_count ?? 0;
  const sourcesCount = summary?.connected_sources ?? summary?.connected_sources_count ?? 0;
  const freshnessTimestamp = summary?.latest_freshness_timestamp ?? summary?.data_freshness?.latest_snapshot_at;

  const hasData =
    summary &&
    (trackedCount > 0 ||
      sourcesCount > 0 ||
      (summary.top_rising_trends && summary.top_rising_trends.length > 0));

  if (!hasData) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Workspace Overview</h1>
            <p className="text-sm text-slate-500">Welcome to your digital intelligence workspace</p>
          </div>
        </div>

        <EmptyState
          title="No intelligence signals detected yet"
          description="Connect your campaign performance data or load our curated Indian D2C demo dataset to start discovering emerging trends."
          actionText="Explore Trend Explorer"
          onAction={() => navigate("/app/trends")}
        />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="p-6 border-slate-200">
            <h3 className="font-bold text-slate-900 mb-1">Option 1: Ingest Ad Performance Data</h3>
            <p className="text-xs text-slate-500 mb-4">
              Upload Meta Ads, Google Ads, or Shopify CSV exports with Indian rupee and lakhs formatting.
            </p>
            <Button size="sm" onClick={() => navigate("/app/campaigns")} className="gap-2">
              <Upload className="h-4 w-4" /> Go to Campaign Upload
            </Button>
          </Card>

          <Card className="p-6 border-slate-200">
            <h3 className="font-bold text-slate-900 mb-1">Option 2: Explore Discovery Modules</h3>
            <p className="text-xs text-slate-500 mb-4">
              Inspect audience interest clusters or generate citation-grounded opportunity briefs.
            </p>
            <Button size="sm" variant="outline" onClick={() => navigate("/app/audiences")}>
              View Audience Clusters
            </Button>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header & Data Freshness Indicator */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Workspace Overview</h1>
          <p className="text-sm text-slate-500">
            Real-time cross-channel intelligence and momentum rankings for Indian D2C
          </p>
        </div>

        <div className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-sm text-xs text-slate-600">
          <Clock className="h-3.5 w-3.5 text-indigo-500" />
          <span>Freshness:</span>
          <span className="font-semibold text-slate-800">
            {freshnessTimestamp
              ? new Date(freshnessTimestamp).toLocaleDateString("en-IN", {
                  month: "short",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })
              : "Live Snapshot"}
          </span>
        </div>
      </div>

      {/* KPI Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-slate-200 shadow-sm hover:border-slate-300 transition">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0 p-5">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Tracked Topics
            </CardTitle>
            <Layers className="h-4 w-4 text-slate-400" />
          </CardHeader>
          <CardContent className="px-5 pb-5 pt-0">
            <div className="text-2xl font-extrabold text-slate-900">
              {formatNumber(trackedCount)}
            </div>
            <p className="text-xs text-slate-500 mt-1">Ground consumer signals</p>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm hover:border-slate-300 transition">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0 p-5">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Rising Topics
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent className="px-5 pb-5 pt-0">
            <div className="text-2xl font-extrabold text-emerald-600">
              {formatNumber(risingCount)}
            </div>
            <p className="text-xs text-emerald-700 mt-1">Momentum score &gt; 50</p>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm hover:border-slate-300 transition">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0 p-5">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Saved Opportunities
            </CardTitle>
            <Lightbulb className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent className="px-5 pb-5 pt-0">
            <div className="text-2xl font-extrabold text-slate-900">
              {formatNumber(savedCount)}
            </div>
            <p className="text-xs text-slate-500 mt-1">Briefs ready for execution</p>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm hover:border-slate-300 transition">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0 p-5">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Connected Sources
            </CardTitle>
            <Database className="h-4 w-4 text-indigo-500" />
          </CardHeader>
          <CardContent className="px-5 pb-5 pt-0">
            <div className="text-2xl font-extrabold text-slate-900">
              {formatNumber(sourcesCount)}
            </div>
            <p className="text-xs text-slate-500 mt-1">DPDP compliant channels</p>
          </CardContent>
        </Card>
      </div>

      {/* Top Rising Trends Section */}
      <Card className="border-slate-200 shadow-sm">
        <CardHeader className="flex flex-row items-center justify-between p-6">
          <div>
            <CardTitle className="text-base font-bold text-slate-900">
              Top Rising Trends in India
            </CardTitle>
            <CardDescription className="text-xs text-slate-500 mt-0.5">
              Ranked by consumer momentum score and multi-source corroboration
            </CardDescription>
          </div>
          <Link to="/app/trends">
            <Button variant="outline" size="sm" className="gap-1 text-xs">
              View All Trends <ArrowUpRight className="h-3.5 w-3.5" />
            </Button>
          </Link>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-y border-slate-200 bg-slate-50/75 text-slate-500 uppercase tracking-wider font-semibold">
                  <th className="px-6 py-3">Topic / Signal</th>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3">Momentum</th>
                  <th className="px-4 py-3">Growth (vs Prev)</th>
                  <th className="px-4 py-3">Evidence Coverage</th>
                  <th className="px-4 py-3">Confidence</th>
                  <th className="px-6 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {summary.top_rising_trends.map((item) => (
                  <tr key={item.trend_id} className="hover:bg-slate-50/60 transition">
                    <td className="px-6 py-3.5 font-bold text-slate-900">
                      <Link
                        to={`/app/trends/${item.trend_id}`}
                        className="hover:text-indigo-600 transition flex items-center gap-1.5"
                      >
                        {item.topic_name}
                      </Link>
                    </td>
                    <td className="px-4 py-3.5 text-slate-600">{item.category || "General"}</td>
                    <td className="px-4 py-3.5 font-bold text-slate-900">
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-slate-100 rounded-full h-2 overflow-hidden">
                          <div
                            className="bg-indigo-600 h-2 rounded-full"
                            style={{ width: `${Math.min(100, Math.max(0, item.momentum_score))}%` }}
                          />
                        </div>
                        <span>{item.momentum_score.toFixed(1)}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3.5">
                      {item.change_pct !== null && item.change_pct !== undefined ? (
                        <span
                          className={`font-semibold ${
                            item.change_pct >= 0 ? "text-emerald-600" : "text-rose-600"
                          }`}
                        >
                          {item.change_pct >= 0 ? "+" : ""}
                          {formatPercent(item.change_pct)}
                        </span>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3.5 text-slate-600">
                      {item.source_count} {item.source_count === 1 ? "source" : "sources"}
                    </td>
                    <td className="px-4 py-3.5">
                      {item.is_cold_start ? (
                        <Badge variant="coldStart">Single-Source Snapshot</Badge>
                      ) : (
                        <Badge
                          variant={
                            item.confidence === "high"
                              ? "success"
                              : item.confidence === "medium"
                              ? "default"
                              : "warning"
                          }
                        >
                          {item.confidence.toUpperCase()}
                        </Badge>
                      )}
                    </td>
                    <td className="px-6 py-3.5 text-right">
                      <Link to={`/app/trends/${item.trend_id}`}>
                        <Button variant="ghost" size="sm" className="text-xs text-indigo-600 hover:text-indigo-700">
                          Inspect
                        </Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
