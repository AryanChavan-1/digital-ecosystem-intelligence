import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Search, Filter, ArrowUpDown } from "lucide-react";
import { apiClient } from "../../api/client";
import { TrendItem } from "../../types";
import { Input } from "../../components/ui/Input";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../../components/ui/Card";
import { TableSkeleton } from "../../components/ui/Skeleton";
import { ErrorState } from "../../components/ui/ErrorState";
import { EmptyState } from "../../components/ui/EmptyState";
import { formatNumber, formatPercent } from "../../lib/utils";

export function TrendExplorer() {
  const [search, setSearch] = useState("");
  const [confidence, setConfidence] = useState<string>("");
  const [minMomentum, setMinMomentum] = useState<number>(0);
  const [periodDays, setPeriodDays] = useState<number>(30);

  const {
    data: trends,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<TrendItem[]>({
    queryKey: ["trends", search, confidence, minMomentum, periodDays],
    queryFn: () =>
      apiClient.get<TrendItem[]>("/trends", {
        search: search || undefined,
        confidence: confidence || undefined,
        min_momentum: minMomentum > 0 ? minMomentum : undefined,
        period_days: periodDays,
      }),
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Trend Explorer</h1>
        <p className="text-sm text-slate-500">
          Search and rank emerging consumer signals across Indian e-commerce and social content
        </p>
      </div>

      {/* Filter Toolbar */}
      <Card className="border-slate-200 shadow-sm p-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <Input
              type="text"
              placeholder="Search topics (e.g. Linen, Vitamin C)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-600 whitespace-nowrap">Confidence:</span>
            <select
              value={confidence}
              onChange={(e) => setConfidence(e.target.value)}
              className="w-full rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-xs shadow-sm focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="">All Levels</option>
              <option value="high">High Confidence</option>
              <option value="medium">Medium Confidence</option>
              <option value="low">Low (Snapshot)</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-600 whitespace-nowrap">Window:</span>
            <div className="flex rounded-md border border-slate-200 bg-slate-50 p-0.5 w-full">
              {[7, 30, 90].map((days) => (
                <button
                  key={days}
                  type="button"
                  onClick={() => setPeriodDays(days)}
                  className={`flex-1 py-1 text-xs font-semibold rounded transition ${
                    periodDays === days
                      ? "bg-white text-indigo-600 shadow-sm"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  {days}d
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-600 whitespace-nowrap">Min Momentum:</span>
            <input
              type="range"
              min="0"
              max="90"
              step="10"
              value={minMomentum}
              onChange={(e) => setMinMomentum(Number(e.target.value))}
              className="w-full accent-indigo-600 cursor-pointer"
            />
            <span className="text-xs font-mono font-bold text-slate-700 w-6 text-right">
              {minMomentum}
            </span>
          </div>
        </div>
      </Card>

      {/* Results Table */}
      <Card className="border-slate-200 shadow-sm">
        <CardHeader className="p-6 pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base font-bold text-slate-900">
                Ranked Emerging Signals
              </CardTitle>
              <CardDescription className="text-xs text-slate-500 mt-0.5">
                Calculated using time-decayed frequency and cross-source corroboration
              </CardDescription>
            </div>
            {trends && (
              <span className="text-xs font-semibold text-slate-500">
                Showing {trends.length} {trends.length === 1 ? "topic" : "topics"}
              </span>
            )}
          </div>
        </CardHeader>

        <CardContent className="p-0">
          {isLoading && (
            <div className="p-6">
              <TableSkeleton rows={8} cols={6} />
            </div>
          )}

          {isError && (
            <div className="p-6">
              <ErrorState
                title="Failed to load trends"
                message={error instanceof Error ? error.message : "Error querying trends API"}
                onRetry={() => refetch()}
              />
            </div>
          )}

          {!isLoading && !isError && trends && trends.length === 0 && (
            <div className="p-8">
              <EmptyState
                title="No trends found"
                description="Try broadening your search query, lowering the minimum momentum filter, or adjusting the time window."
                actionText="Reset Filters"
                onAction={() => {
                  setSearch("");
                  setConfidence("");
                  setMinMomentum(0);
                  setPeriodDays(30);
                }}
              />
            </div>
          )}

          {!isLoading && !isError && trends && trends.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-y border-slate-200 bg-slate-50/75 text-slate-500 uppercase tracking-wider font-semibold">
                    <th className="px-6 py-3">Topic Name</th>
                    <th className="px-4 py-3">Category</th>
                    <th className="px-4 py-3">
                      <div className="flex items-center gap-1 cursor-pointer">
                        Momentum Score <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </th>
                    <th className="px-4 py-3">Mentions</th>
                    <th className="px-4 py-3">Change %</th>
                    <th className="px-4 py-3">Sources</th>
                    <th className="px-4 py-3">Confidence & Scoring</th>
                    <th className="px-6 py-3 text-right">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {trends.map((item) => (
                    <tr key={item.trend_id} className="hover:bg-slate-50/60 transition group">
                      <td className="px-6 py-3.5 font-bold text-slate-900">
                        <Link
                          to={`/app/trends/${item.trend_id}`}
                          className="hover:text-indigo-600 transition"
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
                      <td className="px-4 py-3.5 text-slate-700 font-medium">
                        {formatNumber(item.mention_count)}
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
                          <Badge variant="coldStart">Low / Single-Source Snapshot</Badge>
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
                            {item.confidence === "high"
                              ? "High Confidence"
                              : item.confidence === "medium"
                              ? "Medium Confidence"
                              : "Low Confidence"}
                          </Badge>
                        )}
                      </td>
                      <td className="px-6 py-3.5 text-right">
                        <Link to={`/app/trends/${item.trend_id}`}>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-xs text-indigo-600 hover:text-indigo-700"
                          >
                            Inspect
                          </Button>
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
