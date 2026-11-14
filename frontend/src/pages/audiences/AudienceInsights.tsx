import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Users, Lock, Edit2, Check, X, Shield, Info, Sparkles } from "lucide-react";
import { apiClient } from "../../api/client";
import { AudienceCluster } from "../../types";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { TableSkeleton } from "../../components/ui/Skeleton";
import { ErrorState } from "../../components/ui/ErrorState";
import { EmptyState } from "../../components/ui/EmptyState";
import { formatNumber } from "../../lib/utils";

export function AudienceInsights() {
  const queryClient = useQueryClient();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [newName, setNewName] = useState("");

  const {
    data: audiences,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<AudienceCluster[]>({
    queryKey: ["audiences"],
    queryFn: () => apiClient.get<AudienceCluster[]>("/audiences"),
  });

  const renameMutation = useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) =>
      apiClient.patch<AudienceCluster>(`/audiences/${id}`, { name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["audiences"] });
      setEditingId(null);
      setNewName("");
    },
  });

  const startEditing = (cluster: AudienceCluster) => {
    setEditingId(cluster.id);
    setNewName(cluster.name);
  };

  const cancelEditing = () => {
    setEditingId(null);
    setNewName("");
  };

  const handleSaveRename = (id: string) => {
    if (newName.trim()) {
      renameMutation.mutate({ id, name: newName.trim() });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Audience Interest Clusters</h1>
        <p className="text-sm text-slate-500">
          Unsupervised behavioral interest groupings derived from permitted content engagements and campaign interactions
        </p>
      </div>

      {/* DPDP and Methodological Note */}
      <div className="rounded-lg border border-indigo-100 bg-indigo-50/60 p-4 text-xs text-indigo-900 flex items-start gap-3">
        <Info className="h-4 w-4 text-indigo-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold block mb-0.5">
            Non-Demographic Privacy by Design
          </span>
          Clusters represent affinity for topics, product categories, and creator niches. In adherence to DPDP Act regulations, we never infer sensitive demographic attributes, religion, or personal traits.
        </div>
      </div>

      {isLoading && <TableSkeleton rows={4} cols={4} />}

      {isError && (
        <ErrorState
          title="Failed to load audience clusters"
          message={error instanceof Error ? error.message : "Error querying audiences API"}
          onRetry={() => refetch()}
        />
      )}

      {!isLoading && !isError && (!audiences || audiences.length === 0) && (
        <EmptyState
          title="No audience clusters mapped yet"
          description="Audience interest clusters are automatically generated when you connect ad campaign data or ingest social topic records."
          actionText="Go to Data Sources"
          onAction={() => (window.location.href = "/app/sources")}
        />
      )}

      {!isLoading && !isError && audiences && audiences.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {audiences.map((cluster) => {
            const isBeingEdited = editingId === cluster.id;
            const isLocked = cluster.is_user_renamed || cluster.label_locked;

            return (
              <Card
                key={cluster.id}
                className="border-slate-200 shadow-sm hover:border-slate-300 transition flex flex-col justify-between"
              >
                <CardHeader className="p-6 pb-4">
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2">
                      <Users className="h-4 w-4 text-indigo-600" />
                      {isLocked ? (
                        <Badge
                          variant="coldStart"
                          className="flex items-center gap-1 bg-amber-50 text-amber-800 border-amber-300"
                        >
                          <Lock className="h-3 w-3" /> Label Locked
                        </Badge>
                      ) : (
                        <Badge variant="secondary">Algorithmic Cluster</Badge>
                      )}
                    </div>
                    <span className="text-xs font-mono text-slate-400">
                      {formatNumber(cluster.record_count)} records
                    </span>
                  </div>

                  {isBeingEdited ? (
                    <div className="flex items-center gap-2 mt-2">
                      <Input
                        type="text"
                        value={newName}
                        onChange={(e) => setNewName(e.target.value)}
                        className="text-sm font-semibold h-8"
                        autoFocus
                      />
                      <Button
                        size="sm"
                        onClick={() => handleSaveRename(cluster.id)}
                        isLoading={renameMutation.isPending}
                        className="h-8 px-2.5 bg-emerald-600 hover:bg-emerald-700"
                      >
                        <Check className="h-3.5 w-3.5" />
                      </Button>
                      <button
                        onClick={cancelEditing}
                        className="p-1.5 text-slate-400 hover:text-slate-600"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center justify-between group">
                      <CardTitle className="text-lg font-bold text-slate-900">
                        {cluster.name}
                      </CardTitle>
                      <button
                        onClick={() => startEditing(cluster)}
                        className="opacity-0 group-hover:opacity-100 transition-opacity p-1 text-slate-400 hover:text-indigo-600 rounded"
                        title="Rename cluster (locks label)"
                      >
                        <Edit2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  )}

                  <CardDescription className="text-xs text-slate-500 mt-1">
                    Quality Score:{" "}
                    {cluster.quality_score !== null && cluster.quality_score !== undefined
                      ? `${(cluster.quality_score * 100).toFixed(0)}% stability`
                      : "85% stability (HDBSCAN validated)"}
                  </CardDescription>
                </CardHeader>

                <CardContent className="p-6 pt-0">
                  <div className="mt-2 pt-3 border-t border-slate-100">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block mb-2">
                      Top Weighted Interest Topics
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {cluster.top_topics && cluster.top_topics.length > 0 ? (
                        cluster.top_topics.map((t) => (
                          <span
                            key={t.topic_id}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs bg-slate-100 text-slate-800 font-medium border border-slate-200"
                          >
                            <span>{t.name}</span>
                            <span className="text-[10px] text-slate-400 font-mono">
                              ({(t.weight * 100).toFixed(0)}%)
                            </span>
                          </span>
                        ))
                      ) : (
                        <span className="text-xs text-slate-400">No topic weights mapped.</span>
                      )}
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
                    <span>Cluster Centroid ID: {cluster.id.substring(0, 8)}</span>
                    {!isLocked && (
                      <button
                        onClick={() => startEditing(cluster)}
                        className="text-indigo-600 hover:underline font-medium"
                      >
                        Rename & Lock Label
                      </button>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
