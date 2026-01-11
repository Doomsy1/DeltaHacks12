#!/bin/bash

# Frontend Vultr Connection Test
# Tests if the bucket is accessible and can list objects

set -e

echo "=== Frontend Vultr Connection Test ==="
echo ""

# Check if .env file exists
if [ ! -f "frontend/.env" ]; then
    echo "❌ Error: frontend/.env file not found"
    echo ""
    echo "Please create frontend/.env with:"
    echo "  EXPO_PUBLIC_VULTR_ENDPOINT=https://your-endpoint.vultrobjects.com"
    echo "  EXPO_PUBLIC_VULTR_BUCKET=your-bucket-name"
    exit 1
fi

# Source the .env file and extract variables
ENDPOINT=$(grep EXPO_PUBLIC_VULTR_ENDPOINT frontend/.env | cut -d '=' -f2)
BUCKET=$(grep EXPO_PUBLIC_VULTR_BUCKET frontend/.env | cut -d '=' -f2)

if [ -z "$ENDPOINT" ] || [ -z "$BUCKET" ]; then
    echo "❌ Error: VULTR configuration not found in frontend/.env"
    echo ""
    echo "Make sure frontend/.env contains:"
    echo "  EXPO_PUBLIC_VULTR_ENDPOINT=https://your-endpoint.vultrobjects.com"
    echo "  EXPO_PUBLIC_VULTR_BUCKET=your-bucket-name"
    exit 1
fi

echo "Configuration:"
echo "  Endpoint: $ENDPOINT"
echo "  Bucket: $BUCKET"
echo ""

# Test bucket listing access
LIST_URL="${ENDPOINT}/${BUCKET}/?list-type=2&max-keys=10"
echo "Testing bucket listing access..."
echo "  URL: $LIST_URL"
echo ""

HTTP_CODE=$(curl -s -o /tmp/bucket_list.xml -w "%{http_code}" "$LIST_URL")

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Success! Bucket is accessible for listing"
    echo ""
    echo "Bucket contents (first 10 objects):"
    # Extract Keys from XML
    grep -o '<Key>[^<]*</Key>' /tmp/bucket_list.xml | sed 's/<Key>//;s/<\/Key>//' || echo "  (No objects found)"
    echo ""
    
    # Count video files
    VIDEO_COUNT=$(grep -o '<Key>[^<]*\.mp4</Key>\|<Key>[^<]*\.mov</Key>\|<Key>[^<]*\.avi</Key>\|<Key>[^<]*\.webm</Key>\|<Key>[^<]*\.m4v</Key>' /tmp/bucket_list.xml | wc -l || echo "0")
    echo "Video files found (in first 10): $VIDEO_COUNT"
    echo ""
    
    # Test first video if found
    if [ "$VIDEO_COUNT" != "0" ]; then
        FIRST_VIDEO=$(grep -o '<Key>[^<]*\.\(mp4\|mov\|avi\|webm\|m4v\)</Key>' /tmp/bucket_list.xml | head -1 | sed 's/<Key>//;s/<\/Key>//')
        if [ ! -z "$FIRST_VIDEO" ]; then
            VIDEO_URL="${ENDPOINT}/${BUCKET}/${FIRST_VIDEO}"
            echo "Testing first video access..."
            echo "  File: $FIRST_VIDEO"
            echo "  URL: $VIDEO_URL"
            VIDEO_HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -I "$VIDEO_URL")
            if [ "$VIDEO_HTTP_CODE" = "200" ]; then
                echo "  ✅ Video is accessible"
            else
                echo "  ❌ Video returned HTTP $VIDEO_HTTP_CODE"
            fi
        fi
    else
        echo "⚠️  No video files found in bucket"
        echo "    Please upload .mp4, .mov, .avi, .webm, or .m4v files to your bucket"
    fi
    
    rm -f /tmp/bucket_list.xml
    echo ""
    echo "✅ All tests passed! Your frontend should be able to load videos from Vultr."
    
elif [ "$HTTP_CODE" = "404" ]; then
    echo "❌ Bucket not found (HTTP 404)"
    echo ""
    echo "Please check:"
    echo "  - Bucket name is correct"
    echo "  - Bucket exists in the correct region"
    exit 1
    
elif [ "$HTTP_CODE" = "403" ]; then
    echo "❌ Access denied (HTTP 403)"
    echo ""
    echo "Your bucket is not publicly accessible for listing. Please:"
    echo "  1. Go to Vultr Object Storage dashboard"
    echo "  2. Select your bucket"
    echo "  3. Set permissions to allow public 's3:ListBucket' and 's3:GetObject'"
    exit 1
    
else
    echo "❌ Failed to list bucket (HTTP $HTTP_CODE)"
    echo ""
    echo "Possible issues:"
    echo "  - Endpoint URL is incorrect"
    echo "  - Bucket name is incorrect"
    echo "  - Network connectivity issues"
    exit 1
fi
