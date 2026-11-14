import Papa from "papaparse";

export interface CsvPreviewResult {
  headers: string[];
  rows: Record<string, string>[];
  totalRowsEstimate: number;
}

export function parseCsvPreview(file: File, maxRows: number = 20): Promise<CsvPreviewResult> {
  return new Promise((resolve, reject) => {
    let rowCount = 0;
    const previewRows: Record<string, string>[] = [];
    let detectedHeaders: string[] = [];

    Papa.parse<Record<string, string>>(file, {
      header: true,
      skipEmptyLines: "greedy",
      preview: maxRows,
      complete: (results) => {
        detectedHeaders = (results.meta.fields || []).map((h) => h.trim());
        results.data.forEach((row) => {
          if (row && typeof row === "object") {
            const cleanRow: Record<string, string> = {};
            for (const [k, v] of Object.entries(row)) {
              cleanRow[k.trim()] = typeof v === "string" ? v.trim() : String(v ?? "");
            }
            previewRows.push(cleanRow);
          }
        });

        resolve({
          headers: detectedHeaders,
          rows: previewRows,
          totalRowsEstimate: results.data.length,
        });
      },
      error: (error) => {
        reject(new Error(`Failed to parse CSV preview: ${error.message}`));
      },
    });
  });
}

export function detectAmbiguousDateFormat(dateValues: string[]): {
  isAmbiguous: boolean;
  suggestedFormat: string;
  hasUnambiguousDay: boolean;
} {
  const cleanDates = dateValues
    .map((d) => d.trim())
    .filter((d) => d && d !== "--" && d !== "-" && d !== "N/A");

  if (cleanDates.length === 0) {
    return { isAmbiguous: false, suggestedFormat: "%d/%m/%Y", hasUnambiguousDay: false };
  }

  // Check if all dates match YYYY-MM-DD
  const allYMD = cleanDates.every((d) => /^\d{4}-\d{2}-\d{2}$/.test(d));
  if (allYMD) {
    return { isAmbiguous: false, suggestedFormat: "%Y-%m-%d", hasUnambiguousDay: true };
  }

  let sawDayGreaterThan12 = false;
  let sawMonthGreaterThan12 = false;

  for (const dateStr of cleanDates) {
    // Check DD/MM/YYYY or MM/DD/YYYY (or with dash / dot)
    const match = dateStr.match(/^(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})$/);
    if (match) {
      const first = parseInt(match[1], 10);
      const second = parseInt(match[2], 10);

      if (first > 12) {
        sawDayGreaterThan12 = true; // First number is day -> DD/MM/YYYY
      }
      if (second > 12) {
        sawMonthGreaterThan12 = true; // Second number is day -> MM/DD/YYYY
      }
    }
  }

  if (sawDayGreaterThan12 && !sawMonthGreaterThan12) {
    return { isAmbiguous: false, suggestedFormat: "%d/%m/%Y", hasUnambiguousDay: true };
  }

  if (sawMonthGreaterThan12 && !sawDayGreaterThan12) {
    return { isAmbiguous: false, suggestedFormat: "%m/%d/%Y", hasUnambiguousDay: true };
  }

  // If both numbers were always <= 12 (e.g. 05/06/2026), it is genuinely ambiguous!
  return {
    isAmbiguous: true,
    suggestedFormat: "%d/%m/%Y", // Default Indian format preference
    hasUnambiguousDay: false,
  };
}

export const STANDARD_REQUIRED_COLUMNS = [
  { key: "date", label: "Date (Local)", aliases: ["date", "day", "reporting starts", "reporting date"] },
  { key: "campaign_name", label: "Campaign Name", aliases: ["campaign name", "campaign", "ad campaign"] },
  { key: "channel", label: "Platform / Channel", aliases: ["channel", "platform", "publisher platform", "source"] },
  { key: "currency", label: "Currency", aliases: ["currency", "currency code", "account currency"] },
  { key: "impressions", label: "Impressions", aliases: ["impressions", "views", "impr"] },
  { key: "clicks", label: "Clicks", aliases: ["clicks", "link clicks"] },
  { key: "spend", label: "Amount Spent (INR)", aliases: ["spend", "amount spent", "cost", "total spend (inr)"] },
  { key: "conversions", label: "Conversions / Purchases", aliases: ["conversions", "purchases", "orders", "results"] },
  { key: "attributed_revenue", label: "Attributed Revenue", aliases: ["attributed revenue", "purchase conversion value", "conversion value", "sales"] },
];

export function guessColumnMapping(headers: string[]): Record<string, string> {
  const mapping: Record<string, string> = {};

  STANDARD_REQUIRED_COLUMNS.forEach((col) => {
    const foundHeader = headers.find((h) => {
      const lower = h.toLowerCase().trim();
      return col.aliases.some((alias) => lower.includes(alias) || alias === lower);
    });
    if (foundHeader) {
      mapping[col.key] = foundHeader;
    }
  });

  return mapping;
}
