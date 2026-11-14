export interface User {
  id: string;
  email: string;
  full_name?: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  industry?: string | null;
  market_region: string;
  default_currency: string;
  timezone: string;
  created_by?: string;
  created_at: string;
}

export interface MeResponseData {
  user: User;
  workspaces: Workspace[];
  current_workspace: Workspace | null;
}

export interface ApiResponseEnvelope<T> {
  data: T;
  meta: {
    request_id?: string;
    generated_at?: string;
    [key: string]: unknown;
  };
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  details?: unknown;
  request_id?: string;
}

export interface ApiErrorResponse {
  error: ApiErrorDetail;
}

export interface TrendItem {
  trend_id: string;
  topic_id: string;
  topic_name: string;
  category?: string | null;
  momentum_score: number;
  mention_count: number;
  previous_mention_count: number;
  change_pct: number | null;
  source_count: number;
  confidence: "low" | "medium" | "high";
  confidence_badge: string;
  is_cold_start: boolean;
  period_start: string;
  period_end: string;
  generated_at: string;
}

export interface DashboardSummary {
  tracked_topics?: number;
  tracked_topics_count?: number;
  rising_topics?: number;
  rising_topics_count?: number;
  saved_opportunities?: number;
  saved_opportunities_count?: number;
  connected_sources?: number;
  connected_sources_count?: number;
  top_rising_trends: TrendItem[];
  latest_freshness_timestamp?: string | null;
  data_freshness?: {
    latest_snapshot_at: string | null;
    source_counts?: Record<string, number>;
  };
}

export interface TrendDetail extends TrendItem {
  summary: string;
  timeline: Array<{
    date: string;
    mention_count: number;
    momentum: number;
  }>;
  source_breakdown: Record<string, number>;
  related_topics: Array<{
    topic_id: string;
    name: string;
    relation_type: string;
    strength: number;
  }>;
  evidence_snippets: Array<{
    id: string;
    content_text: string;
    source_type: string;
    published_at: string;
    url?: string | null;
  }>;
  associated_audiences: Array<{
    cluster_id: string;
    name: string;
    weight: number;
  }>;
}

export interface AudienceCluster {
  id: string;
  workspace_id: string;
  name: string;
  is_user_renamed: boolean;
  label_locked: boolean;
  record_count: number;
  quality_score: number | null;
  top_topics: Array<{
    topic_id: string;
    name: string;
    weight: number;
  }>;
  created_at: string;
  updated_at: string;
}

export interface BriefSections {
  signal_summary: string;
  evidence_coverage: string;
  audience_hypotheses: string;
  product_angles: string;
  campaign_experiments: string;
  risks_counter_signals: string;
  confidence_limitations: string;
  citations?: Array<{
    id: string;
    valid: boolean;
    type?: string;
  }>;
  asci_disclosure?: string;
}

export interface Opportunity {
  id: string;
  workspace_id: string;
  topic_id: string;
  title: string;
  status: "draft" | "review" | "approved" | "archived";
  brief_json: BriefSections | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  topic_name?: string;
  topic_category?: string;
}

export interface DataSource {
  id: string;
  workspace_id: string;
  name: string;
  source_type: string;
  status: string;
  record_count: number;
  last_synced_at: string | null;
  created_at: string;
}

export interface UploadResponse {
  upload_id: string;
  upload_url: string;
  object_key: string;
}

export interface UploadStatus {
  id: string;
  status: string;
  original_filename: string;
  file_size_bytes: number;
  mapping: Record<string, string> | null;
  created_at: string;
  completed_at: string | null;
  job_status?: string | null;
  rows_accepted?: number;
  rows_quarantined?: number;
}

export interface Campaign {
  id: string;
  workspace_id: string;
  external_campaign_id: string;
  name: string;
  channel: string;
  start_date: string | null;
  end_date: string | null;
  currency: string;
  created_at: string;
}

export interface CampaignSummary {
  campaign_id: string;
  campaign_name?: string;
  currency: string;
  total_impressions: number;
  total_clicks: number;
  total_spend: number | string;
  total_conversions: number;
  total_attributed_revenue: number | string;
  ctr: number | string | null;
  cpc: number | string | null;
  cpm: number | string | null;
  cpa: number | string | null;
  roas: number | string | null;
}
