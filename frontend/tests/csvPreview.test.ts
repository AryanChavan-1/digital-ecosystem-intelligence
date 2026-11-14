import { describe, it, expect } from "vitest";
import {
  parseCsvPreview,
  detectAmbiguousDateFormat,
  guessColumnMapping,
} from "../src/lib/csvParser";

describe("CSV Preview and Date Ambiguity Resolver", () => {
  it("parses CSV preview and extracts headers and rows", async () => {
    const csvContent = `Date,Campaign Name,Platform,Spend,Clicks,Impressions
25/10/2026,Diwali Festive Sale,Meta Ads,15000,450,12000
26/10/2026,Diwali Festive Sale,Meta Ads,18000,520,14500`;

    const file = new File([csvContent], "campaigns.csv", { type: "text/csv" });
    const result = await parseCsvPreview(file, 20);

    expect(result.headers).toEqual([
      "Date",
      "Campaign Name",
      "Platform",
      "Spend",
      "Clicks",
      "Impressions",
    ]);
    expect(result.rows).toHaveLength(2);
    expect(result.rows[0]["Campaign Name"]).toBe("Diwali Festive Sale");
    expect(result.rows[0]["Date"]).toBe("25/10/2026");
  });

  it("caps preview rows at maxRows limit (e.g. 20 rows)", async () => {
    const rows = Array.from({ length: 50 })
      .map((_, i) => `2026-10-${String((i % 28) + 1).padStart(2, "0")},Campaign ${i},Meta,1000`)
      .join("\n");
    const csvContent = `Date,Campaign Name,Platform,Spend\n${rows}`;

    const file = new File([csvContent], "large.csv", { type: "text/csv" });
    const result = await parseCsvPreview(file, 20);

    expect(result.rows.length).toBeLessThanOrEqual(20);
  });

  it("detects unambiguous ISO date format YYYY-MM-DD", () => {
    const sample = ["2026-10-05", "2026-10-12", "2026-10-25"];
    const check = detectAmbiguousDateFormat(sample);

    expect(check.isAmbiguous).toBe(false);
    expect(check.suggestedFormat).toBe("%Y-%m-%d");
  });

  it("detects unambiguous DD/MM/YYYY when day > 12", () => {
    const sample = ["25/10/2026", "26/10/2026", "02/11/2026"];
    const check = detectAmbiguousDateFormat(sample);

    expect(check.isAmbiguous).toBe(false);
    expect(check.suggestedFormat).toBe("%d/%m/%Y");
    expect(check.hasUnambiguousDay).toBe(true);
  });

  it("detects unambiguous MM/DD/YYYY when month position has day > 12", () => {
    const sample = ["10/25/2026", "10/26/2026", "11/02/2026"];
    const check = detectAmbiguousDateFormat(sample);

    expect(check.isAmbiguous).toBe(false);
    expect(check.suggestedFormat).toBe("%m/%d/%Y");
    expect(check.hasUnambiguousDay).toBe(true);
  });

  it("flags genuine date ambiguity when all day and month values are <= 12", () => {
    const sample = ["05/06/2026", "06/07/2026", "01/02/2026"];
    const check = detectAmbiguousDateFormat(sample);

    expect(check.isAmbiguous).toBe(true);
    expect(check.hasUnambiguousDay).toBe(false);
    // Defaults to Indian convention recommendation
    expect(check.suggestedFormat).toBe("%d/%m/%Y");
  });

  it("auto-guesses column mappings from typical ad export headers", () => {
    const headers = [
      "Reporting Starts",
      "Campaign Name",
      "Publisher Platform",
      "Account Currency",
      "Impressions",
      "Link Clicks",
      "Amount Spent (INR)",
      "Purchases",
      "Purchase Conversion Value",
    ];

    const mapping = guessColumnMapping(headers);

    expect(mapping.date).toBe("Reporting Starts");
    expect(mapping.campaign_name).toBe("Campaign Name");
    expect(mapping.channel).toBe("Publisher Platform");
    expect(mapping.currency).toBe("Account Currency");
    expect(mapping.impressions).toBe("Impressions");
    expect(mapping.clicks).toBe("Link Clicks");
    expect(mapping.spend).toBe("Amount Spent (INR)");
    expect(mapping.conversions).toBe("Purchases");
    expect(mapping.attributed_revenue).toBe("Purchase Conversion Value");
  });
});
