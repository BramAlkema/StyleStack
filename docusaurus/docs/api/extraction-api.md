# Design Token Extraction API

StyleStack provides a comprehensive API for extracting design tokens from existing Office templates. This RESTful API enables automated reverse engineering of legacy templates and integration with design systems.

## Base URL

```
https://api.stylestack.io/v1
```

## Authentication

All API requests require authentication using API keys:

```bash
# Include API key in request headers
curl -H "Authorization: Bearer sk_live_..." \
     -H "Content-Type: application/json" \
     https://api.stylestack.io/v1/extract
```

## Endpoints Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/extract` | POST | Extract design tokens from templates |
| `/extract/{job_id}` | GET | Check extraction job status |
| `/extract/{job_id}/download` | GET | Download extraction results |
| `/templates` | GET | List supported template formats |
| `/validate` | POST | Validate template before extraction |

## Extract Design Tokens

Extract comprehensive design tokens from Office templates.

### `POST /extract`

**Request Body**

```json
{
  "files": [
    {
      "name": "presentation.pptx",
      "content": "base64-encoded-file-content",
      "format": "pptx"
    }
  ],
  "options": {
    "output_format": "yaml",
    "extract_assets": true,
    "include_analytics": true,
    "accessibility_check": true,
    "merge_similar_tokens": true
  },
  "webhook_url": "https://your-app.com/webhooks/extraction-complete"
}
```

**cURL Example**

```bash
curl -X POST https://api.stylestack.io/v1/extract \
  -H "Authorization: Bearer sk_live_..." \
  -H "Content-Type: application/json" \
  -d '{
    "files": [
      {
        "name": "template.pptx",
        "content": "UEsDBBQAAAAI...",
        "format": "pptx"
      }
    ],
    "options": {
      "output_format": "yaml",
      "extract_assets": true
    }
  }'
```

**Response**

```json
{
  "job_id": "ext_1a2b3c4d5e6f",
  "status": "processing",
  "created_at": "2025-01-15T10:30:00Z",
  "estimated_completion": "2025-01-15T10:32:00Z",
  "files_count": 1,
  "total_size_mb": 2.4
}
```

## Check Extraction Status

Monitor the progress of extraction jobs.

### `GET /extract/{job_id}`

**Response - Processing**

```json
{
  "job_id": "ext_1a2b3c4d5e6f",
  "status": "processing",
  "progress": 65,
  "current_stage": "analyzing_typography",
  "stages": [
    {"name": "file_validation", "completed": true},
    {"name": "ooxml_parsing", "completed": true}, 
    {"name": "analyzing_colors", "completed": true},
    {"name": "analyzing_typography", "completed": false},
    {"name": "extracting_assets", "completed": false},
    {"name": "generating_tokens", "completed": false}
  ],
  "estimated_completion": "2025-01-15T10:32:00Z"
}
```

**Response - Completed**

```json
{
  "job_id": "ext_1a2b3c4d5e6f",
  "status": "completed",
  "progress": 100,
  "completed_at": "2025-01-15T10:31:45Z",
  "results": {
    "tokens_extracted": 47,
    "colors_found": 12,
    "fonts_analyzed": 3,
    "assets_extracted": 8,
    "accessibility_score": 94
  },
  "download_url": "/extract/ext_1a2b3c4d5e6f/download"
}
```

**Response - Failed**

```json
{
  "job_id": "ext_1a2b3c4d5e6f",
  "status": "failed",
  "error": {
    "code": "unsupported_format",
    "message": "Template format not supported",
    "details": "The uploaded file is not a valid OOXML document"
  },
  "failed_at": "2025-01-15T10:31:12Z"
}
```

## Download Extraction Results

Retrieve the extracted design tokens and assets.

### `GET /extract/{job_id}/download`

**Query Parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `format` | string | `yaml` | Output format: `yaml`, `json`, `css` |
| `include_assets` | boolean | `true` | Include extracted assets in response |
| `compress` | boolean | `false` | Return compressed archive |

**Response - YAML Format**

