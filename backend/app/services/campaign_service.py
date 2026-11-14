from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, List, Optional, Tuple


class MixedCurrencyError(ValueError):
    """Raised when metrics with differing currencies are aggregated without conversion."""
    pass


class CampaignService:
    """
    Deterministic Campaign KPI & Aggregation Engine.
    All calculations strictly use Decimal arithmetic.
    Zero or null denominators return None (JSON null), never Infinity, NaN, or fabricated 0.
    """

    ROUND_PRECISION = Decimal("0.0001")

    @classmethod
    def calculate_ctr(
        cls,
        clicks: Optional[int | Decimal],
        impressions: Optional[int | Decimal],
    ) -> Optional[Decimal]:
        """
        CTR = (clicks / impressions) * 100
        Returns None if impressions is 0, None, or clicks is None.
        """
        if clicks is None or impressions is None:
            return None
        dec_clicks = Decimal(str(clicks))
        dec_impressions = Decimal(str(impressions))
        if dec_impressions <= Decimal("0"):
            return None
        result = (dec_clicks / dec_impressions) * Decimal("100")
        return result.quantize(cls.ROUND_PRECISION, rounding=ROUND_HALF_UP)

    @classmethod
    def calculate_cpc(
        cls,
        spend: Optional[Decimal | int | float],
        clicks: Optional[int | Decimal],
    ) -> Optional[Decimal]:
        """
        CPC = spend / clicks
        Returns None if clicks is 0, None, or spend is None.
        """
        if spend is None or clicks is None:
            return None
        dec_spend = Decimal(str(spend))
        dec_clicks = Decimal(str(clicks))
        if dec_clicks <= Decimal("0"):
            return None
        result = dec_spend / dec_clicks
        return result.quantize(cls.ROUND_PRECISION, rounding=ROUND_HALF_UP)

    @classmethod
    def calculate_cpm(
        cls,
        spend: Optional[Decimal | int | float],
        impressions: Optional[int | Decimal],
    ) -> Optional[Decimal]:
        """
        CPM = (spend / impressions) * 1000
        Returns None if impressions is 0, None, or spend is None.
        """
        if spend is None or impressions is None:
            return None
        dec_spend = Decimal(str(spend))
        dec_impressions = Decimal(str(impressions))
        if dec_impressions <= Decimal("0"):
            return None
        result = (dec_spend / dec_impressions) * Decimal("1000")
        return result.quantize(cls.ROUND_PRECISION, rounding=ROUND_HALF_UP)

    @classmethod
    def calculate_cpa(
        cls,
        spend: Optional[Decimal | int | float],
        conversions: Optional[Decimal | int | float],
    ) -> Optional[Decimal]:
        """
        CPA = spend / conversions
        Returns None if conversions is 0, None, or spend is None.
        """
        if spend is None or conversions is None:
            return None
        dec_spend = Decimal(str(spend))
        dec_conversions = Decimal(str(conversions))
        if dec_conversions <= Decimal("0"):
            return None
        result = dec_spend / dec_conversions
        return result.quantize(cls.ROUND_PRECISION, rounding=ROUND_HALF_UP)

    @classmethod
    def calculate_roas(
        cls,
        attributed_revenue: Optional[Decimal | int | float],
        spend: Optional[Decimal | int | float],
    ) -> Optional[Decimal]:
        """
        ROAS = attributed_revenue / spend
        Returns None if spend is 0, None, or revenue is None.
        """
        if attributed_revenue is None or spend is None:
            return None
        dec_rev = Decimal(str(attributed_revenue))
        dec_spend = Decimal(str(spend))
        if dec_spend <= Decimal("0"):
            return None
        result = dec_rev / dec_spend
        return result.quantize(cls.ROUND_PRECISION, rounding=ROUND_HALF_UP)

    @classmethod
    def compute_kpis(
        cls,
        impressions: Optional[int | Decimal],
        clicks: Optional[int | Decimal],
        spend: Optional[Decimal | int | float],
        conversions: Optional[Decimal | int | float],
        attributed_revenue: Optional[Decimal | int | float],
    ) -> Dict[str, Optional[Decimal]]:
        """Compute all KPIs with zero-denominator safety."""
        return {
            "ctr": cls.calculate_ctr(clicks, impressions),
            "cpc": cls.calculate_cpc(spend, clicks),
            "cpm": cls.calculate_cpm(spend, impressions),
            "cpa": cls.calculate_cpa(spend, conversions),
            "roas": cls.calculate_roas(attributed_revenue, spend),
        }

    @classmethod
    def aggregate_metrics(
        cls,
        metric_items: List[Any],
        target_currency: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Aggregate a list of metric rows (either ORM objects or dictionaries)
        with strict currency isolation.

        Returns (summary_totals, daily_series).
        Raises MixedCurrencyError if multiple distinct currencies exist.
        """
        if not metric_items:
            currency = target_currency or "INR"
            totals = {
                "impressions": 0,
                "clicks": 0,
                "spend": Decimal("0.0000"),
                "conversions": Decimal("0.0000"),
                "attributed_revenue": Decimal("0.0000"),
                "currency": currency,
                "ctr": None,
                "cpc": None,
                "cpm": None,
                "cpa": None,
                "roas": None,
            }
            return totals, []

        # Enforce currency isolation
        currencies = set()
        for item in metric_items:
            curr = getattr(item, "currency", None) if not isinstance(item, dict) else item.get("currency")
            if curr:
                currencies.add(curr.upper())

        if target_currency:
            currencies.add(target_currency.upper())

        if len(currencies) > 1:
            raise MixedCurrencyError(
                f"Mixed currencies detected ({currencies}). Currency isolation prohibits summing different currencies."
            )

        currency = next(iter(currencies)) if currencies else (target_currency or "INR")

        total_impressions = 0
        total_clicks = 0
        total_spend = Decimal("0.0000")
        total_conversions = Decimal("0.0000")
        total_revenue = Decimal("0.0000")

        daily_series: List[Dict[str, Any]] = []

        for item in metric_items:
            # Extract fields
            if isinstance(item, dict):
                local_d = item.get("local_date")
                imp = item.get("impressions", 0) or 0
                clk = item.get("clicks", 0) or 0
                sp = Decimal(str(item.get("spend", 0) or 0))
                conv = Decimal(str(item.get("conversions", 0) or 0))
                rev = Decimal(str(item.get("attributed_revenue", 0) or 0))
                creative = item.get("creative_label")
                audience = item.get("audience_label")
            else:
                local_d = item.local_date
                imp = item.impressions or 0
                clk = item.clicks or 0
                sp = Decimal(str(item.spend or 0))
                conv = Decimal(str(item.conversions or 0))
                rev = Decimal(str(item.attributed_revenue or 0))
                creative = item.creative_label
                audience = item.audience_label

            total_impressions += imp
            total_clicks += clk
            total_spend += sp
            total_conversions += conv
            total_revenue += rev

            kpis = cls.compute_kpis(
                impressions=imp,
                clicks=clk,
                spend=sp,
                conversions=conv,
                attributed_revenue=rev,
            )

            daily_series.append({
                "local_date": local_d,
                "impressions": imp,
                "clicks": clk,
                "spend": sp.quantize(cls.ROUND_PRECISION, rounding=ROUND_HALF_UP),
                "conversions": conv.quantize(cls.ROUND_PRECISION, rounding=ROUND_HALF_UP),
                "attributed_revenue": rev.quantize(cls.ROUND_PRECISION, rounding=ROUND_HALF_UP),
                "creative_label": creative,
                "audience_label": audience,
                **kpis,
            })

        summary_kpis = cls.compute_kpis(
            impressions=total_impressions,
            clicks=total_clicks,
            spend=total_spend,
            conversions=total_conversions,
            attributed_revenue=total_revenue,
        )

        totals = {
            "impressions": total_impressions,
            "clicks": total_clicks,
            "spend": total_spend.quantize(cls.ROUND_PRECISION, rounding=ROUND_HALF_UP),
            "conversions": total_conversions.quantize(cls.ROUND_PRECISION, rounding=ROUND_HALF_UP),
            "attributed_revenue": total_revenue.quantize(cls.ROUND_PRECISION, rounding=ROUND_HALF_UP),
            "currency": currency,
            **summary_kpis,
        }

        return totals, daily_series
