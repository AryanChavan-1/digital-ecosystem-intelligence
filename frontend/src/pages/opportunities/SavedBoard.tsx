import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Lightbulb, Plus, Clock, ArrowRight, CheckCircle2 } from "lucide-react";
import { apiClient } from "../../api/client";
import { Opportunity } from "../../types";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../../components/ui/Card";
import { TableSkeleton } from "../../components/ui/Skeleton";
import { ErrorState } from "../../components/ui/ErrorState";
import { EmptyState } from "../../components/ui/EmptyState";

export function SavedBoard() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [filterStatus, setFilterStatus] = useState<string>("all");

  const {
    data: opportunities,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<Opportunity[]>({
    queryKey: ["opportunities"],
    queryFn: () => apiClient.get<Opportunity[]>("/opportunities"),
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: Opportunity["status"] }) =>
      apiClient.patch<Opportunity>(`/opportunities/${id}`, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["opportunities"] });
    },
  });

  const filteredOpportunities = opportunities?.filter((opp) => {
    if (filterStatus === "all") return true;
    return opp.status === filterStatus;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Saved Opportunities & Briefs</h1>
          <p className="text-sm text-slate-500">
            Track and collaborate on evidence-grounded marketing briefs and campaign experiments
          </p>
        </div>

        <Button onClick={() => navigate("/app/trends")} className="gap-2">
          <Plus className="h-4 w-4" /> Discover New Signals
        </Button>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 border-b border-slate-200 pb-2">
        {["all", "draft", "review", "approved"].map((status) => (
          <button
            key={status}
            onClick={() => setFilterStatus(status)}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold capitalize transition ${
              filterStatus === status
                ? "bg-indigo-50 text-indigo-700"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            }`}
          >
            {status}
          </button>
        ))}
      </div>

      {isLoading && <TableSkeleton rows={5} cols={4} />}

      {isError && (
        <ErrorState
          title="Failed to load opportunities"
          message={error instanceof Error ? error.message : "Error querying opportunities API"}
          onRetry={() => refetch()}
        />
      )}

      {!isLoading && !isError && (!filteredOpportunities || filteredOpportunities.length === 0) && (
        <EmptyState
          title="No saved opportunities in this view"
          description="Identify rising signals on the Trend Explorer and generate an evidence-backed Opportunity Brief with 1 click."
          actionText="Go to Trend Explorer"
          onAction={() => navigate("/app/trends")}
        />
      )}

      {!isLoading && !isError && filteredOpportunities && filteredOpportunities.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredOpportunities.map((opp) => (
            <Card
              key={opp.id}
              className="border-slate-200 shadow-sm hover:border-indigo-300 transition flex flex-col justify-between"
            >
              <CardHeader className="p-5 pb-3">
                <div className="flex items-center justify-between mb-2">
                  <Badge
                    variant={
                      opp.status === "approved"
                        ? "success"
                        : opp.status === "review"
                        ? "warning"
                        : "secondary"
                    }
                    className="capitalize"
                  >
                    {opp.status}
                  </Badge>
                  <span className="text-[11px] text-slate-400 flex items-center gap-1 font-mono">
                    <Clock className="h-3 w-3" />
                    {new Date(opp.created_at).toLocaleDateString("en-IN")}
                  </span>
                </div>
                <CardTitle className="text-base font-bold text-slate-900 leading-snug">
                  <Link
                    to={`/app/opportunities/${opp.id}`}
                    className="hover:text-indigo-600 transition"
                  >
                    {opp.title}
                  </Link>
                </CardTitle>
                <CardDescription className="text-xs text-slate-500 mt-1 line-clamp-2">
                  {opp.brief_json?.signal_summary || opp.notes || "Draft opportunity ready for synthesis."}
                </CardDescription>
              </CardHeader>

              <CardContent className="p-5 pt-0">
                <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <select
                    value={opp.status}
                    onChange={(e) =>
                      updateStatusMutation.mutate({
                        id: opp.id,
                        status: e.target.value as Opportunity["status"],
                      })
                    }
                    className="rounded border border-slate-200 bg-slate-50 px-2 py-1 text-xs text-slate-700 capitalize focus:outline-none"
                  >
                    <option value="draft">Draft</option>
                    <option value="review">In Review</option>
                    <option value="approved">Approved</option>
                    <option value="archived">Archived</option>
                  </select>

                  <Link
                    to={`/app/opportunities/${opp.id}`}
                    className="inline-flex items-center gap-1 font-semibold text-indigo-600 hover:text-indigo-800"
                  >
                    View Brief <ArrowRight className="h-3.5 w-3.5" />
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
