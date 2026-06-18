# test_supabase_connection.py
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")

print(f"URL: {url}")
print(f"Key starts with: {key[:10]}...")

try:
    supabase = create_client(url, key)
    
    # Try to count documents
    result = supabase.table("documents").select("*", count="exact").execute()
    print(f"✅ Connection successful!")
    print(f"Documents count: {result.count}")
    
except Exception as e:
    print(f"❌ Error: {e}")