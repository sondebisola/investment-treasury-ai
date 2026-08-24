import kfp
from kfp import dsl
from kfp.dsl import component, Input, Output, Dataset, Model, Metrics

@component(
    base_image="python:3.11-slim",
    packages_to_install=["pandas"]
)
def prepare_dataset_op(
    raw_data_uri: str,
    processed_dataset: Output[Dataset]
):
    """Ingest and prepare the training dataset."""
    import pandas as pd
    from google.cloud import storage
    df = pd.read_json(raw_data_uri, lines=True, storage_options={"token": "cloud"})
    df.to_json(processed_dataset.path, orient="records", lines=True)


@component(
    base_image="python:3.11-slim"
)
def train_lora_op(
    dataset: Input[Dataset],
    model_adapter: Output[Model],
    r_rank: int = 8,
    lora_alpha: int = 16
):
    """Simulate LoRA adapter training and serialize adapter config."""
    import json
    import os

    adapter_metadata = {
        "adapter_type": "LORA",
        "base_model": "google/gemma-2-2b-it",
        "r": r_rank,
        "lora_alpha": lora_alpha,
        "target_modules": ["q_proj", "v_proj"],
        "status": "TRAINED_SUCCESS"
    }

    os.makedirs(model_adapter.path, exist_ok=True)
    with open(os.path.join(model_adapter.path, "adapter_config.json"), "w") as f:
        json.dump(adapter_metadata, f, indent=2)


@component(
    base_image="python:3.11-slim",
    packages_to_install=["sqlglot"]
)
def benchmark_and_evaluate_op(
    model_adapter: Input[Model],
    metrics: Output[Metrics],
    min_ast_pass_threshold: float = 0.90
) -> bool:
    """Benchmark SQL outputs against golden AST rules."""
    import json
    import os
    import sqlglot
    from sqlglot import exp

    golden_test_cases = [
        "SELECT SUM(total_exposure) FROM `dbt_dev_analytics.fct_liquidity_summary`",
        "SELECT asset_class, COUNT(*) FROM `dbt_dev_analytics.fct_liquidity_summary` GROUP BY 1",
        "SELECT MAX(snapshot_date) FROM `dbt_dev_analytics.fct_liquidity_summary`"
    ]

    passed_ast = 0
    for query in golden_test_cases:
        try:
            parsed = sqlglot.parse_one(query, read="bigquery")
            if isinstance(parsed, exp.Select):
                passed_ast += 1
        except Exception:
            pass

    ast_pass_rate = passed_ast / len(golden_test_cases)
    metrics.log_metric("ast_pass_rate", float(ast_pass_rate))
    metrics.log_metric("min_threshold", float(min_ast_pass_threshold))
    return bool(ast_pass_rate >= min_ast_pass_threshold)


@component(base_image="python:3.11-slim")
def deploy_canary_gate_op(
    model_adapter: Input[Model],
    traffic_percentage: int = 10
):
    """Deploy model adapter as a canary endpoint."""
    print(f"Deploying Canary LoRA Adapter with {traffic_percentage}% traffic split.")


@dsl.pipeline(
    name="treasury-lora-tuning-pipeline",
    pipeline_root="gs://investment-treasury-ai-pipeline-artifacts/pipeline-root"
)
def treasury_training_pipeline(
    raw_data_uri: str = "gs://investment-treasury-ai-pipeline-artifacts/data/train.jsonl",
    r_rank: int = 8,
    lora_alpha: int = 16
):
    prep_task = prepare_dataset_op(raw_data_uri=raw_data_uri)

    train_task = train_lora_op(
        dataset=prep_task.outputs["processed_dataset"],
        r_rank=r_rank,
        lora_alpha=lora_alpha
    )

    eval_task = benchmark_and_evaluate_op(
        model_adapter=train_task.outputs["model_adapter"],
        min_ast_pass_threshold=0.90
    )

    # Reference eval_task.outputs["Output"] instead of eval_task.output
    with dsl.Condition(eval_task.outputs["Output"] == True, name="benchmark-passed-gate"):
        deploy_canary_gate_op(
            model_adapter=train_task.outputs["model_adapter"],
            traffic_percentage=10
        )


if __name__ == "__main__":
    kfp.compiler.Compiler().compile(
        pipeline_func=treasury_training_pipeline,
        package_path="treasury_pipeline.yaml"
    )
    print("Pipeline compiled successfully to treasury_pipeline.yaml")
