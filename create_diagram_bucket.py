#!/usr/bin/env python
"""
Create diagram-charts bucket in Supabase with proper RLS policies.

This script uses the Supabase service key for administrative access.
"""

import os
from dotenv import load_dotenv
from supabase import create_client
import requests

# Load environment
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
BUCKET_NAME = 'diagram-charts'

print("=" * 70)
print("  Creating diagram-charts Bucket in Supabase")
print("=" * 70)
print()

# Use service key if available, otherwise try anon key
service_key = SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY

if not service_key:
    print("❌ No Supabase key found!")
    print("Please set either SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY")
    exit(1)

print(f"Connecting to Supabase...")
print(f"  URL: {SUPABASE_URL}")
print(f"  Using: {'Service Key' if SUPABASE_SERVICE_KEY else 'Anon Key'}")
print()

# Create client
client = create_client(SUPABASE_URL, service_key)

# Step 1: Create the bucket using REST API
print(f"Step 1: Creating bucket '{BUCKET_NAME}'...")

try:
    # Try to create bucket via REST API with proper headers
    headers = {
        'apikey': service_key,
        'Authorization': f'Bearer {service_key}',
        'Content-Type': 'application/json'
    }

    bucket_config = {
        'name': BUCKET_NAME,
        'public': True,
        'file_size_limit': 5242880,  # 5MB
        'allowed_mime_types': ['image/svg+xml', 'image/png', 'image/jpeg']
    }

    # First check if bucket exists
    response = requests.get(
        f'{SUPABASE_URL}/storage/v1/bucket',
        headers=headers
    )

    if response.status_code == 200:
        buckets = response.json()
        bucket_names = [b['name'] for b in buckets]

        if BUCKET_NAME in bucket_names:
            print(f"✅ Bucket '{BUCKET_NAME}' already exists")
        else:
            # Create the bucket
            response = requests.post(
                f'{SUPABASE_URL}/storage/v1/bucket',
                headers=headers,
                json=bucket_config
            )

            if response.status_code in [200, 201]:
                print(f"✅ Created bucket '{BUCKET_NAME}'")
            else:
                print(f"⚠️  Could not create bucket: {response.status_code}")
                print(f"    Response: {response.text}")
                print()
                print("    Continuing anyway - you may need to create it manually")

except Exception as e:
    print(f"⚠️  Error creating bucket: {e}")
    print("    Continuing to RLS policy setup...")

# Step 2: Configure RLS policies via SQL
print()
print(f"Step 2: Configuring RLS policies...")

sql_policies = f"""
-- Enable RLS on storage.objects if not already enabled
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (to avoid conflicts)
DROP POLICY IF EXISTS "Allow public uploads to diagram-charts" ON storage.objects;
DROP POLICY IF EXISTS "Allow public reads from diagram-charts" ON storage.objects;
DROP POLICY IF EXISTS "Allow public updates to diagram-charts" ON storage.objects;
DROP POLICY IF EXISTS "Allow public deletes from diagram-charts" ON storage.objects;

-- Create policy to allow anyone to upload files
CREATE POLICY "Allow public uploads to diagram-charts"
ON storage.objects
FOR INSERT
WITH CHECK (bucket_id = '{BUCKET_NAME}');

-- Create policy to allow anyone to read files
CREATE POLICY "Allow public reads from diagram-charts"
ON storage.objects
FOR SELECT
USING (bucket_id = '{BUCKET_NAME}');

-- Create policy to allow anyone to update files
CREATE POLICY "Allow public updates to diagram-charts"
ON storage.objects
FOR UPDATE
USING (bucket_id = '{BUCKET_NAME}');

-- Create policy to allow anyone to delete files
CREATE POLICY "Allow public deletes from diagram-charts"
ON storage.objects
FOR DELETE
USING (bucket_id = '{BUCKET_NAME}');
"""

try:
    # Execute SQL via REST API
    response = requests.post(
        f'{SUPABASE_URL}/rest/v1/rpc/exec_sql',
        headers={
            'apikey': service_key,
            'Authorization': f'Bearer {service_key}',
            'Content-Type': 'application/json'
        },
        json={'query': sql_policies}
    )

    if response.status_code == 200:
        print(f"✅ RLS policies configured")
    else:
        # Try alternative method - direct SQL execution
        print(f"⚠️  REST API method failed, trying alternative...")

        # Use Supabase client's postgrest to execute
        try:
            # Split into individual statements and execute
            statements = [s.strip() for s in sql_policies.split(';') if s.strip()]

            for stmt in statements:
                if stmt:
                    print(f"   Executing: {stmt[:50]}...")
                    # Note: This might not work with anon key
                    result = client.postgrest.rpc('exec_sql', {'query': stmt}).execute()

            print(f"✅ RLS policies configured via alternative method")
        except Exception as e2:
            print(f"⚠️  Could not set RLS policies programmatically: {e2}")
            print()
            print("You'll need to run this SQL manually in Supabase SQL Editor:")
            print("=" * 70)
            print(sql_policies)
            print("=" * 70)

except Exception as e:
    print(f"⚠️  Error setting RLS policies: {e}")
    print()
    print("Please run this SQL manually in Supabase SQL Editor:")
    print("=" * 70)
    print(sql_policies)
    print("=" * 70)

# Step 3: Test the configuration
print()
print(f"Step 3: Testing bucket configuration...")

test_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><circle cx="50" cy="50" r="40" fill="#3B82F6"/></svg>'
test_filename = f"test_{os.urandom(4).hex()}.svg"

try:
    # Upload test file
    response = client.storage.from_(BUCKET_NAME).upload(
        test_filename,
        test_svg.encode('utf-8'),
        {'content-type': 'image/svg+xml'}
    )

    print(f"✅ Successfully uploaded test file")

    # Get public URL
    url = client.storage.from_(BUCKET_NAME).get_public_url(test_filename)
    print(f"✅ Public URL: {url}")

    # Clean up
    client.storage.from_(BUCKET_NAME).remove([test_filename])
    print(f"✅ Cleaned up test file")

    print()
    print("=" * 70)
    print("✅ SUCCESS! Bucket is ready to use!")
    print("=" * 70)
    print()
    print(f"Bucket name: {BUCKET_NAME}")
    print(f"Public URL pattern: {SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/...")
    print()
    print("You can now restart your Diagram Generator v3 server!")

except Exception as e:
    print(f"❌ Test upload failed: {e}")
    print()
    print("=" * 70)
    print("Manual Configuration Required")
    print("=" * 70)
    print()
    print(f"1. Go to: https://app.supabase.com/project/{SUPABASE_URL.split('//')[1].split('.')[0]}/storage/buckets")
    print(f"2. Create bucket '{BUCKET_NAME}' (Public: Yes, Size: 5MB)")
    print()
    print(f"3. Go to: https://app.supabase.com/project/{SUPABASE_URL.split('//')[1].split('.')[0]}/sql")
    print(f"4. Run this SQL:")
    print()
    print(sql_policies)
    print()

print("=" * 70)
