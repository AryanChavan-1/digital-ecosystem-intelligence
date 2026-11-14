import React, { useState, useRef } from "react";
import { UploadCloud, FileText, CheckCircle2, AlertTriangle, ArrowRight, ArrowLeft } from "lucide-react";
import { Modal } from "../ui/Modal";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";
import {
  parseCsvPreview,
  detectAmbiguousDateFormat,
  guessColumnMapping,
  STANDARD_REQUIRED_COLUMNS,
  CsvPreviewResult,
} from "../../lib/csvParser";
import { apiClient } from "../../api/client";
import { UploadResponse } from "../../types";

interface CampaignUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function CampaignUploadModal({ isOpen, onClose, onSuccess }: CampaignUploadModalProps) {
  const [step, setStep] = useState<"file" | "preview" | "uploading" | "complete">("file");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<CsvPreviewResult | null>(null);
  const [columnMapping, setColumnMapping] = useState<Record<string, string>>({});
  const [dateFormat, setDateFormat] = useState<string>("%d/%m/%Y");
  const [isDateAmbiguous, setIsDateAmbiguous] = useState<boolean>(false);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const resetState = () => {
    setStep("file");
    setFile(null);
    setPreview(null);
    setColumnMapping({});
    setDateFormat("%d/%m/%Y");
    setIsDateAmbiguous(false);
    setIsProcessing(false);
    setErrorMessage(null);
  };

