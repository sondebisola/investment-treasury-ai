import os
from google.cloud import aiplatform

PROJECT_ID = "investment-treasury-ai"
REGION = "us-central1"

def submit_pipeline():
    aiplatform.init(project=PROJECT_ID, location=REGION)
    
    job = aiplatform.PipelineJob(
        display_name="treasury-lora-tuning-run",
        template_path="treasury_pipeline.yaml",
        pipeline_root="gs://investment-treasury-ai-pipeline-artifacts/pipeline-root",
        parameter_values={
            "raw_data_uri": "gs://investment-treasury-ai-pipeline-artifacts/data/train.jsonl",
            "r_rank": 8,
            "lora_alpha": 16
        },
        enable_caching=True
    )
    
    job.submit()
    print("Pipeline job successfully submitted to Vertex AI Pipelines!")
    print(f"Check execution in the Google Cloud Console: Vertex AI > Pipelines")

if __name__ == "__main__":
    submit_pipeline()
