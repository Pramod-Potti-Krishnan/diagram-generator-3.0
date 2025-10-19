#!/usr/bin/env python
"""Test diagram-charts bucket configuration."""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
BUCKET_NAME = 'diagram-charts'

print("Testing diagram-charts bucket...")
print()

# Create client with anon key (same as app will use)
client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Test upload
test_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><circle cx="50" cy="50" r="40" fill="#3B82F6"/></svg>'
test_filename = f"test_{os.urandom(4).hex()}.svg"

try:
    print(f"1. Uploading test file: {test_filename}")
    response = client.storage.from_(BUCKET_NAME).upload(
        test_filename,
        test_svg.encode('utf-8'),
        {'content-type': 'image/svg+xml'}
    )
    print(f"   ✅ Upload successful")

    print(f"2. Getting public URL...")
    url = client.storage.from_(BUCKET_NAME).get_public_url(test_filename)
    print(f"   ✅ Public URL: {url}")

    print(f"3. Downloading file...")
    downloaded = client.storage.from_(BUCKET_NAME).download(test_filename)
    print(f"   ✅ Download successful ({len(downloaded)} bytes)")

    print(f"4. Deleting test file...")
    client.storage.from_(BUCKET_NAME).remove([test_filename])
    print(f"   ✅ Delete successful")

    print()
    print("=" * 70)
    print("✅ ALL TESTS PASSED! Bucket is configured correctly!")
    print("=" * 70)
    print()
    print("You can now restart your diagram server and it will work!")

except Exception as e:
    print(f"   ❌ Failed: {e}")
    print()
    print("Make sure you've created the RLS policies in Supabase Dashboard:")
    print(f"https://app.supabase.com/project/{SUPABASE_URL.split('//')[1].split('.')[0]}/storage/policies")
    exit(1)
