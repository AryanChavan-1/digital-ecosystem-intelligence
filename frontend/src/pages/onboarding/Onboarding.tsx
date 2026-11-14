import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Sparkles, UploadCloud, CheckCircle2, ArrowRight } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { Button } from "../../components/ui/Button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/Card";

export function Onboarding() {
  const { currentWorkspace, updateWorkspace, seedDemoData } = useAuth();
  const navigate = useNavigate();

  const [industry, setIndustry] = useState<string>("Sustainable Fashion & D2C Apparel");
  const [marketRegion] = useState<string>("IN");
  const [currency] = useState<string>("INR");
  const [timezone] = useState<string>("Asia/Kolkata");
  const [isLoadingDemo, setIsLoadingDemo] = useState<boolean>(false);
  const [isSaving, setIsSaving] = useState<boolean>(false);

  const handleSaveSettings = async () => {
    if (!currentWorkspace) return;
    setIsSaving(true);
    try {
      await updateWorkspace(currentWorkspace.id, {
        industry,
        market_region: marketRegion,
        default_currency: currency,
        timezone: timezone,
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleSeedDemoAndProceed = async () => {
    if (!currentWorkspace) return;
    setIsLoadingDemo(true);
    try {
      await handleSaveSettings();
      await seedDemoData(currentWorkspace.id, industry);
      navigate("/app");
    } catch {
      // Fallback navigate
      navigate("/app");
    } finally {
      setIsLoadingDemo(false);
    }
  };

  const handleGoToUpload = async () => {
    await handleSaveSettings();
    navigate("/app/campaigns");
  };

  const handleSkip = async () => {
    await handleSaveSettings();
    navigate("/app");
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
      <div className="max-w-2xl w-full space-y-6">
        <div className="text-center space-y-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-700">
            <Sparkles className="h-3.5 w-3.5" /> 5-Minute Fast Setup
          </span>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            Configure Your Intelligence Workspace
          </h1>
          <p className="text-sm text-slate-600 max-w-lg mx-auto">
            Tailor the signal detection algorithms, momentum tracking, and currency formatting to your target Indian consumer segment.
          </p>
        </div>

        <Card className="border-slate-200 shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg">Workspace Parameters</CardTitle>
            <CardDescription>
              Configure the industry category and default reporting parameters for {currentWorkspace?.name || "your workspace"}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700">Primary Industry Vertical</label>
              <select
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value="Sustainable Fashion & D2C Apparel">Sustainable Fashion & D2C Apparel</option>
                <option value="Clean Beauty & Personal Care">Clean Beauty & Personal Care (D2C)</option>
                <option value="Health, Wellness & Organic Foods">Health, Wellness & Organic Foods</option>
                <option value="Home Living & Direct-to-Consumer Goods">Home Living & Direct-to-Consumer Goods</option>
              </select>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                <span className="text-[11px] font-semibold text-slate-500 block uppercase">Target Market</span>
                <span className="text-sm font-bold text-slate-800">India (IN)</span>
              </div>
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                <span className="text-[11px] font-semibold text-slate-500 block uppercase">Currency Base</span>
                <span className="text-sm font-bold text-slate-800">INR (₹) Lakhs/Crores</span>
              </div>
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                <span className="text-[11px] font-semibold text-slate-500 block uppercase">Timezone</span>
                <span className="text-sm font-bold text-slate-800">Asia/Kolkata (IST)</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 2 Path Choice Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            onClick={handleSeedDemoAndProceed}
            className="group relative cursor-pointer rounded-xl border-2 border-indigo-200 bg-gradient-to-br from-indigo-50/50 to-white p-6 shadow-sm hover:border-indigo-600 transition flex flex-col justify-between"
          >
            <div>
              <div className="h-10 w-10 rounded-lg bg-indigo-600 text-white flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
                <Sparkles className="h-5 w-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900">Explore Demo Intelligence</h3>
              <p className="mt-1 text-xs text-slate-600 leading-relaxed">
                Pre-populate your workspace with sample rising topics, D2C ad metrics, interest clusters, and generated opportunity briefs.
              </p>
            </div>
            <div className="mt-6 flex items-center text-xs font-bold text-indigo-600 gap-1 group-hover:gap-2 transition-all">
              {isLoadingDemo ? "Loading Demo Signals..." : "Load Demo Dataset & Explore"}
              <ArrowRight className="h-4 w-4" />
            </div>
          </div>

          <div
            onClick={handleGoToUpload}
            className="group relative cursor-pointer rounded-xl border border-slate-200 bg-white p-6 shadow-sm hover:border-slate-400 transition flex flex-col justify-between"
          >
            <div>
              <div className="h-10 w-10 rounded-lg bg-slate-100 text-slate-700 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
                <UploadCloud className="h-5 w-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900">Upload Campaign CSV</h3>
              <p className="mt-1 text-xs text-slate-600 leading-relaxed">
                Import your Meta Ads, Google Ads, or Shopify CSV export with 20-row client-side preview and Indian currency sanitizer.
              </p>
            </div>
            <div className="mt-6 flex items-center text-xs font-bold text-slate-700 gap-1 group-hover:gap-2 transition-all">
              Go to CSV Upload Wizard
              <ArrowRight className="h-4 w-4" />
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between pt-2">
          <div className="flex items-center gap-1.5 text-xs text-slate-500">
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            <span>DPDP non-PII compliance active</span>
          </div>
          <Button variant="ghost" size="sm" onClick={handleSkip} disabled={isSaving}>
            Skip directly to Dashboard
          </Button>
        </div>
      </div>
    </div>
  );
}
