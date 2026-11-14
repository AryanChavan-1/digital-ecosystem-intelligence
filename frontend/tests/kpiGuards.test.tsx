import { describe, it, expect } from "vitest";
import { formatNumber, formatCurrency, formatPercent } from "../src/lib/utils";

describe("KPI Zero-Denominator Guards and Locale Formatting", () => {
  it("strictly renders '—' when metrics are null, undefined, or empty (zero-denominator guard)", () => {
    // Zero-denominator guards per .cursorrules: never render 0, NaN, or Infinity for null values
    expect(formatNumber(null)).toBe("—");
    expect(formatNumber(undefined)).toBe("—");
    expect(formatNumber("")).toBe("—");

    expect(formatCurrency(null, "INR")).toBe("—");
    expect(formatCurrency(undefined, "INR")).toBe("—");
    expect(formatCurrency("", "INR")).toBe("—");

    expect(formatPercent(null)).toBe("—");
    expect(formatPercent(undefined)).toBe("—");
    expect(formatPercent("")).toBe("—");
  });

  it("correctly formats valid numerical values in Indian numbering style", () => {
    expect(formatNumber(100000)).toBe("1,00,000");
    expect(formatNumber(1500000)).toBe("15,00,000");

    expect(formatPercent(2.456)).toBe("2.46%");
    expect(formatPercent(0)).toBe("0.00%");
  });

  it("handles string representations of numbers gracefully", () => {
    expect(formatNumber("25000")).toBe("25,000");
    expect(formatPercent("4.15")).toBe("4.15%");
  });
});
