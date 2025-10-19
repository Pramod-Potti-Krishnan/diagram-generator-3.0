# Railway Deployment Guide - Diagram Generator v3.0

Complete guide for deploying the Diagram Generator v3.0 REST API to Railway.

---

## 📋 Prerequisites

Before deploying to Railway, ensure you have:

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **Supabase Project**:
   - Create a project at [supabase.com](https://supabase.com)
   - Set up the `diagram-charts` storage bucket (see Supabase Setup below)
3. **Google Gemini API Key**:
   - Get one from [Google AI Studio](https://makersuite.google.com/app/apikey)

---

## 🚀 Quick Deploy to Railway

### Step 1: Create New Railway Project

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click **"New Project"**
3. Choose **"Deploy from GitHub repo"** or **"Empty Project"**

### Step 2: Connect Your Repository

#### Option A: Deploy from GitHub
1. Select your repository containing this code
2. Railway will automatically detect `railway.toml` and `requirements.txt`
3. The build will start automatically

#### Option B: Deploy using Railway CLI
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Link to this directory
cd /path/to/diagram_generator/v3.0

# Deploy
railway up
```

### Step 3: Configure Environment Variables

Go to your Railway project → **Variables** tab and add these **required** variables:

```bash
# Supabase Configuration (REQUIRED)
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_BUCKET=diagram-charts

# Google Gemini API (REQUIRED)
GOOGLE_API_KEY=your-google-api-key

# Environment (REQUIRED)
ENV=production
```

**Optional but recommended variables:**

```bash
# Performance
REQUEST_TIMEOUT=30
MAX_WORKERS=4

# Logging
LOG_LEVEL=INFO

# Features
ENABLE_CACHE=True
ENABLE_FALLBACK=True
```

**⚠️ Important**: Railway automatically sets the `PORT` variable - **DO NOT** set it manually!

### Step 4: Deploy

1. Railway will automatically deploy when you push to your connected branch
2. Or click **"Deploy"** in the Railway dashboard
3. Monitor deployment logs in the **"Deployments"** tab

---

## 🗄️ Supabase Setup

Before the service can upload diagrams, you need to configure Supabase storage:

### Create Storage Bucket

1. Go to your Supabase project dashboard
2. Navigate to **Storage** → **Buckets**
3. Click **"Create a new bucket"**
4. Configure:
   - **Name**: `diagram-charts`
   - **Public bucket**: ✅ Yes
   - **File size limit**: `5 MB`
   - **Allowed MIME types**: `image/svg+xml, image/png, image/jpeg`
5. Click **"Create bucket"**

### Configure RLS Policies

After creating the bucket, set up Row Level Security policies:

1. Go to **Storage** → **Policies**
2. Select the `diagram-charts` bucket
3. Create these 4 policies:

#### Policy 1: Allow Public Reads
- **Policy name**: `Allow public reads`
- **Target roles**: `public`
- **Policy definition (USING)**:
  ```sql
  bucket_id = 'diagram-charts'
  ```
- **Allowed operations**: `SELECT`

#### Policy 2: Allow Public Uploads
- **Policy name**: `Allow public uploads`
- **Target roles**: `public`
- **Policy definition (WITH CHECK)**:
  ```sql
  bucket_id = 'diagram-charts'
  ```
- **Allowed operations**: `INSERT`

#### Policy 3: Allow Public Updates
- **Policy name**: `Allow public updates`
- **Target roles**: `public`
- **Policy definition (USING)**:
  ```sql
  bucket_id = 'diagram-charts'
  ```
- **Allowed operations**: `UPDATE`

#### Policy 4: Allow Public Deletes
- **Policy name**: `Allow public deletes`
- **Target roles**: `public`
- **Policy definition (USING)**:
  ```sql
  bucket_id = 'diagram-charts'
  ```
- **Allowed operations**: `DELETE`

### Verify Supabase Setup

Run this test locally (before deploying to Railway):

```bash
python test_bucket.py
```

You should see:
```
✅ Upload successful
✅ Public URL: https://...
✅ Download successful
✅ Delete successful
✅ ALL TESTS PASSED!
```

---

## 🔍 Verify Deployment

Once deployed, Railway will provide you with a public URL (e.g., `https://your-service.up.railway.app`).

### Health Check

Visit your deployment URL + `/health`:

```
https://your-service.up.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "diagram_generator_v3",
  "conductor": "ready",
  "jobs": {
    "total_jobs": 0,
    "queued": 0,
    "processing": 0,
    "completed": 0,
    "failed": 0
  }
}
```

### Service Info

Check available diagram types:

```
https://your-service.up.railway.app/
```

You should see 21 SVG templates, 7 Mermaid types, and 6 Python chart types.

---

## 📡 API Usage

### Generate a Diagram

**Endpoint**: `POST /generate`

```bash
curl -X POST https://your-service.up.railway.app/generate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Step 1: Plan\nStep 2: Execute\nStep 3: Review",
    "diagram_type": "cycle_3_step",
    "theme": {
      "primaryColor": "#3B82F6",
      "style": "professional"
    }
  }'
```

**Response**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing"
}
```

### Check Job Status

**Endpoint**: `GET /status/{job_id}`

```bash
curl https://your-service.up.railway.app/status/550e8400-e29b-41d4-a716-446655440000
```

**Response when completed**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "stage": "completed",
  "result": {
    "diagram_url": "https://your-project.supabase.co/storage/v1/object/public/diagram-charts/...",
    "diagram_type": "cycle_3_step",
    "generation_method": "svg_template"
  }
}
```

---

## 🐛 Troubleshooting

### Deployment Fails

**Check build logs:**
1. Go to Railway dashboard → **Deployments** → Select failed deployment
2. Check **Build Logs** and **Deploy Logs** tabs
3. Common issues:
   - Missing environment variables
   - Invalid `requirements.txt` syntax
   - Python version mismatch

**Solution**: Ensure all required environment variables are set and `requirements.txt` is valid.

### Health Check Returns 503

**Cause**: Service is starting up or crashed.

**Solution**:
1. Check **Deploy Logs** for errors
2. Verify all environment variables are set correctly
3. Check if Supabase URL and API keys are valid
4. Ensure Google API key is valid

### Diagram Generation Returns 404

**Cause**: Supabase bucket or RLS policies not configured.

**Solution**:
1. Verify `diagram-charts` bucket exists in Supabase
2. Check all 4 RLS policies are created (see Supabase Setup)
3. Test bucket access using `test_bucket.py` locally

### Diagrams Not Uploading

**Check Deploy Logs for errors like**:
```
ERROR: Failed to upload diagram: 403 Forbidden
```

**Solution**:
1. Verify RLS policies are created correctly
2. Check bucket is set to **public**
3. Verify `SUPABASE_ANON_KEY` is correct

### Port Already in Use (Local Testing)

**Error**: `Address already in use: 8080`

**Solution**:
```bash
# Kill processes on port 8080
lsof -ti :8080 | xargs kill -9

# Or use different port locally
PORT=8081 python main.py
```

---

## 🔒 Production Best Practices

### Security

1. **API Key Protection** (Optional):
   - Add `API_KEY` environment variable in Railway
   - Implement API key validation in `rest_server.py`

2. **CORS Configuration**:
   - Update `CORS_ORIGINS` to restrict allowed origins
   - Example: `CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com`

3. **Supabase Service Key** (Optional):
   - For admin operations, add `SUPABASE_SERVICE_KEY` to Railway
   - Keep it secret - never expose in client-side code

### Monitoring

1. **Railway Metrics**:
   - Monitor CPU, memory, and network usage in Railway dashboard
   - Set up alerts for high resource usage

2. **Logging** (Optional):
   - Add `LOGFIRE_TOKEN` for advanced monitoring
   - Set `LOG_LEVEL=DEBUG` for detailed logs (temporary, for debugging)

3. **Health Checks**:
   - Railway automatically monitors `/health` endpoint
   - Service restarts on failed health checks

### Performance

1. **Scaling**:
   - Railway auto-scales based on traffic
   - Increase `MAX_WORKERS` for higher concurrency

2. **Caching**:
   - Keep `ENABLE_CACHE=True` for better performance
   - Adjust `CACHE_TTL` based on your needs

3. **Timeouts**:
   - Increase `REQUEST_TIMEOUT` for complex diagrams
   - Default 30 seconds usually sufficient

---

## 📊 Monitoring Your Deployment

### Railway Dashboard

Monitor your deployment at: `https://railway.app/project/{your-project-id}`

Key metrics to watch:
- **CPU Usage**: Should stay below 80%
- **Memory**: Should stay below 512MB for this service
- **Network**: Inbound/outbound traffic
- **Response Time**: /health endpoint latency

### Logs

View live logs:
```bash
# Using Railway CLI
railway logs
```

Or view in Railway dashboard → **Deployments** → **Deploy Logs**

---

## 🔄 Updates and Redeployment

### Automatic Deployments

If connected to GitHub:
1. Push changes to your connected branch
2. Railway automatically detects changes and redeploys

### Manual Redeploy

Using Railway CLI:
```bash
railway up
```

Or in Railway dashboard:
1. Go to **Deployments**
2. Click **"Redeploy"** on the latest deployment

---

## 📞 Support

### Common Issues

| Issue | Solution |
|-------|----------|
| 503 Service Unavailable | Check Deploy Logs, verify environment variables |
| Diagram upload fails | Verify Supabase bucket and RLS policies |
| Slow response times | Increase `MAX_WORKERS` or check Railway metrics |
| Build fails | Check `requirements.txt` and Python version |

### Resources

- **Railway Docs**: https://docs.railway.app
- **Supabase Docs**: https://supabase.com/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **This Project**: See `README.md` for API documentation

---

## ✅ Deployment Checklist

Before going live, verify:

- [ ] Supabase project created
- [ ] `diagram-charts` bucket created and public
- [ ] All 4 RLS policies configured
- [ ] Google Gemini API key obtained
- [ ] All required environment variables set in Railway
- [ ] Health check returns 200 OK
- [ ] Service info endpoint lists all diagram types
- [ ] Test diagram generation works
- [ ] Diagram URL is publicly accessible
- [ ] Logs show no errors
- [ ] Performance metrics are healthy

---

**🎉 Deployment Complete!**

Your Diagram Generator v3.0 REST API is now live on Railway!

API Base URL: `https://your-service.up.railway.app`

Test it:
```bash
curl https://your-service.up.railway.app/health
```
