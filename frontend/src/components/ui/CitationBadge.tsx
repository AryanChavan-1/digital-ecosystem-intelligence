import React from "react";
import { Link2, AlertTriangle } from "lucide-react";
import { cn } from "../../lib/utils";

interface CitationBadgeProps {
  id: string;
  isValid?: boolean;
  type?: string;
  onClick?: () => void;
}

export function CitationBadge({ id, isValid = true, type = "record", onClick }: CitationBadgeProps) {
  const shortId = id.length > 8 ? id.substring(0, 8) : id;

  if (!isValid) {
    return (
      <span
        title={`Unverified citation: ${id}`}
        className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-mono bg-rose-100 text-rose-800 border border-rose-300 mx-1"
      >
        <AlertTriangle className="h-3 w-3 text-rose-600" />
        [{type}:{shortId} (unverified)]
      </span>
    );
  }

  return (
    <button
      type="button"
      onClick={onClick}
      title={`Verified citation: ${id}`}
      className={cn(
        "inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-mono transition-colors mx-1",
        "bg-indigo-50 text-indigo-700 border border-indigo-200 hover:bg-indigo-100 cursor-pointer"
      )}
    >
      <Link2 className="h-3 w-3 text-indigo-500" />
      [{type}:{shortId}]
    </button>
  );
}

export function formatWithCitations(text: string, citations?: Array<{ id: string; valid: boolean; type?: string }>) {
  if (!text) return null;

  // Match [record:uuid] or [campaign:uuid] or [citation:uuid] or [uuid]
  const citationRegex = /\[(record|campaign|citation):([a-f0-9\-]{36})\]|\[([a-f0-9\-]{36})\]/gi;
  const parts: (string | React.ReactNode)[] = [];
  let lastIndex = 0;
  let match;

  while ((match = citationRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }

    const type = match[1] || "record";
    const id = match[2] || match[3];
    const citationMeta = citations?.find((c) => c.id === id);
    const isValid = citationMeta ? citationMeta.valid : true;

    parts.push(
      <CitationBadge key={`${id}-${match.index}`} id={id} isValid={isValid} type={type} />
    );

    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return parts;
}
