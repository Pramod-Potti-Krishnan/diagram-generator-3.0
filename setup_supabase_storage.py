#!/usr/bin/env python
"""
Setup Supabase Storage for Diagram Generator v3

This script creates the necessary storage bucket and configures RLS policies.
"""

import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
BUCKET_NAME = os.getenv('SUPABASE_BUCKET', 'diagram-charts')

print("=" * 70)
print("  Supabase Storage Setup for Diagram Generator v3")
print("=" * 70)
print()

# Create client
print(f"Connecting to Supabase...")
print(f"  URL: {SUPABASE_URL}")
print(f"  Bucket: {BUCKET_NAME}")
print()

try:
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    print("✅ Connected to Supabase")
except Exception as e:
    print(f"❌ Failed to connect: {e}")
    exit(1)

# Check if bucket exists
print()
print(f"Checking if bucket '{BUCKET_NAME}' exists...")

try:
    buckets = client.storage.list_buckets()
    bucket_names = [b.name for b in buckets] if buckets else []
    print(f"  Found {len(bucket_names)} buckets: {bucket_names}")

    if BUCKET_NAME in bucket_names:
        print(f"✅ Bucket '{BUCKET_NAME}' already exists")
    else:
        print(f"⚠️  Bucket '{BUCKET_NAME}' does not exist")
        print(f"  Creating public bucket '{BUCKET_NAME}'...")

        # Create the bucket as public
        response = client.storage.create_bucket(
            BUCKET_NAME,
            options={"public": True}
        )
        print(f"✅ Created bucket '{BUCKET_NAME}' (public)")

except Exception as e:
    print(f"❌ Error managing bucket: {e}")
    print()
    print("Note: You may need to create the bucket manually in Supabase Dashboard:")
    print(f"  1. Go to https://app.supabase.com/project/{SUPABASE_URL.split('//')[1].split('.')[0]}/storage/buckets")
    print(f"  2. Click 'New bucket'")
    print(f"  3. Name: {BUCKET_NAME}")
    print(f"  4. Make it Public: Yes")
    print(f"  5. File size limit: 5 MB")
    print(f"  6. Allowed MIME types: image/svg+xml, image/png")
    print()

# Test upload
print()
print("Testing upload to bucket...")

test_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><circle cx="50" cy="50" r="40" fill="blue"/></svg>'
test_filename = f"test_diagram_{os.urandom(4).hex()}.svg"

try:
    # Upload test file
    response = client.storage.from_(BUCKET_NAME).upload(
        test_filename,
        test_svg.encode('utf-8'),
        {"content-type": "image/svg+xml"}
    )

    print(f"✅ Successfully uploaded test file: {test_filename}")

    # Get public URL
    url = client.storage.from_(BUCKET_NAME).get_public_url(test_filename)
    print(f"✅ Public URL: {url}")

    # Clean up test file
    client.storage.from_(BUCKET_NAME).remove([test_filename])
    print(f"✅ Cleaned up test file")

    print()
    print("=" * 70)
    print("✅ SUPABASE STORAGE CONFIGURED SUCCESSFULLY!")
    print("=" * 70)
    print()
    print(f"Your diagram service can now upload to: {BUCKET_NAME}")
    print(f"Public URL pattern: {SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/...")

except Exception as e:
    print(f"❌ Upload test failed: {e}")
    print()
    print("This usually means RLS (Row Level Security) policies are blocking uploads.")
    print()
    print("To fix this, you need to configure RLS policies in Supabase:")
    print()
    print("Option 1 - Disable RLS (Simple, less secure):")
    print(f"  1. Go to https://app.supabase.com/project/{SUPABASE_URL.split('//')[1].split('.')[0]}/storage/buckets/{BUCKET_NAME}")
    print(f"  2. Click on '{BUCKET_NAME}' bucket")
    print(f"  3. Go to 'Policies' tab")
    print(f"  4. Click 'New policy'")
    print(f"  5. Choose 'For full customization'")
    print(f"  6. Name: 'Allow public uploads'")
    print(f"  7. Policy Definition: true")
    print(f"  8. Save")
    print()
    print("Option 2 - Enable RLS with proper policies (Recommended):")
    print(f"  Run this SQL in Supabase SQL Editor:")
    print()
    print(f"-- Allow anyone to upload files")
    print(f"CREATE POLICY \"Allow public uploads\"")
    print(f"ON storage.objects FOR INSERT")
    print(f"WITH CHECK (bucket_id = '{BUCKET_NAME}');")
    print()
    print(f"-- Allow anyone to read files")
    print(f"CREATE POLICY \"Allow public reads\"")
    print(f"ON storage.objects FOR SELECT")
    print(f"USING (bucket_id = '{BUCKET_NAME}');")
    print()

print()
print("=" * 70)
