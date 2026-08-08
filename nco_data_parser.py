from google.api_core.client_options import ClientOptions
from google.cloud import documentai
import time
from typing import Optional
import os

# --- ALL YOUR VARIABLES ---
project_id = os.getenv('PROJECT_ID')
processor_id = os.getenv('PROCESSOR_ID')

PROJECT_ID = project_id
LOCATION = "us"
PROCESSOR_ID = processor_id
MIME_TYPE = "application/pdf"

BUCKET_NAME = "nco_2015_data_chunks"
GCS_INPUT_URI = f"gs://{BUCKET_NAME}/nco - 2015_data_pdf_1-1152_complete.pdf"
GCS_OUTPUT_URI = f"gs://{BUCKET_NAME}/output_documentai_complete_1 - 1152/" # Folder for the results


def batch_process_document(
    project_id: str,
    location: str,
    processor_id: str,
    gcs_input_uri: str,
    gcs_output_uri: str,
    mime_type: str,
    processor_version_id: Optional[str] = "default"
):
    opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
    client = documentai.DocumentProcessorServiceClient(client_options=opts)

    name = client.processor_version_path(
        project_id, location, processor_id, processor_version=processor_version_id
    )

    print(f"Submitting job for processor: {name}")

    input_document = documentai.GcsDocument(
        gcs_uri=gcs_input_uri, mime_type=mime_type
    )
    input_config = documentai.BatchDocumentsInputConfig(
        gcs_documents=documentai.GcsDocuments(documents=[input_document])
    )

    output_config = documentai.DocumentOutputConfig(
        gcs_output_config=documentai.DocumentOutputConfig.GcsOutputConfig(
            gcs_uri=gcs_output_uri
        )
    )

    request = documentai.BatchProcessRequest(
        name=name,
        input_documents=input_config,
        document_output_config=output_config,
    )

    print("Starting batch processing operation...")
    operation = client.batch_process_documents(request)

    print(f"Waiting for operation {operation.operation.name} to complete...")
    
    try:
        response = operation.result(timeout=3600) # 1 hour timeout
        print("--------------------------------------------------")
        print("✅ Batch processing complete.")
        print(f"Output files are in: {gcs_output_uri}")
        print("--------------------------------------------------")
    except Exception as e:
        print(f"Error during processing: {e}")
        print(f"Operation metadata: {operation.metadata}")

if __name__ == '__main__':
    batch_process_document(
        project_id=PROJECT_ID,
        location=LOCATION,
        processor_id=PROCESSOR_ID,
        gcs_input_uri=GCS_INPUT_URI,
        gcs_output_uri=GCS_OUTPUT_URI,
        processor_version_id="pretrained-ocr-v2.1-2024-08-07",
        mime_type=MIME_TYPE
    )