"""Evaluate retrieved evidence and preserve per-query traces."""
from typing import Any


def check_hit(hit: dict[str, Any], question: dict[str, Any]) -> bool:
    """A hit occurs when the chunk belongs to gold source/page and contains sufficient evidence quote."""
    meta = hit.get("metadata", {})
    chunk_page = meta.get("page")
    chunk_text = hit.get("text", "")
    
    gold_page = question.get("gold_page")
    evidence_quote = question.get("evidence_quote", "")
    
    # 1. Page match check
    if chunk_page != gold_page:
        return False
        
    # 2. Evidence match check: clean both texts for robust whitespace comparison
    norm_chunk = " ".join(chunk_text.split()).lower()
    norm_quote = " ".join(evidence_quote.split()).lower()
    
    # Check if quote is in chunk, or if significant prefix of quote is present
    if norm_quote in norm_chunk:
        return True
        
    # Check if a substantial part (>= 60 chars) matches
    if len(norm_quote) > 60 and norm_quote[:60] in norm_chunk:
        return True
        
    return False


def evaluate_query(question: dict[str, Any], hits: list[dict[str, Any]]) -> dict[str, Any]:
    """Check source/page and evidence containment; retain Hit@1 and Hit@3 traces."""
    hit_statuses = [check_hit(h, question) for h in hits]
    
    hit_at_1 = 1 if (len(hit_statuses) > 0 and hit_statuses[0]) else 0
    hit_at_3 = 1 if any(hit_statuses[:3]) else 0
    
    # Check filter compliance
    expected_filter = question.get("filter")
    filter_compliant = True
    if expected_filter:
        for h in hits:
            meta = h.get("metadata", {})
            for k, v in expected_filter.items():
                if meta.get(k) != v:
                    filter_compliant = False
                    break
    else:
        filter_compliant = None  # N/A

    return {
        "question_id": question.get("id"),
        "split": question.get("split"),
        "question": question.get("question"),
        "gold_page": question.get("gold_page"),
        "evidence_quote": question.get("evidence_quote"),
        "filter": expected_filter,
        "hit_at_1": hit_at_1,
        "hit_at_3": hit_at_3,
        "filter_compliant": filter_compliant,
        "hits": [
            {
                "rank": idx + 1,
                "chunk_id": h.get("chunk_id"),
                "page": h.get("metadata", {}).get("page"),
                "section": h.get("metadata", {}).get("section"),
                "score": round(float(h.get("score", 0.0)), 4),
                "is_gold_hit": hit_statuses[idx],
                "text_snippet": h.get("text", "")[:120] + "..."
            }
            for idx, h in enumerate(hits)
        ]
    }


def summarize(traces: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate Hit@1 and Evidence Hit@3 by strategy and dev/test split."""
    summary: dict[str, Any] = {}
    
    for split in ["dev", "test", "overall"]:
        if split == "overall":
            split_traces = traces
        else:
            split_traces = [t for t in traces if t["split"] == split]
            
        total = len(split_traces)
        if total == 0:
            continue
            
        h1_count = sum(t["hit_at_1"] for t in split_traces)
        h3_count = sum(t["hit_at_3"] for t in split_traces)
        
        filter_traces = [t for t in split_traces if t["filter_compliant"] is not None]
        filter_compliant_count = sum(1 for t in filter_traces if t["filter_compliant"] is True)
        
        summary[split] = {
            "total_questions": total,
            "hit_at_1_count": h1_count,
            "hit_at_1_ratio": f"{h1_count}/{total}",
            "hit_at_1_pct": round(h1_count / total * 100, 1),
            "hit_at_3_count": h3_count,
            "hit_at_3_ratio": f"{h3_count}/{total}",
            "hit_at_3_pct": round(h3_count / total * 100, 1),
            "filter_compliant_count": filter_compliant_count,
            "filter_total": len(filter_traces),
            "filter_ratio": f"{filter_compliant_count}/{len(filter_traces)}" if filter_traces else "N/A"
        }
        
    return summary
