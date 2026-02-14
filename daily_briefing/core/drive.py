import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def authenticate_drive():
    """Authenticates the user with Google Drive and returns the service object."""
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                print("Error: credentials.json not found. Please download it from Google Cloud Console.")
                return None
                
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("drive", "v3", credentials=creds)

def upload_file(file_path, folder_id=None):
    """
    Uploads a file to Google Drive.
    
    Args:
        file_path (str): Path to the file to upload.
        folder_id (str, optional): ID of the folder to upload to. 
                                   Defaults to GOOGLE_DRIVE_FOLDER_ID env var if set.
    """
    service = authenticate_drive()
    if not service:
        return None

    if folder_id is None:
        folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

    file_metadata = {"name": os.path.basename(file_path)}
    
    if folder_id:
        file_metadata["parents"] = [folder_id]

    media = MediaFileUpload(file_path, resumable=True)
    
    try:
        file = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )
        print(f"File ID: {file.get('id')}")
        return file.get("id")
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
