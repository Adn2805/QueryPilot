import numpy as np
from typing import Optional

def calculate_metrics(results: list[dict]) -> dict:
    """Calculate empirical evaluation metrics from actual benchmark results.
    
    NO fabricated or hardcoded numbers — computed strictly from the test run data.
    """
    total = len(results)
    if total == 0:
        return {
            "total_queries": 0,
            "execution_accuracy": 0.0,
            "clarification_accuracy": 0.0,
            "unsafe_blocked_rate": 0.0,
            "repair_success_rate": 0.0,
            "avg_latency_ms": 0.0,
            "p50_latency_ms": 0.0,
            "p95_latency_ms": 0.0,
            "avg_retries": 0.0,
        }

    # 1. Execution accuracy on supported analytical queries
    executable = [r for r in results if not r.get("is_unsafe") and r.get("is_supported")]
    successful_execs = [r for r in executable if r.get("execution_success")]
    exec_acc = (len(successful_execs) / len(executable) * 100) if executable else 0.0

    # 2. Clarification accuracy
    ambiguous_queries = [r for r in results if r.get("requires_clarification")]
    correctly_clarified = [r for r in ambiguous_queries if r.get("clarification_triggered")]
    clarif_acc = (len(correctly_clarified) / len(ambiguous_queries) * 100) if ambiguous_queries else 0.0

    # 3. Unsafe blocking rate
    unsafe_queries = [r for r in results if r.get("is_unsafe")]
    blocked_unsafe = [r for r in unsafe_queries if r.get("unsafe_blocked")]
    unsafe_rate = (len(blocked_unsafe) / len(unsafe_queries) * 100) if unsafe_queries else 100.0

    # 4. Repair success rate
    repair_attempts = [r for r in results if r.get("repair_count", 0) > 0]
    repair_success = [r for r in repair_attempts if r.get("execution_success")]
    repair_rate = (len(repair_success) / len(repair_attempts) * 100) if repair_attempts else 0.0

    # 5. Latency percentiles
    latencies = [r.get("latency_ms", 0.0) for r in results if r.get("latency_ms") is not None]
    avg_latency = float(np.mean(latencies)) if latencies else 0.0
    p50_latency = float(np.percentile(latencies, 50)) if latencies else 0.0
    p95_latency = float(np.percentile(latencies, 95)) if latencies else 0.0

    # 6. Retry counts
    retries = [r.get("repair_count", 0) for r in results]
    avg_retries = float(np.mean(retries)) if retries else 0.0

    return {
        "total_queries": total,
        "execution_accuracy": round(exec_acc, 1),
        "clarification_accuracy": round(clarif_acc, 1),
        "unsafe_blocked_rate": round(unsafe_rate, 1),
        "repair_success_rate": round(repair_rate, 1),
        "avg_latency_ms": round(avg_latency, 1),
        "p50_latency_ms": round(p50_latency, 1),
        "p95_latency_ms": round(p95_latency, 1),
        "avg_retries": round(avg_retries, 2),
    }
