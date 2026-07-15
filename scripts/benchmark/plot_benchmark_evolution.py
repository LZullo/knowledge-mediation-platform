"""
Gera gráficos simples de evolução v1 → v2 → v3 a partir de artefatos benchmark_*.json.

Uso:
  python scripts/benchmark/plot_benchmark_evolution.py \\
    --runs results/benchmark_20260525_160434.json \\
           results/benchmark_20260526_020326.json \\
           results/benchmark_<teste3_run_id>.json \\
    --labels v1 v2 v3
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt


def _load_summaries(path: Path) -> dict[str, dict[str, float]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, dict[str, float]] = {}
    for summary in data.get("summaries", []):
        out[str(summary["scenario"])] = {
            "mean_f1": float(summary["mean_f1"]),
            "mean_latency_seconds": float(summary["mean_latency_seconds"]),
        }
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Gráficos de evolução do benchmark")
    parser.add_argument("--runs", nargs="+", required=True, help="Caminhos JSON de benchmark")
    parser.add_argument("--labels", nargs="+", required=True, help="Rótulos (ex.: v1 v2 v3)")
    parser.add_argument(
        "--output-dir",
        default="results/plots",
        help="Diretório de saída dos gráficos",
    )
    args = parser.parse_args()

    if len(args.runs) != len(args.labels):
        raise SystemExit("--runs e --labels devem ter o mesmo tamanho")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    scenarios = ["llm", "rag_basic", "rag_rerank"]
    versions = args.labels
    summaries_per_version: list[dict[str, dict[str, float]]] = []
    for run_path in args.runs:
        summaries_per_version.append(_load_summaries(Path(run_path)))

    # F1 por cenário (barras agrupadas)
    fig, ax = plt.subplots(figsize=(9, 5))
    width = 0.25
    x = range(len(scenarios))
    for i, label in enumerate(versions):
        offsets = [xi + (i - 1) * width for xi in x]
        f1_vals = [summaries_per_version[i].get(s, {}).get("mean_f1", 0.0) for s in scenarios]
        ax.bar(offsets, f1_vals, width=width, label=label)
    ax.set_xticks(list(x))
    ax.set_xticklabels(scenarios)
    ax.set_ylabel("F1 médio")
    ax.set_title("F1 médio por cenário e versão do corpus")
    ax.legend()
    fig.tight_layout()
    f1_path = output_dir / "f1_by_scenario.png"
    fig.savefig(f1_path, dpi=120)
    plt.close(fig)

    # Latência por cenário
    fig, ax = plt.subplots(figsize=(9, 5))
    for i, label in enumerate(versions):
        offsets = [xi + (i - 1) * width for xi in x]
        lat_vals = [
            summaries_per_version[i].get(s, {}).get("mean_latency_seconds", 0.0)
            for s in scenarios
        ]
        ax.bar(offsets, lat_vals, width=width, label=label)
    ax.set_xticks(list(x))
    ax.set_xticklabels(scenarios)
    ax.set_ylabel("Latência média (s)")
    ax.set_title("Latência média por cenário e versão do corpus")
    ax.legend()
    fig.tight_layout()
    lat_path = output_dir / "latency_by_scenario.png"
    fig.savefig(lat_path, dpi=120)
    plt.close(fig)

    # Evolução agregada (média dos cenários RAG)
    fig, ax = plt.subplots(figsize=(7, 4))
    for scenario in scenarios:
        series = [
            summaries_per_version[i].get(scenario, {}).get("mean_f1", 0.0)
            for i in range(len(versions))
        ]
        ax.plot(versions, series, marker="o", label=scenario)
    ax.set_ylabel("F1 médio")
    ax.set_title("Evolução v1 → v2 → v3 (F1 por cenário)")
    ax.legend()
    fig.tight_layout()
    evo_path = output_dir / "evolution_f1_v1_v2_v3.png"
    fig.savefig(evo_path, dpi=120)
    plt.close(fig)

    # Tradeoff qualidade vs latência (rag_rerank)
    fig, ax = plt.subplots(figsize=(6, 5))
    for i, label in enumerate(versions):
        s = summaries_per_version[i].get("rag_rerank", {})
        ax.scatter(
            s.get("mean_latency_seconds", 0.0),
            s.get("mean_f1", 0.0),
            s=80,
            label=label,
        )
        ax.annotate(label, (s.get("mean_latency_seconds", 0.0), s.get("mean_f1", 0.0)))
    ax.set_xlabel("Latência média rag_rerank (s)")
    ax.set_ylabel("F1 médio rag_rerank")
    ax.set_title("Tradeoff qualidade vs latência (rag_rerank)")
    ax.legend()
    fig.tight_layout()
    trade_path = output_dir / "tradeoff_f1_latency_rerank.png"
    fig.savefig(trade_path, dpi=120)
    plt.close(fig)

    print("Gráficos salvos em:")
    for p in (f1_path, lat_path, evo_path, trade_path):
        print(f"  {p}")


if __name__ == "__main__":
    main()