```yaml
# Downloaded as: tokens.yaml
stylestack:
  version: "1.0.0"
  extracted_at: "2025-01-15T10:31:45Z"
  source_files:
    - "presentation.pptx"
  
  tokens:
    colors:
      primary: "#2563eb"
      secondary: "#64748b"
      accent: "#f59e0b"
      text:
        primary: "#1f2937"
        secondary: "#6b7280"
      background:
        primary: "#ffffff"
        secondary: "#f8fafc"
    
    typography:
      font_families:
        sans: "Inter, -apple-system, sans-serif"
        serif: "Playfair Display, Georgia, serif"
        mono: "JetBrains Mono, Consolas, monospace"
      
      font_sizes:
        xs: "10pt"
        sm: "12pt"
        base: "14pt"
        lg: "16pt"
        xl: "20pt"
        "2xl": "24pt"
        "3xl": "30pt"
        "4xl": "36pt"
      
      line_heights:
        tight: 1.25
        normal: 1.5
        relaxed: 1.625
      
      letter_spacing:
        tight: "-0.025em"
        normal: "0em"
        wide: "0.025em"
    
    spacing:
      baseline_grid: "24px"
      margins:
        slide: "72pt"
        page: "1in"
      padding:
        content: "24pt"
        section: "48pt"
    
    shadows:
      sm: "0 1px 2px rgba(0,0,0,0.05)"
      md: "0 4px 6px rgba(0,0,0,0.1)"
      lg: "0 10px 15px rgba(0,0,0,0.1)"
    
    borders:
      width:
        thin: "1px"
        medium: "2px"  
        thick: "4px"
      radius:
        sm: "4px"
        md: "8px"
        lg: "16px"

  brand_assets:
    logos:
      - path: "assets/logo-primary.svg"
        usage: "primary"
        dimensions: "200x60px"
        colors: ["#2563eb", "#1f2937"]
      - path: "assets/logo-white.svg"
        usage: "reversed"
        dimensions: "200x60px"
        colors: ["#ffffff"]
    
    icons:
      - path: "assets/icons/"
        count: 12
        format: "svg"
        style: "outline"
    
    images:
      - path: "assets/hero-image.jpg"
        dimensions: "1920x1080px"
        usage: "hero_background"

  analytics:
    color_usage:
      "#2563eb": 23  # Primary blue used 23 times
      "#1f2937": 45  # Text color used 45 times
      "#f59e0b": 8   # Accent used 8 times
    
    font_usage:
      "Inter": 67        # Inter used in 67 elements
      "Playfair Display": 12  # Playfair used in 12 elements
    
    accessibility:
      overall_score: 94
      contrast_ratio:
        passed: 18
        failed: 2
      font_size:
        passed: 20
        failed: 0
      issues:
        - "Low contrast between #6b7280 and #f8fafc"
        - "Font size 9pt below minimum recommendation"
```

**Response - JSON Format**

```json
{
  "stylestack": {
    "version": "1.0.0",
    "tokens": {
      "colors": {
        "primary": "#2563eb",
        "secondary": "#64748b"
      },
      "typography": {
        "font_families": {
          "sans": "Inter, sans-serif"
        }
      }
    },
    "brand_assets": {
      "logos": [
        {
          "path": "assets/logo-primary.svg",
          "usage": "primary"
        }
      ]
    }
  }
}
```

## Validate Template

Check if a template is compatible with the extraction API.

### `POST /validate`

**Request Body**

```json
{
  "file": {
    "name": "template.pptx",
    "content": "base64-encoded-content",
    "format": "pptx"
  }
}
```

**Response - Valid**

```json
{
  "valid": true,
  "format": "pptx",
  "version": "Office 2019",
  "estimated_extraction_time": "2-3 minutes",
  "extractable_elements": {
    "colors": 15,
    "fonts": 4,
    "images": 6,
    "shapes": 28
  }
}
```

**Response - Invalid**

```json
{
  "valid": false,
  "error": {
    "code": "corrupted_file",
    "message": "Template file is corrupted or incomplete",
    "suggestions": [
      "Try re-saving the template from the original application",
      "Ensure the file was not corrupted during upload"
    ]
  }
}
```

## Supported Formats

List all template formats supported by the extraction API.

### `GET /templates`

**Response**