  const handleClose = () => {
    resetState();
    onClose();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    if (!selectedFile.name.endsWith(".csv")) {
      setErrorMessage("Please select a valid CSV file (.csv)");
      return;
    }

    if (selectedFile.size > 25 * 1024 * 1024) {
      setErrorMessage("File exceeds the 25 MB upload limit.");
      return;
    }

    setFile(selectedFile);
    setErrorMessage(null);
    setIsProcessing(true);

    try {
      const result = await parseCsvPreview(selectedFile, 20);
      setPreview(result);

      // Guess initial mapping
      const guessed = guessColumnMapping(result.headers);
      setColumnMapping(guessed);

      // Check dates in guessed date column
      const dateCol = guessed.date;
      if (dateCol) {
        const sampleDates = result.rows.map((r) => r[dateCol]).filter(Boolean);
        const dateCheck = detectAmbiguousDateFormat(sampleDates);
        setIsDateAmbiguous(dateCheck.isAmbiguous);
        setDateFormat(dateCheck.suggestedFormat);
      }

      setStep("preview");
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Error reading CSV preview");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleMappingChange = (standardKey: string, csvHeader: string) => {
    const updated = { ...columnMapping, [standardKey]: csvHeader };
    setColumnMapping(updated);

    if (standardKey === "date" && preview) {
      const sampleDates = preview.rows.map((r) => r[csvHeader]).filter(Boolean);
      const dateCheck = detectAmbiguousDateFormat(sampleDates);
      setIsDateAmbiguous(dateCheck.isAmbiguous);
      setDateFormat(dateCheck.suggestedFormat);
    }
  };

  const handleProceedUpload = async () => {
    if (!file || !preview) return;

    // Validate date and campaign_name are mapped
    if (!columnMapping.date || !columnMapping.campaign_name) {
      setErrorMessage("Please map at least Date and Campaign Name columns.");
      return;
    }

    setIsProcessing(true);
    setErrorMessage(null);
    setStep("uploading");

    try {
      // 1. Request signed upload URL from backend
      const uploadInit = await apiClient.post<UploadResponse>("/uploads", {
        original_filename: file.name,
        file_size_bytes: file.size,
        mapping: columnMapping,
        date_format: dateFormat,
      });

      // 2. Upload file to presigned URL (S3 / Local adapter)
      await apiClient.uploadToPresignedUrl(uploadInit.upload_url, file);

      // 3. Confirm upload to trigger background validation / ingestion
      await apiClient.post(`/uploads/${uploadInit.upload_id}/confirm`, {
        mapping: columnMapping,
        date_format: dateFormat,
      });

      setStep("complete");
      onSuccess();
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Upload processing failed");
      setStep("preview");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Upload Campaign Performance CSV"
      description="Client-side preview with Indian currency & lakhs sanitizer"
      maxWidth="4xl"
    >
      {errorMessage && (
        <div className="mb-4 rounded-md bg-rose-50 p-3 text-xs text-rose-700 border border-rose-200">
          {errorMessage}
        </div>
      )}

      {/* Step 1: Select File */}
      {step === "file" && (
        <div className="space-y-4">
          <div
            onClick={() => fileInputRef.current?.click()}
            className="flex flex-col items-center justify-center p-8 border-2 border-dashed border-slate-300 rounded-lg hover:border-indigo-500 cursor-pointer bg-slate-50/50 transition group"
          >
            <div className="h-12 w-12 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
              <UploadCloud className="h-6 w-6" />
            </div>
            <p className="text-sm font-semibold text-slate-800">
              Click or drag your Meta Ads, Google Ads, or Shopify CSV export
            </p>
            <p className="text-xs text-slate-500 mt-1">
              Supports ₹ (INR), Lakhs/Crores commas, and auto summary-row dropping • Up to 25 MB
            </p>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="hidden"
            />
          </div>

          <div className="text-[11px] text-slate-400 bg-slate-50 p-3 rounded border border-slate-200">
            <strong>Security Notice:</strong> The first 20 rows are parsed entirely in your browser memory for verification before any file upload to secure cloud storage.
          </div>
        </div>
      )}

      {/* Step 2: 20-Row Preview & Column Mapping & Date Ambiguity Resolution */}
      {step === "preview" && preview && (
        <div className="space-y-5">
          {/* Ambiguous Date Format Warning Banner */}
          {isDateAmbiguous && (
            <div className="p-3 bg-amber-50 border border-amber-300 rounded-lg text-xs text-amber-900 flex items-start gap-2.5">
              <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
              <div className="flex-1">
                <span className="font-bold block">Ambiguous Date Format Detected</span>
                <span>
                  The sample date values have day and month numbers &le; 12. Please explicitly confirm your date convention:
                </span>
                <div className="mt-2 flex gap-4">
                  <label className="flex items-center gap-1.5 font-semibold cursor-pointer">
                    <input
                      type="radio"
                      name="dateFormat"
                      value="%d/%m/%Y"
                      checked={dateFormat === "%d/%m/%Y"}
                      onChange={(e) => setDateFormat(e.target.value)}
                    />
                    DD/MM/YYYY (Indian Standard e.g. 05/10/2026 = 5th Oct)
                  </label>
                  <label className="flex items-center gap-1.5 font-semibold cursor-pointer">
                    <input
                      type="radio"
                      name="dateFormat"
                      value="%m/%d/%Y"
                      checked={dateFormat === "%m/%d/%Y"}
                      onChange={(e) => setDateFormat(e.target.value)}
                    />
                    MM/DD/YYYY (US Format e.g. 05/10/2026 = 10th May)
                  </label>
                </div>
              </div>
            </div>
          )}

          {/* Column Mapper Grid */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
              1. Map Standard Campaign Fields
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 max-h-48 overflow-y-auto p-1 border rounded bg-slate-50">
              {STANDARD_REQUIRED_COLUMNS.map((col) => (
                <div key={col.key} className="p-2 bg-white rounded border border-slate-200 text-xs">
                  <div className="font-semibold text-slate-700 mb-1 flex items-center justify-between">
                    <span>{col.label}</span>
                    {columnMapping[col.key] && (
                      <Badge variant="success" className="text-[10px] py-0 px-1.5">
                        Mapped
                      </Badge>
                    )}
                  </div>
                  <select
                    value={columnMapping[col.key] || ""}
                    onChange={(e) => handleMappingChange(col.key, e.target.value)}
                    className="w-full text-xs border rounded p-1 text-slate-800 bg-white"
                  >
                    <option value="">-- Ignore / Not in CSV --</option>
                    {preview.headers.map((h) => (
                      <option key={h} value={h}>
                        {h}
                      </option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          </div>

          {/* 20-Row In-Browser Data Preview */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                2. Client-Side Preview (First 20 Rows)
              </h4>
              <span className="text-[11px] font-mono text-slate-400">
                {preview.rows.length} rows previewed
              </span>
            </div>

            <div className="overflow-x-auto max-h-48 border rounded-lg bg-white">
              <table className="w-full text-left text-[11px] border-collapse">
                <thead>
                  <tr className="bg-slate-100 text-slate-600 border-b border-slate-200">
                    {preview.headers.slice(0, 8).map((h) => (
                      <th key={h} className="px-3 py-2 font-semibold whitespace-nowrap">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono">
                  {preview.rows.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-50">
                      {preview.headers.slice(0, 8).map((h) => (
                        <td key={h} className="px-3 py-1.5 whitespace-nowrap text-slate-700">
                          {row[h] || "—"}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between pt-3 border-t border-slate-200">
            <Button variant="ghost" size="sm" onClick={() => setStep("file")} className="gap-1">
              <ArrowLeft className="h-4 w-4" /> Change File
            </Button>
            <Button
              size="sm"
              onClick={handleProceedUpload}
              isLoading={isProcessing}
              className="gap-1.5"
            >
              Confirm & Ingest Records <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Step 3: Uploading State */}
      {step === "uploading" && (
        <div className="py-12 flex flex-col items-center justify-center text-center space-y-3">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent" />
          <h3 className="text-sm font-bold text-slate-800">Uploading and Sanitizing Campaign Data</h3>
          <p className="text-xs text-slate-500 max-w-sm">
            Applying Indian currency regex, dropping summary rows, and computing zero-denominator guarded metrics...
          </p>
        </div>
      )}

      {/* Step 4: Complete State */}
      {step === "complete" && (
        <div className="py-8 flex flex-col items-center justify-center text-center space-y-4">
          <div className="h-12 w-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center">
            <CheckCircle2 className="h-7 w-7" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900">Campaign Ingestion Enqueued!</h3>
            <p className="text-xs text-slate-600 max-w-sm mt-1">
              Your CSV has been securely staged and mapped. The campaign summary engine has begun calculating CTR, CPC, CPM, CPA, and ROAS.
            </p>
          </div>
          <Button onClick={handleClose} size="sm">
            View Campaign Analytics
          </Button>
        </div>
      )}
    </Modal>
  );
}
