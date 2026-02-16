import os
from google.cloud import storage

def upload_to_gcs(source_file_path, bucket_name, destination_blob_name):
    """
    Uploads a file to the bucket and makes it public.
    
    Args:
        source_file_path (str): Path to the file to upload.
        bucket_name (str): ID of the GCS bucket.
        destination_blob_name (str): Name of the file in GCS.
        
    Returns:
        str: Public URL of the uploaded file.
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_filename(source_file_path)

        # Make the blob public
        try:
            blob.make_public()
        except Exception as e:
            if "uniform bucket-level access" in str(e).lower():
                print(f"Warning: Could not make file {destination_blob_name} public due to Uniform Bucket-Level Access.")
                print("Ensure the bucket is configured to be public (add 'allUsers' as 'Storage Object Viewer').")
            else:
                print(f"Warning: Could not make file public: {e}")

        print(f"File {source_file_path} uploaded to {destination_blob_name}.")
        print(f"Public URL: {blob.public_url}")
        
        return blob.public_url

    except Exception as e:
        print(f"An error occurred during GCS upload: {e}")
        return None
