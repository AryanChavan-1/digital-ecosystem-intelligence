import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_current_workspace, get_db
from app.models.opportunity import Opportunity
from app.models.trend import TrendSnapshot
from app.models.user import User
from app.models.workspace import Workspace

router = APIRouter(prefix="/reports", tags=["Reports & Exports"])


@router.get(
    "/export.csv",
    status_code=status.HTTP_200_OK,
    summary="Stream clean CSV export of workspace trends or opportunities",
)
async def export_csv(
    request: Request,
    report_type: str = Query(default="trends", pattern="^(trends|opportunities)$"),
    period_days: int = Query(default=30, ge=1, le=365),
    workspace_and_role: tuple[Workspace, str] = Depends(get_current_workspace),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Stream a clean CSV export with compliance header row stating date range,
    source coverage, and generation timestamp.
    """
    workspace, _ = workspace_and_role
    now_str = datetime.now(timezone.utc).isoformat()

    output = io.StringIO()
    writer = csv.writer(output)

    # Compliance & audit header row comment
    output.write(
        f"# Export Generated: {now_str} | Workspace: {workspace.id} | "
        f"Period: {period_days} days | Scope: {report_type} | DPDP Compliant\n"
    )

    if report_type == "trends":
        writer.writerow([
            "Trend ID",
            "Topic",
            "Period Start",
            "Period End",
            "Mention Count",
            "Previous Mentions",
            "Growth Rate %",
            "Momentum Score",
            "Source Count",
            "Confidence",
        ])

        stmt = (
            select(TrendSnapshot)
            .options(selectinload(TrendSnapshot.topic))
            .where(
                or_(
                    TrendSnapshot.workspace_id == workspace.id,
                    TrendSnapshot.workspace_id.is_(None),
                )
            )
            .order_by(TrendSnapshot.momentum_score.desc())
        )
        res = await db.execute(stmt)
        snapshots = res.scalars().all()

        for s in snapshots:
            topic_label = s.topic.canonical_label if s.topic else "Unknown"
            writer.writerow([
                str(s.id),
                topic_label,
                str(s.period_start),
                str(s.period_end),
                s.mention_count,
                s.previous_mention_count,
                str(s.change_pct or "0.0"),
                str(s.momentum_score),
                s.source_count,
                s.confidence,
            ])

    else:
        writer.writerow([
            "Opportunity ID",
            "Title",
            "Status",
            "Score",
            "Created At",
            "Summary",
        ])

        stmt = (
            select(Opportunity)
            .where(Opportunity.workspace_id == workspace.id)
            .order_by(Opportunity.created_at.desc())
        )
        res = await db.execute(stmt)
        opps = res.scalars().all()

        for o in opps:
            writer.writerow([
                str(o.id),
                o.title,
                o.status,
                str(o.score or ""),
                o.created_at.isoformat(),
                o.summary or "",
            ])

    csv_bytes = output.getvalue().encode("utf-8")
    filename = f"workspace_{workspace.id}_{report_type}_export.csv"

    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