```json
{
  "supported_formats": [
    {
      "format": "pptx",
      "description": "Microsoft PowerPoint Template",
      "extensions": [".pptx", ".potx"],
      "max_file_size_mb": 100,
      "features": ["colors", "typography", "assets", "layouts"]
    },
    {
      "format": "docx", 
      "description": "Microsoft Word Document",
      "extensions": [".docx", ".dotx"],
      "max_file_size_mb": 50,
      "features": ["colors", "typography", "styles"]
    },
    {
      "format": "xlsx",
      "description": "Microsoft Excel Spreadsheet", 
      "extensions": [".xlsx", ".xltx"],
      "max_file_size_mb": 25,
      "features": ["colors", "typography", "charts"]
    },
    {
      "format": "odp",
      "description": "OpenDocument Presentation",
      "extensions": [".odp", ".otp"],
      "max_file_size_mb": 100,
      "features": ["colors", "typography", "assets"]
    }
  ]
}
```

## Webhooks

Configure webhooks to receive notifications when extraction jobs complete.

### Webhook Payload

When an extraction job completes, StyleStack sends a POST request to your webhook URL:

```json
{
  "event": "extraction.completed",
  "job_id": "ext_1a2b3c4d5e6f",
  "status": "completed",
  "completed_at": "2025-01-15T10:31:45Z",
  "results": {
    "tokens_extracted": 47,
    "accessibility_score": 94
  },
  "download_url": "https://api.stylestack.io/v1/extract/ext_1a2b3c4d5e6f/download"
}
```

### Webhook Security

Verify webhook authenticity using HMAC signatures:

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(), 
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
```

## Rate Limits

| Plan | Requests/Hour | Concurrent Jobs | Max File Size |
|------|---------------|-----------------|---------------|
| Free | 10 | 1 | 10MB |
| Pro | 100 | 5 | 100MB |
| Enterprise | 1000 | 20 | 500MB |

## Error Codes

| Code | Description |
|------|-------------|
| `invalid_format` | Unsupported file format |
| `file_too_large` | File exceeds size limit |
| `corrupted_file` | File is corrupted or incomplete |
| `rate_limit_exceeded` | Too many requests |
| `insufficient_credits` | Account has insufficient credits |
| `extraction_failed` | Extraction process failed |
| `webhook_failed` | Webhook delivery failed |

## SDKs and Libraries

### Python

```python
pip install stylestack-api

from stylestack import ExtractionClient

client = ExtractionClient(api_key="sk_live_...")

# Extract tokens from local file
job = client.extract_file("template.pptx")
result = client.wait_for_completion(job.id)
tokens = result.download_yaml()
```

### Node.js

```javascript
npm install stylestack-api

const { ExtractionClient } = require('stylestack-api');

const client = new ExtractionClient('sk_live_...');

// Extract with async/await
const job = await client.extractFile('template.pptx');
const result = await client.waitForCompletion(job.id);
const tokens = await result.downloadJSON();
```

### cURL Examples

```bash
# Start extraction
JOB_ID=$(curl -s -X POST https://api.stylestack.io/v1/extract \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d @request.json | jq -r '.job_id')

# Wait for completion (polling)
while true; do
  STATUS=$(curl -s https://api.stylestack.io/v1/extract/$JOB_ID \
    -H "Authorization: Bearer $API_KEY" | jq -r '.status')
  
  if [ "$STATUS" = "completed" ]; then
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "Extraction failed"
    exit 1
  fi
  
  sleep 5
done

# Download results
curl https://api.stylestack.io/v1/extract/$JOB_ID/download \
  -H "Authorization: Bearer $API_KEY" \
  -o extracted-tokens.yaml
```

## Best Practices

### File Preparation
1. **Clean Templates**: Remove unused elements and styles
2. **Consistent Naming**: Use descriptive names for colors and styles
3. **Modern Formats**: Use recent Office file formats
4. **Size Optimization**: Compress images and remove unused assets

### API Usage
1. **Batch Processing**: Extract multiple files in single requests
2. **Webhook Integration**: Use webhooks instead of polling for long jobs
3. **Error Handling**: Implement proper retry logic with exponential backoff
4. **Caching**: Cache results to avoid re-extracting unchanged templates

### Token Management
1. **Version Control**: Track extracted tokens in git repositories
2. **Validation**: Always validate tokens before using in production
3. **Documentation**: Document the source and purpose of each token set
4. **Testing**: Test generated templates with extracted tokens

The Extraction API enables automated design system migration, allowing you to modernize legacy Office templates and maintain design consistency across your organization.