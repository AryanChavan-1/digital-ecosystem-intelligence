import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Database,
  Trash2,
  UploadCloud,
  CheckCircle2,
  AlertOctagon,
  Clock,
  ShieldCheck,
  FileSpreadsheet,
} from "lucide-react";
import { apiClient } from "../../api/client";
import { DataSource } from "../../types";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../../components/ui/Card";
import { Modal } from "../../components/ui/Modal";
import { CampaignUploadModal } from "../../components/campaigns/CampaignUploadModal";
import { TableSkeleton } from "../../components/ui/Skeleton";
import { ErrorState } from "../../components/ui/ErrorState";
import { EmptyState } from "../../components/ui/EmptyState";
import { formatNumber } from "../../lib/utils";

export function DataSources() {
  const queryClient = useQueryClient();
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [sourceToDelete, setSourceToDelete] = useState<DataSource | null>(null);
  const [deleteErrorMessage, setDeleteErrorMessage] = useState<string | null>(null);

  const {
    data: sources,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<DataSource[]>({
    queryKey: ["sources"],
    queryFn: () => apiClient.get<DataSource[]>("/sources"),
  });

  const deleteSourceMutation = useMutation({
    mutationFn: (sourceId: string) => apiClient.delete(`/data/${sourceId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sources"] });
      setSourceToDelete(null);
      setDeleteErrorMessage(null);
    },
    onError: (err: Error) => {
      setDeleteErrorMessage(err.message || "Failed to purge source data");
    },
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Data Connectors & Governance</h1>
          <p className="text-sm text-slate-500">
            Manage connected campaign exports, public datasets, and exercise DPDP data erasure rights
          </p>
        </div>

        <Button onClick={() => setIsUploadOpen(true)} className="gap-2 shadow-sm">
          <UploadCloud className="h-4 w-4" /> Connect New CSV Source
        </Button>
      </div>

      {/* DPDP Governance Notice */}
      <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm flex items-start gap-3">
        <ShieldCheck className="h-5 w-5 text-emerald-600 shrink-0 mt-0.5" />
        <div className="text-xs text-slate-600">
          <span className="font-bold text-slate-800 block">
            India Digital Personal Data Protection (DPDP) Act Compliance
          </span>
          All ingested data is partitioned strictly by workspace tenant. You may delete any source at any time to irreversibly purge raw storage files, derived topic assignments, and extracted records.
        </div>
      </div>

      {isLoading && <TableSkeleton rows={4} cols={5} />}

      {isError && (
        <ErrorState
          title="Failed to load data sources"
          message={error instanceof Error ? error.message : "Error querying sources API"}
          onRetry={() => refetch()}
        />
      )}

      {!isLoading && !isError && (!sources || sources.length === 0) && (
        <EmptyState
          title="No data sources connected yet"
          description="Upload an ad performance CSV or connect an industry dataset to begin ingesting records into your workspace."
          actionText="Upload Ad Performance CSV"
          onAction={() => setIsUploadOpen(true)}
        />
      )}

      {!isLoading && !isError && sources && sources.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sources.map((src) => (
            <Card
              key={src.id}
              className="border-slate-200 shadow-sm hover:border-slate-300 transition flex flex-col justify-between"
            >
              <CardHeader className="p-5 pb-3">
                <div className="flex items-center justify-between mb-2">
                  <Badge
                    variant={src.status === "active" ? "success" : "secondary"}
                    className="capitalize"
                  >
                    {src.status}
                  </Badge>
                  <span className="text-[11px] text-slate-400 font-mono">
                    ID: {src.id.substring(0, 8)}
                  </span>
                </div>
                <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <FileSpreadsheet className="h-4 w-4 text-indigo-600 shrink-0" />
                  <span className="truncate">{src.name}</span>
                </CardTitle>
                <CardDescription className="text-xs text-slate-500 uppercase tracking-wider font-semibold mt-1">
                  Type: {src.source_type}
                </CardDescription>
              </CardHeader>

              <CardContent className="p-5 pt-0">
                <div className="py-2.5 border-y border-slate-100 flex items-center justify-between text-xs font-mono">
                  <span className="text-slate-500">Records Ingested</span>
                  <span className="font-bold text-slate-800">{formatNumber(src.record_count)}</span>
                </div>

                <div className="mt-3 flex items-center justify-between text-xs">
                  <span className="text-[11px] text-slate-400 flex items-center gap-1 font-sans">
                    <Clock className="h-3 w-3" />
                    {src.last_synced_at
                      ? new Date(src.last_synced_at).toLocaleDateString("en-IN")
                      : "Recently Added"}
                  </span>

                  <button
                    onClick={() => setSourceToDelete(src)}
                    className="inline-flex items-center gap-1 text-xs text-rose-600 hover:text-rose-800 font-semibold p-1 hover:bg-rose-50 rounded transition"
                    title="Purge source and delete raw files"
                  >
                    <Trash2 className="h-3.5 w-3.5" /> Purge
                  </button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* DPDP Delete Source Confirmation Modal */}
      <Modal
        isOpen={!!sourceToDelete}
        onClose={() => {
          setSourceToDelete(null);
          setDeleteErrorMessage(null);
        }}
        title="Confirm DPDP Data Erasure"
        description="Irreversible purge of source records and raw files"
        maxWidth="md"
      >
        <div className="space-y-4">
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-800 flex items-start gap-2.5">
            <AlertOctagon className="h-5 w-5 text-rose-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold block">Permanent Deletion Warning</span>
              Are you sure you want to delete source{" "}
              <strong className="font-bold">{sourceToDelete?.name}</strong>? This action will:
              <ul className="list-disc list-inside mt-1 space-y-0.5">
                <li>Permanently remove raw uploaded CSVs from object storage.</li>
                <li>Cascade purge all {sourceToDelete?.record_count || 0} extracted source records.</li>
                <li>Remove derived topic assignments and write an immutable audit log.</li>
              </ul>
            </div>
          </div>

          {deleteErrorMessage && (
            <div className="p-2 bg-rose-100 text-rose-800 rounded text-xs">
              {deleteErrorMessage}
            </div>
          )}

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setSourceToDelete(null);
                setDeleteErrorMessage(null);
              }}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => {
                if (sourceToDelete) {
                  deleteSourceMutation.mutate(sourceToDelete.id);
                }
              }}
              isLoading={deleteSourceMutation.isPending}
              className="gap-1.5"
            >
              <Trash2 className="h-3.5 w-3.5" /> Permanently Purge Source
            </Button>
          </div>
        </div>
      </Modal>

      {/* CSV Upload Wizard Modal */}
      <CampaignUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onSuccess={() => {
          refetch();
        }}
      />
    </div>
  );
}
