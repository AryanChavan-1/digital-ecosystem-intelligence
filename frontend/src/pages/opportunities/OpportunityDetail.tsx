import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Sparkles,
  Printer,
  Save,
  CheckCircle,
  FileEdit,
  Clock,
  Shield,
} from "lucide-react";
import { apiClient } from "../../api/client";
import { Opportunity, BriefSections } from "../../types";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../../components/ui/Card";
import { ASCIAlert, AISynthesizedBanner } from "../../components/ui/ASCIAlert";
import { formatWithCitations } from "../../components/ui/CitationBadge";
import { ErrorState } from "../../components/ui/ErrorState";

const BRIEF_SECTION_CONFIG = [
  { key: "signal_summary" as const, title: "1. Executive Signal Summary", placeholder: "Synthesized core consumer movement..." },
  { key: "evidence_coverage" as const, title: "2. Evidence Coverage & Grounding", placeholder: "Data coverage, sample records, and channel breakdown..." },
  { key: "audience_hypotheses" as const, title: "3. Audience Hypotheses & Personas", placeholder: "Distinguishing interests and behavioral clusters..." },
  { key: "product_angles" as const, title: "4. D2C Product & Merchandising Angles", placeholder: "SKU adaptations, messaging angles, and formulation trends..." },
  { key: "campaign_experiments" as const, title: "5. Recommended Campaign Experiments", placeholder: "Creative hooks, test budgets (INR), and channels..." },
  { key: "risks_counter_signals" as const, title: "6. Strategic Risks & Counter-Signals", placeholder: "Seasonality, ad saturation, regulatory or platform shifts..." },
  { key: "confidence_limitations" as const, title: "7. Confidence Score & Data Limitations", placeholder: "Sample boundaries, single-source caveats, and validation rules..." },
];

