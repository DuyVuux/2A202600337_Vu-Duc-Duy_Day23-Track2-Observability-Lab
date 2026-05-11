# Day 23 Lab Reflection

> Fill in each section. Grader reads the "What I'd change" paragraph closest.

**Student:** Vũ Đức Duy
**Submission date:** 2026-05-12
**Lab repo URL:** https://github.com/DuyVuux/2A202600337_Vu-Duc-Duy_Day23-Track2-Observability-Lab

---

## 1. Hardware + setup output

Paste output of `python3 00-setup/verify-docker.py`:

```
Docker:        OK  (29.4.2)
Compose v2:    OK  (5.1.3)
RAM available: 15.31 GB (OK)
Ports free:    BOUND: [8000, 9090, 9093, 3100, 16686, 4317, 4318, 8888]
Report written: /home/duykhongngu28/massive/day23-observability-lab/00-setup/setup-report.json
```

---

## 2. Track 02 — Dashboards & Alerts

### 6 essential panels (screenshot)

Drop `submission/screenshots/dashboard-overview.png`.

### Burn-rate panel

Drop `submission/screenshots/slo-burn-rate.png`.

### Alert fire + resolve

| When | What | Evidence |
|---|---|---|
| _T0_ | killed `day23-app`         | screenshot `alertmanager-firing.png` |
| _T0+90s_ | `ServiceDown` fired   | screenshot `slack-firing.png` |
| _T1_ | restored app              | — |
| _T1+60s_ | alert resolved        | screenshot `slack-resolved.png` |

### One thing surprised me about Prometheus / Grafana

What surprised me most was how powerful and expressive PromQL is, particularly for calculating complex Service Level Objectives (SLOs). With just a few lines of vector math, we can seamlessly calculate multi-window burn rates and trigger alerts, entirely removing the need for heavy external computational pipelines.

---

## 3. Track 03 — Tracing & Logs

### One trace screenshot from Jaeger

Drop `submission/screenshots/jaeger-trace.png` showing `embed-text → vector-search → generate-tokens` spans.

### Log line correlated to trace

Paste the log line and the trace_id it links to:

```json
{"event": "prediction served", "model": "llama3-mock", "input_tokens": 15, "output_tokens": 42, "quality": 0.89, "duration_seconds": 1.15, "trace_id": "84d2f635a5548271b16cf0654bd5f83e", "level": "info", "logger": "main"}
```

### Tail-sampling math

Let $N$ be the total number of traces per second. Let $E$ be the number of error traces and $S$ be the number of slow traces (> 2000ms).
Based on the composite policy intent (keep all errors + keep slow + 1% probabilistic for the rest):
- Traces kept via error/slow rules: $E + S$
- Remaining "healthy" traces: $N - E - S$
- Probabilistic sampling keeps 1% of the healthy traces: $0.01 \times (N - E - S)$

**Total kept fraction** = $\frac{(E + S) + 0.01 \times (N - E - S)}{N}$

*(Note: If the system is perfectly healthy without errors or slow requests, it drops 99% of traces and keeps exactly 1% to save storage costs.)*

---

## 4. Track 04 — Drift Detection

### PSI scores

Paste `04-drift-detection/reports/drift-summary.json`:

```json
{
  "prompt_length": {
    "psi": 3.461,
    "kl": 1.7982,
    "ks_stat": 0.702,
    "ks_pvalue": 0.0,
    "drift": "yes"
  },
  "embedding_norm": {
    "psi": 0.0187,
    "kl": 0.0324,
    "ks_stat": 0.052,
    "ks_pvalue": 0.133853,
    "drift": "no"
  },
  "response_length": {
    "psi": 0.0162,
    "kl": 0.0178,
    "ks_stat": 0.056,
    "ks_pvalue": 0.086899,
    "drift": "no"
  },
  "response_quality": {
    "psi": 8.8486,
    "kl": 13.5011,
    "ks_stat": 0.941,
    "ks_pvalue": 0.0,
    "drift": "yes"
  }
}
```

### Which test fits which feature?

- **`prompt_length`**: **PSI (Population Stability Index)**. Since lengths can be naturally binned into categorical ranges (e.g., short, medium, long), PSI is an industry standard for monitoring distribution shifts in such features over time without being overly sensitive to minor fluctuations.
- **`embedding_norm`**: **KS (Kolmogorov-Smirnov) test**. The embedding norm is a continuous 1D float. The KS test is non-parametric and highly effective at detecting differences in the shape and location of continuous distributions.
- **`response_length`**: **KS test or PSI**. Similar to prompt length, but since it's a continuous/discrete numerical value, the KS test provides a strict statistical guarantee (p-value) on whether the generation length distribution has shifted (e.g., model becoming too verbose).
- **`response_quality`**: **KL (Kullback-Leibler) Divergence**. Quality scores are typically probabilities or bounded scores. KL Divergence is information-theoretic and perfectly suited for measuring how much the new quality probability distribution diverges from the reference baseline.

---

## 5. Track 05 — Cross-Day Integration

### Which prior-day metric was hardest to expose? Why?

Integrating the Day 20 LLM Serving metrics (like `llama-cpp`) is typically the hardest to expose. Unlike a standard API where you just measure request latency via middleware, exposing deep inference metrics like KV cache utilization, time-to-first-token (TTFT), and token generation speed requires instrumenting the internal generation loop and streaming mechanisms.

---

## 6. The single change that mattered most

The single change that made the biggest difference between a stack that merely "works" and one that is practically "useful" was **injecting the `trace_id` into our structured JSON logs** (as seen in the `bind_log` and `span.get_span_context().trace_id` implementation). Before this, we had isolated Prometheus metrics telling us *that* a latency spike occurred, and Jaeger showing us *where* it happened, but we had no idea *what* the exact input prompt or context was without manually digging through thousands of logs. 

By linking the `trace_id` directly into the log payload, we successfully unified the "Three Pillars of Observability" (Metrics, Traces, Logs) mentioned in the deck. This allows us to spot an anomaly in Grafana (Metrics), pivot directly to the offending trace in Jaeger to see the bottleneck (Traces), and then search that exact `trace_id` in Loki to see the raw user prompt and model parameters (Logs). It transformed debugging from a guessing game into a deterministic, linear workflow.
