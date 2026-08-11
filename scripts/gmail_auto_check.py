import sqlite3, os, sys, base64, time
from email.mime.text import MIMEText

DB = "../data/leadservice.db"

def get_gmail_service():
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        
        SCOPES = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send'
        ]
        
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists('credentials.json'):
                    print("ERROR: credentials.json not found!")
                    print("Follow setup instructions in setup_gmail.sh")
                    sys.exit(1)
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=8080)
            with open('token.json', 'w') as f:
                f.write(creds.to_json())
        
        return build('gmail', 'v1', credentials=creds)
    except ImportError as e:
        print("ERROR: Missing Gmail libraries")
        print("Run: pip install google-auth google-auth-oauthlib google-api-python-client")
        sys.exit(1)

def check_emails(service, max_results=5):
    try:
        results = service.users().messages().list(
            userId='me', 
            labelIds=['INBOX'], 
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        emails = []
        
        for msg in messages:
            msg_data = service.users().messages().get(
                userId='me', 
                id=msg['id'], 
                format='full'
            ).execute()
            
            headers = msg_data['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            
            body = ''
            if 'parts' in msg_data['payload']:
                for part in msg_data['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body']['data']
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
                        break
            
            emails.append({
                'id': msg['id'],
                'subject': subject,
                'sender': sender,
                'body': body,
                'thread_id': msg_data.get('threadId')
            })
        
        return emails
    except Exception as e:
        print(f"Error checking emails: {e}")
        return []

def send_reply(service, to, subject, body, thread_id=None):
    try:
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        if thread_id:
            message['threadId'] = thread_id
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        if thread_id:
            service.users().messages().send(
                userId='me', 
                body={'raw': raw, 'threadId': thread_id}
            ).execute()
        else:
            service.users().messages().send(
                userId='me', 
                body={'raw': raw}
            ).execute()
        
        print("Reply sent!")
        return True
    except Exception as e:
        print(f"Error sending reply: {e}")
        return False

def find_lead_by_email(email):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, protocol FROM leads WHERE contact_email LIKE ?", ('%' + email + '%',))
    row = c.fetchone()
    conn.close()
    return row

def process_emails(service, processed_ids_file='processed_emails.txt'):
    processed = set()
    if os.path.exists(processed_ids_file):
        with open(processed_ids_file, 'r') as f:
            processed = set(f.read().strip().split('
'))
    
    emails = check_emails(service, max_results=10)
    new_count = 0
    
    for email in emails:
        if email['id'] in processed:
            continue
        
        new_count += 1
        print(f"
{'='*60}")
        print(f"New email from: {email['sender']}")
        print(f"Subject: {email['subject']}")
        print(f"Body preview: {email['body'][:100]}...")
        
        lead = find_lead_by_email(email['sender'])
        
        if lead:
            lead_id, protocol = lead
            print(f"Matched lead: {protocol} (ID: {lead_id})")
            
            import requests
            response = requests.post('http://localhost:8001/replies/auto-reply', data={
                'lead_id': lead_id,
                'incoming_subject': email['subject'],
                'incoming_body': email['body']
            })
            
            result = response.json()
            print(f"AI Category: {result['category']}")
            print(f"AI Reply:
{result['reply']}")
            
            send = input("
Send this reply? (y/n): ").strip().lower()
            if send == 'y':
                send_reply(service, email['sender'], 'Re: ' + email['subject'], result['reply'], email['thread_id'])
                
                processed.add(email['id'])
                with open(processed_ids_file, 'w') as f:
                    f.write('
'.join(processed))
        else:
            print("No matching lead found")
            processed.add(email['id'])
            with open(processed_ids_file, 'w') as f:
                f.write('
'.join(processed))
    
    print(f"
{'='*60}")
    print(f"Processed {new_count} new emails")
    return new_count

if __name__ == "__main__":
    print("Gmail Auto-Checker")
    print("=" * 60)
    
    service = get_gmail_service()
    print("Gmail connected!")
    
    while True:
        try:
            count = process_emails(service)
            
            if count == 0:
                print("No new emails. Checking again in 60 seconds...")
            
            time.sleep(60)
        except KeyboardInterrupt:
            print("
Stopping...")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)