export function OpportunityDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [isEditing, setIsEditing] = useState(false);
  const [editedTitle, setEditedTitle] = useState("");
  const [editedNotes, setEditedNotes] = useState("");
  const [editedSections, setEditedSections] = useState<Partial<BriefSections>>({});
  const [saveSuccess, setSaveSuccess] = useState(false);

  const {
    data: opportunity,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<Opportunity>({
    queryKey: ["opportunity", id],
    queryFn: () => apiClient.get<Opportunity>(`/opportunities/${id}`),
    enabled: !!id,
  });

  useEffect(() => {
    if (opportunity) {
      setEditedTitle(opportunity.title);
      setEditedNotes(opportunity.notes || "");
      if (opportunity.brief_json) {
        setEditedSections(opportunity.brief_json);
      }
    }
  }, [opportunity]);

  const generateBriefMutation = useMutation({
    mutationFn: () => apiClient.post<Opportunity>(`/opportunities/${id}/generate-brief`),
    onSuccess: (data) => {
      queryClient.setQueryData(["opportunity", id], data);
      if (data.brief_json) {
        setEditedSections(data.brief_json);
      }
    },
  });

  const saveMutation = useMutation({
    mutationFn: async () => {
      return apiClient.patch<Opportunity>(`/opportunities/${id}`, {
        title: editedTitle,
        notes: editedNotes,
        brief_json: {
          ...(opportunity?.brief_json || {}),
          ...editedSections,
        },
      });
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["opportunity", id], data);
      setIsEditing(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    },
  });

  const handlePrint = () => {
    window.print();
  };

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse max-w-4xl mx-auto">
        <div className="h-8 w-60 bg-slate-200 rounded" />
        <div className="h-32 bg-slate-200 rounded-lg" />
        <div className="h-96 bg-slate-200 rounded-lg" />
      </div>
    );
  }

  if (isError || !opportunity) {
    return (
      <ErrorState
        title="Opportunity Brief not found"
        message={error instanceof Error ? error.message : "Could not load opportunity brief."}
        onRetry={() => refetch()}
      />
    );
  }

  const brief = opportunity.brief_json;

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Action Bar (Hidden in Print) */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 no-print">
        <div>
          <button
            onClick={() => navigate("/app/saved")}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 mb-1 transition"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Back to Saved Opportunities
          </button>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-slate-900">{opportunity.title}</h1>
            <Badge variant="secondary" className="capitalize">
              {opportunity.status}
            </Badge>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {!isEditing ? (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsEditing(true)}
                className="gap-1.5"
              >
                <FileEdit className="h-4 w-4" /> Edit Brief
              </Button>
              <Button variant="outline" size="sm" onClick={handlePrint} className="gap-1.5">
                <Printer className="h-4 w-4" /> Print / Save as PDF
              </Button>
              {(!brief || Object.keys(brief).length === 0) && (
                <Button
                  size="sm"
                  onClick={() => generateBriefMutation.mutate()}
                  isLoading={generateBriefMutation.isPending}
                  className="gap-1.5"
                >
                  <Sparkles className="h-4 w-4" /> Generate AI Brief
                </Button>
              )}
            </>
          ) : (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setIsEditing(false);
                  if (opportunity.brief_json) setEditedSections(opportunity.brief_json);
                }}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={() => saveMutation.mutate()}
                isLoading={saveMutation.isPending}
                className="gap-1.5 bg-emerald-600 hover:bg-emerald-700"
              >
                <Save className="h-4 w-4" /> Save Changes
              </Button>
            </>
          )}
        </div>
      </div>

      {saveSuccess && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 font-semibold flex items-center gap-2 no-print">
          <CheckCircle className="h-4 w-4 text-emerald-600" /> Changes saved successfully!
        </div>
      )}

      {/* Printable Report Header */}
      <div className="p-6 bg-white border border-slate-200 rounded-lg shadow-sm print:border-none print:shadow-none print:p-0">
        <div className="flex items-start justify-between pb-6 border-b border-slate-100">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-600 block">
              Opportunity Intelligence Brief
            </span>
            <h2 className="text-2xl font-black text-slate-900 mt-1">
              {isEditing ? (
                <input
                  type="text"
                  value={editedTitle}
                  onChange={(e) => setEditedTitle(e.target.value)}
                  className="w-full font-bold text-xl border rounded px-2 py-1"
                />
              ) : (
                opportunity.title
              )}
            </h2>
            <div className="flex items-center gap-4 text-xs text-slate-400 mt-2 font-mono">
              <span className="flex items-center gap-1">
                <Clock className="h-3.5 w-3.5" /> Created:{" "}
                {new Date(opportunity.created_at).toLocaleDateString("en-IN")}
              </span>
              <span>Topic ID: {opportunity.topic_id.substring(0, 8)}</span>
              <span>Market: India (IN) • D2C</span>
            </div>
          </div>
          <div className="text-right hidden sm:block print:block">
            <span className="text-xs font-bold text-slate-900 block">Digital Ecosystem Intel</span>
            <span className="text-[10px] text-slate-400">Strict Citation & DPDP Verified</span>
          </div>
        </div>

        {/* AI provenance & ASCI Compliance Banners */}
        <div className="mt-6">
          <AISynthesizedBanner />
          <ASCIAlert />
        </div>

        {/* Brief Generation Callout if Empty */}
        {(!brief || Object.keys(brief).length === 0) && (
          <div className="my-8 text-center p-8 border border-dashed border-slate-300 rounded-lg bg-slate-50">
            <Sparkles className="h-8 w-8 text-indigo-600 mx-auto mb-2" />
            <h3 className="font-bold text-slate-900 text-sm">Brief Content Not Generated</h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto mt-1 mb-4">
              Ground this opportunity against your connected source records, ad performance, and momentum snapshots.
            </p>
            <Button
              onClick={() => generateBriefMutation.mutate()}
              isLoading={generateBriefMutation.isPending}
              size="sm"
              className="gap-2"
            >
              <Sparkles className="h-4 w-4" /> Synthesize Citation-Verified Brief
            </Button>
          </div>
        )}

        {/* 7 Core Brief Sections */}
        {brief && Object.keys(brief).length > 0 && (
          <div className="space-y-6 mt-4">
            {BRIEF_SECTION_CONFIG.map(({ key, title, placeholder }) => {
              const content = isEditing
                ? editedSections[key] ?? ""
                : brief[key] ?? "";

              return (
                <div
                  key={key}
                  className="p-5 rounded-lg border border-slate-200/90 bg-white print:border-slate-200 print-break-inside-avoid"
                >
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 border-b border-slate-100 pb-2 mb-3">
                    {title}
                  </h3>
                  {isEditing ? (
                    <textarea
                      rows={4}
                      value={editedSections[key] ?? ""}
                      onChange={(e) =>
                        setEditedSections((prev) => ({ ...prev, [key]: e.target.value }))
                      }
                      placeholder={placeholder}
                      className="w-full text-xs text-slate-800 p-2 border rounded font-mono focus:ring-1 focus:ring-indigo-500"
                    />
                  ) : (
                    <div className="text-xs text-slate-700 leading-relaxed whitespace-pre-wrap">
                      {formatWithCitations(content, brief.citations)}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Analyst Notes Section */}
        <div className="mt-8 pt-6 border-t border-slate-200 print-break-inside-avoid">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
            Analyst Collaboration Notes
          </h3>
          {isEditing ? (
            <textarea
              rows={3}
              value={editedNotes}
              onChange={(e) => setEditedNotes(e.target.value)}
              placeholder="Add internal notes, assignees, test budgets..."
              className="w-full text-xs text-slate-800 p-2 border rounded"
            />
          ) : (
            <p className="text-xs text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-100">
              {opportunity.notes || "No notes added yet."}
            </p>
          )}
        </div>

        {/* Compliance Footer on Print */}
        <div className="mt-12 pt-4 border-t border-slate-200 text-[10px] text-slate-400 flex justify-between items-center print:flex">
          <span>Confidential — Prepared for internal brand and agency planning</span>
          <span>Verified Non-PII per India Digital Personal Data Protection (DPDP) Act</span>
        </div>
      </div>
    </div>
  );
}
