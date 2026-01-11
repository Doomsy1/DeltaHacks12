# Frontend - Vultr Object Storage Setup

This guide explains how to configure the frontend to pull videos directly from Vultr Object Storage.

## Configuration

The frontend uses environment variables to connect to Vultr Object Storage. These variables are prefixed with `EXPO_PUBLIC_` so they can be accessed at runtime in the Expo app.

### Step 1: Create .env File

Create a `.env` file in the `frontend/` directory:

```bash
cd frontend
touch .env
```

### Step 2: Add Vultr Configuration

Add your Vultr Object Storage credentials to the `.env` file:

```bash
# Vultr Object Storage Configuration
EXPO_PUBLIC_VULTR_ENDPOINT=https://ewr1.vultrobjects.com
EXPO_PUBLIC_VULTR_BUCKET=your_bucket_name
```

**Replace with your actual values:**
- `EXPO_PUBLIC_VULTR_ENDPOINT`: Your Vultr Object Storage endpoint (e.g., `https://ewr1.vultrobjects.com`)
- `EXPO_PUBLIC_VULTR_BUCKET`: Your bucket name where videos are stored

### Step 3: Make Your Bucket Publicly Accessible

For the frontend to access videos directly, your Vultr bucket needs to be publicly readable:

1. Go to your Vultr Object Storage dashboard
2. Select your bucket
3. Go to **Settings** or **Permissions**
4. Set **Access Control** to **public-read** or create a bucket policy that allows:
   - Public GET requests on objects (`s3:GetObject`)
   - Public LIST requests on the bucket (`s3:ListBucket`)

**Example Bucket Policy (if supported):**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::your_bucket_name/*",
        "arn:aws:s3:::your_bucket_name"
      ]
    }
  ]
}
```

### Step 4: Restart Your Development Server

After creating the `.env` file, restart your Expo development server:

```bash
# Stop the current server (Ctrl+C)
# Then restart
npm start
```

## How It Works

1. The app reads `EXPO_PUBLIC_VULTR_ENDPOINT` and `EXPO_PUBLIC_VULTR_BUCKET` from environment variables
2. On load, it calls the S3 ListObjectsV2 API: `{ENDPOINT}/{BUCKET}/?list-type=2&max-keys=1000`
3. It parses the XML response to extract all video file keys (mp4, mov, avi, webm, m4v)
4. It constructs full video URLs from the keys: `{ENDPOINT}/{BUCKET}/{video_key}`
5. Videos are loaded into the FlatList and played

**No manifest.json needed!** The app automatically discovers all video files in your bucket.

## Troubleshooting

### "No videos available" error

**Possible causes:**
1. Missing or incorrect `.env` configuration
2. Bucket is not publicly accessible for listing
3. No video files in the bucket
4. Network connectivity issues

**Solutions:**
- Check your `.env` file has the correct values
- Verify bucket has public read AND list permissions
- Test access in browser: `https://{ENDPOINT}/{BUCKET}/?list-type=2`
- Check that you have .mp4, .mov, .avi, .webm, or .m4v files in your bucket
- Check bucket permissions

### Videos not playing

**Possible causes:**
1. Video files are not publicly accessible
2. Incorrect video URLs in manifest.json
3. CORS issues

**Solutions:**
- Ensure bucket has public-read access
- Verify video file names in manifest.json match actual files
- Check browser console for CORS errors
- Configure CORS on your Vultr bucket if needed

### Configuration not updating

**Solutions:**
- Restart the Expo development server completely
- Clear Metro bundler cache: `npm start -- --clear`
- On device/simulator, delete app and reinstall

## Security Considerations

### Current Implementation (Public Bucket)

The current implementation requires:
- ✅ Videos are publicly accessible (anyone with URL can view)
- ✅ No authentication required
- ❌ No usage tracking
- ❌ Videos can be downloaded directly

**Best for:**
- Public content
- Demo/prototype apps
- Non-sensitive videos

### Alternative: Private Bucket with Backend Proxy

For production apps with private content, consider:

1. Keep bucket private
2. Create backend endpoint that:
   - Lists videos for authenticated users
   - Generates presigned URLs with expiration
   - Tracks video access
3. Frontend fetches from backend instead of directly from Vultr

**Benefits:**
- ✅ Controlled access
- ✅ Usage tracking
- ✅ Temporary URLs that expire
- ✅ Authentication/authorization

## Environment Variables Reference

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `EXPO_PUBLIC_VULTR_ENDPOINT` | Vultr Object Storage endpoint URL | `https://ewr1.vultrobjects.com` | Yes |
| `EXPO_PUBLIC_VULTR_BUCKET` | Bucket name containing videos | `my-video-bucket` | Yes |

**Note:** The `EXPO_PUBLIC_` prefix is required for Expo to expose these variables to the client-side code.

## Video File Discovery

The app automatically discovers video files in your bucket by:
1. Listing all objects using the S3 ListObjectsV2 API
2. Filtering for common video extensions: `.mp4`, `.mov`, `.avi`, `.webm`, `.m4v`
3. Creating a playable video list

**Supported file formats:**
- MP4 (`.mp4`, `.m4v`) - Recommended
- MOV (`.mov`)
- AVI (`.avi`)
- WebM (`.webm`)

## Updating Videos

To add/remove videos:

1. Upload/delete video files in your Vultr bucket
2. Restart the app or pull to refresh
3. The app will automatically discover the new videos

No manifest file needed! The app scans your bucket automatically.
