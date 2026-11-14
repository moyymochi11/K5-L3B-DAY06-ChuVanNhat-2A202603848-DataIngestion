"""Suggested pipeline entry point; implements end-to-end orchestration."""
import csv
import json
import os
import time
from pathlib import Path

from .chunking import by_paragraph, fixed_size
from .embeddings import MyEmbedder
from .evaluation import evaluate_query, summarize
from .ingestion import load_pdf
from .store import ChromaVectorStore


def main() -> None:
    print("=" * 70)
    print("DAY 06: DATA INGESTION ENGINEERING PIPELINE")
    print("=" * 70)

    # 1. Locate files
    project_root = Path(__file__).resolve().parent.parent.parent
    pdf_path = project_root / "data" / "vinuni_international_student_handbook.pdf"
    if not pdf_path.exists():
        pdf_path = project_root / "starter" / "data" / "vinuni_international_student_handbook.pdf"
        
    benchmark_path = project_root / "benchmark" / "benchmark.json"

    print(f"[Setup] PDF path: {pdf_path}")
    print(f"[Setup] Benchmark path: {benchmark_path}")

    # Load pages
    pages = load_pdf(pdf_path, document_id="vinuni-handbook-2024", source="vinuni_handbook.pdf")
    if len(pages) < 30:
        raise ValueError(f"Requirement failed: expected >= 30 content pages, got {len(pages)}")

    # Load benchmark
    with open(benchmark_path, "r", encoding="utf-8") as f:
        benchmark = json.load(f)
    print(f"[Setup] Loaded {len(benchmark)} benchmark questions.")

    # 2. Initialize Embedder and Store
    embedder = MyEmbedder("all-MiniLM-L6-v2")
    store = ChromaVectorStore(
        persist_dir=str(project_root / "starter" / "chroma_store"),
        dimensions=embedder.dimensions
    )

    strategies = [
        {
            "id": "A",
            "name": "Fixed-Size Window",
            "chunker": lambda p: fixed_size(p, size=500, overlap=50),
            "use_filter": False,
            "hypothesis": "Fixed-size windows ensure consistent chunk length but may cut sentences mid-thought, degrading coherence."
        },
        {
            "id": "B",
            "name": "Paragraph / Structure-Aware",
            "chunker": lambda p: by_paragraph(p, max_size=500),
            "use_filter": False,
            "hypothesis": "Sentence/paragraph boundaries keep thoughts whole, improving coherence and semantic retrieval."
        },
        {
            "id": "C",
            "name": "Paragraph + Metadata Filtering",
            "chunker": lambda p: by_paragraph(p, max_size=500),
            "use_filter": True,
            "hypothesis": "Applying metadata filter on top of structure-aware chunks restricts search scope and eliminates out-of-section noise."
        }
    ]

    all_summaries = {}
    results_dir = project_root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # To avoid re-embedding B's chunks for C:
    cached_b_chunks = None
    cached_b_vectors = None

    for strat in strategies:
        strat_id = strat["id"]
        print("\n" + "-" * 50)
        print(f"RUNNING STRATEGY {strat_id}: {strat['name']}")
        print("-" * 50)

        start_time = time.time()

        # Ingest & Chunk
        if strat_id == "C" and cached_b_chunks is not None:
            chunks = cached_b_chunks
            vectors = cached_b_vectors
            print(f"[{strat_id}] Reusing {len(chunks)} chunks & vectors from Strategy B.")
        else:
            chunks = []
            for page in pages:
                chunks.extend(strat["chunker"](page))
            print(f"[{strat_id}] Generated {len(chunks)} total chunks.")

            # Embed
            texts = [c.text for c in chunks]
            print(f"[{strat_id}] Embedding {len(texts)} chunks...")
            vectors = embedder.embed_documents(texts)

            if strat_id == "B":
                cached_b_chunks = chunks
                cached_b_vectors = vectors

        # Upsert
        store.upsert(strategy=strat_id, chunks=chunks, vectors=vectors)
        ingest_duration = round(time.time() - start_time, 2)
        print(f"[{strat_id}] Ingestion completed in {ingest_duration}s.")

        # Query & Evaluate
        traces = []
        for q in benchmark:
            q_vector = embedder.embed_query(q["question"])
            q_filter = q.get("filter") if strat["use_filter"] else None

            hits = store.search(
                strategy=strat_id,
                query_vector=q_vector,
                top_k=3,
                filters=q_filter
            )

            trace = evaluate_query(q, hits)
            traces.append(trace)

        # Summarize
        strat_summary = summarize(traces)
        strat_summary["ingest_time_seconds"] = ingest_duration
        strat_summary["chunk_count"] = len(chunks)
        strat_summary["cost_usd"] = 0.0
        all_summaries[strat_id] = strat_summary

        # Save Traces
        trace_file = results_dir / f"traces_strategy_{strat_id}.json"
        with open(trace_file, "w", encoding="utf-8") as f:
            json.dump({"strategy": strat_id, "summary": strat_summary, "traces": traces}, f, indent=2, ensure_ascii=False)
        print(f"[{strat_id}] Saved trace to {trace_file}")

        print(f"[{strat_id}] DEV  Hit@1: {strat_summary['dev']['hit_at_1_ratio']} ({strat_summary['dev']['hit_at_1_pct']}%) | Hit@3: {strat_summary['dev']['hit_at_3_ratio']} ({strat_summary['dev']['hit_at_3_pct']}%)")
        print(f"[{strat_id}] TEST Hit@1: {strat_summary['test']['hit_at_1_ratio']} ({strat_summary['test']['hit_at_1_pct']}%) | Hit@3: {strat_summary['test']['hit_at_3_ratio']} ({strat_summary['test']['hit_at_3_pct']}%)")
        if strat_summary["overall"]["filter_total"] > 0:
            print(f"[{strat_id}] Filter Compliance: {strat_summary['overall']['filter_ratio']}")

    # 3. Save Overall Summary
    summary_file = results_dir / "benchmark_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(all_summaries, f, indent=2, ensure_ascii=False)
    print(f"\n[Overall] Saved full benchmark summary to {summary_file}")

    # 4. Update artifacts/experiment_log.csv
    exp_log_path = project_root / "artifacts" / "experiment_log.csv"
    with open(exp_log_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "strategy", "chunking", "chunk_size", "overlap", "metadata", "filter",
            "vectorizer", "hypothesis", "dev_hit1", "dev_hit3", "test_hit1", "test_hit3", "notes"
        ])
        for strat in strategies:
            sid = strat["id"]
            s = all_summaries[sid]
            chunking_type = "fixed" if sid == "A" else "paragraph"
            c_size = 500
            overlap = 50 if sid == "A" else 0
            filter_val = "section" if sid == "C" else "none"
            writer.writerow([
                sid,
                chunking_type,
                c_size,
                overlap,
                "document_id,source,page,section,year,language",
                filter_val,
                "all-MiniLM-L6-v2 (local ONNX, 384 dim)",
                strat["hypothesis"],
                s["dev"]["hit_at_1_ratio"],
                s["dev"]["hit_at_3_ratio"],
                s["test"]["hit_at_1_ratio"],
                s["test"]["hit_at_3_ratio"],
                f"chunks={s['chunk_count']}, time={s['ingest_time_seconds']}s, cost=$0.00"
            ])
    print(f"[Overall] Updated {exp_log_path}")
    print("=" * 70)
    print("PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    main()
