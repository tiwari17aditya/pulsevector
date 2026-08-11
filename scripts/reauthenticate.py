import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]

def main():
    token_file = 'credentials/token.json' if os.path.exists('credentials') else 'token.json'
    client_secrets_file = 'credentials/client_secrets.json' if os.path.exists('credentials/client_secrets.json') else 'client_secrets.json'
    
    if os.path.exists(token_file):
        print(f"Removing old {token_file}...")
        try:
            os.remove(token_file)
        except Exception as e:
            print(f"Warning: Could not remove {token_file}: {e}")
        
    print("Starting local server flow to authenticate...")
    try:
        flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
        creds = flow.run_local_server(port=0)
        
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
            
        print("[SUCCESS] Successfully created new token.json!")
        print("\n=================== NEW YOUTUBE_TOKEN_JSON ===================")
        print(creds.to_json())
        print("==============================================================")
        print("\nCopy the JSON string above (the line between the === bars) and update it in your GitHub Repository Secrets as YOUTUBE_TOKEN_JSON.")
    except Exception as e:
        print(f"[ERROR] Authentication flow failed: {e}")

if __name__ == '__main__':
    main()
