import os
from supabase import create_client, Client #buillds connection to supabase
from dotenv import load_dotenv
 
 #load env var mn .env file
load_dotenv()
 
 
 #get env var mn .env w buildi connection m3a supabase, w ila kayn chi env var manquants nthrowi error, w ila kolchi sahih nbuildi connection w nexporti supabase client li rah yest3mlou auth.py w contact.py w quizzes.py
SUPABASE_URL: str = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY: str = os.environ.get("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError("SUPABASE_URL et SUPABASE_ANON_KEY manquants dans .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
