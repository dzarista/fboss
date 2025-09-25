
/**
 * RawSectionRenderer
 * - Renders raw text line-by-line to enable simple per-line navigation.
 * - Highlights regex matches from anomalies with { type: 'Regex Match' or 'regex_match', line, span:[start,end] }.
 *
 * Props:
 *   - rawContent: string
 *   - anomalies: array (optional)
 *   - className: string (optional)
 */
export default function RawSectionRenderer({ rawContent, anomalies, className }) {
  const text = typeof rawContent === 'string' ? rawContent : '';
  const lines = text.length ? text.split('\n') : ['No content available'];

  // Group regex matches by line; handle both old format { line, span } and new format { line_spans }
  const perLine = new Map();
  if (Array.isArray(anomalies)) {
    for (const a of anomalies) {
      const t = ((a && a.type) || '').toLowerCase();
      const isRegex = t === 'regex match' || t === 'regex_match';
      if (!isRegex) continue;

      // Handle new multi-line format with line_spans
      if (Array.isArray(a?.line_spans)) {
        for (const lineSpan of a.line_spans) {
          if (!Number.isInteger(lineSpan?.line) || !Array.isArray(lineSpan?.span) || lineSpan.span.length !== 2) continue;

          const [start, end] = lineSpan.span;
          if (!Number.isInteger(start) || !Number.isInteger(end) || end <= start) continue;

          const arr = perLine.get(lineSpan.line) || [];
          arr.push({ start, end, severity: a.severity || 'low' });
          perLine.set(lineSpan.line, arr);
        }
      }
      // Handle old single-line format for backward compatibility
      else if (Number.isInteger(a?.line) && Array.isArray(a?.span) && a.span.length === 2) {
        const [start, end] = a.span;
        if (Number.isInteger(start) && Number.isInteger(end) && end > start) {
          const arr = perLine.get(a.line) || [];
          arr.push({ start, end, severity: a.severity || 'low' });
          perLine.set(a.line, arr);
        }
      }
    }
  }

  // Merge overlapping spans on a line; keep the highest severity.
  const sevRank = { low: 0, medium: 1, high: 2 };
  const mergeSpans = (spans) => {
    if (!spans || spans.length === 0) return [];
    const sorted = spans.slice().sort((a, b) => a.start - b.start || a.end - b.end);
    const merged = [];
    for (const s of sorted) {
      if (!merged.length) {
        merged.push({ ...s });
        continue;
      }
      const last = merged[merged.length - 1];
      if (s.start <= last.end) {
        last.end = Math.max(last.end, s.end);
        if ((sevRank[s.severity] || 0) > (sevRank[last.severity] || 0)) last.severity = s.severity;
      } else {
        merged.push({ ...s });
      }
    }
    return merged;
  };

  return (
    <div className={className} style={{ whiteSpace: 'pre', fontFamily: 'monospace' }}>
      {lines.map((lineText, i) => {
        const spans = perLine.has(i) ? mergeSpans(perLine.get(i)) : [];
        if (spans.length === 0) {
          return (
            <div key={i} className="raw-line" data-line={i}>
              {lineText}
            </div>
          );
        }

        // Build segments with <mark> for each merged span
        const parts = [];
        let cursor = 0;
        spans.forEach((m, idx) => {
          const s = Math.max(0, Math.min(m.start, lineText.length));
          const e = Math.max(s, Math.min(m.end, lineText.length));
          if (s > cursor) parts.push(lineText.slice(cursor, s));
          parts.push(
            <mark
              key={`${i}-${idx}`}
              className={`regex-highlight severity-${m.severity}`}
              style={{
                backgroundColor: 'rgba(239, 68, 68, 0.35)', // visible even without CSS
                borderRadius: 2,
                padding: '0 2px'
              }}
            >
              {lineText.slice(s, e)}
            </mark>
          );
          cursor = e;
        });
        if (cursor < lineText.length) parts.push(lineText.slice(cursor));

        return (
          <div key={i} className="raw-line" data-line={i}>
            {parts}
          </div>
        );
      })}
    </div>
  );
}
