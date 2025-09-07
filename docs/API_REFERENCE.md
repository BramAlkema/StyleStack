# API Reference - PPTX Processor v2

This document provides detailed API documentation for all functions and classes in PPTX Processor v2.

## Core Classes

### OOXMLJsonService

Main service for PPTX processing via Cloud Run.

#### Static Methods

##### `unwrap(fileIdOrBlob, options)`

Unwrap OOXML file into JSON manifest.

**Parameters:**
- `fileIdOrBlob` (string|Blob): Drive file ID, filename, or blob
- `options` (Object, optional): Configuration options
  - `useSession` (boolean): Use session for large files (default: false)

**Returns:** Promise<Object> - JSON manifest with entries array

**Example:**
```javascript
const manifest = await OOXMLJsonService.unwrap('presentation.pptx')
console.log(`Extracted ${manifest.entries.length} files`)
```

##### `rewrap(manifest, options)`

Rewrap JSON manifest back to OOXML file.

**Parameters:**
- `manifest` (Object): JSON manifest with entries
- `options` (Object, optional): Configuration options
  - `filename` (string): Output filename (default: 'output.pptx')
  - `saveToGCS` (boolean): Save result to GCS instead of Drive

**Returns:** Promise<string|Object> - Drive file ID or GCS result

**Example:**
```javascript
const fileId = await OOXMLJsonService.rewrap(manifest, {
  filename: 'enhanced.pptx'
})
```

##### `healthCheck()`

Check service health and availability.

**Returns:** Promise<Object> - Health status object

**Example:**
```javascript
const health = await OOXMLJsonService.healthCheck()
console.log('Service available:', health.available)
```

##### `getServiceInfo()`

Get service configuration and capabilities.

**Returns:** Object - Service information

### OOXMLDeployment

Handles Cloud Run deployment from Google Apps Script.

#### Static Methods

##### `showGcpPreflight()`

Show GCP preflight sidebar for setup verification.

**Example:**
```javascript
OOXMLDeployment.showGcpPreflight()
```

##### `initAndDeploy(options)`

Initialize and deploy the OOXML JSON Cloud Run service.

**Parameters:**
- `options` (Object, optional): Deployment options
  - `projectId` (string): Override PROJECT_ID
  - `region` (string): Override REGION (default: 'us-central1')
  - `skipBillingCheck` (boolean): Skip billing verification

**Returns:** Promise<string> - Deployed service URL

**Example:**
```javascript
const serviceUrl = await OOXMLDeployment.initAndDeploy({
  region: 'us-central1',
  skipBillingCheck: false
})
```

##### `getDeploymentStatus()`

Get current deployment status.

**Returns:** Object - Deployment status information

## Kerning Functions

### `applyKerningToDuarteSlidedoc(options)`

Apply advanced kerning to Duarte slidedoc.

**Parameters:**
- `options` (Object, optional): Configuration options
  - `fileName` (string): Name of file to process (default: 'Duarte_Slidedoc_Download (1).pptx')
  - `outputName` (string): Name for output file (default: auto-generated)
  - `addMetadata` (boolean): Add processing metadata (default: true)

**Returns:** Promise<Object> - Processing result with file information

**Result Object:**
```javascript
{
  success: true,
  input: {
    fileId: "1abc...",
    fileName: "original.pptx",
    sizeMB: 2.5
  },
  output: {
    fileId: "2def...",
    fileName: "enhanced.pptx",
    sizeMB: 2.6,
    url: "https://drive.google.com/..."
  },
  processing: {
    slidesProcessed: 15,
    kerningApplications: 847,
    ruleBreakdown: {
      "Large titles": 23,
      "Headers": 156,
      "Body text": 432,
      "Bold text": 89,
      "Letter pair kerning": 147
    },
    letterPairs: 147
  },
  timestamp: "2024-01-15T10:30:00.000Z"
}
```

**Example:**
```javascript
const result = await applyKerningToDuarteSlidedoc({
  fileName: 'MyPresentation.pptx',
  outputName: 'MyPresentation_Enhanced.pptx'
})

console.log(`Processed ${result.processing.slidesProcessed} slides`)
console.log(`Applied ${result.processing.kerningApplications} kerning adjustments`)
```

### `testKerningSetup()`

Test kerning setup and dependencies.

**Returns:** Object - Setup validation results

**Result Object:**
```javascript
{
  success: true,
  checks: {
    tempFolder: { status: "found", id: "folder123" },
    duarteFile: { 
      status: "found", 
      id: "file456",
      name: "Duarte_Slidedoc_Download (1).pptx",
      sizeMB: 3.2
    },
    ooxmlService: { status: "available" },
    serviceUrl: { status: "configured", url: "https://..." }
  },
  errors: []
}
```

## Deployment Functions

### `setupProjectId()`

Set Google Cloud Project ID in Script Properties.

**Usage:**
1. Edit the function to replace 'your-project-id-here' with your actual project ID
2. Run the function

### `showPreflightChecks()`

Show the preflight checks sidebar for setup verification.

### `deployToUSFreeTier()`

Deploy the PPTX processing service to US free tier.

**Returns:** Promise<string> - Service URL

### `testDeployedService()`

Test the deployed PPTX processing service.

**Returns:** Promise<Object> - Test results

### `checkDeploymentStatus()`

Check current deployment status.

**Returns:** Object - Status information

### `quickDeployToFreeTier()`

Deploy everything in one step (skip preflight checks).

**Returns:** Promise<string> - Service URL

## Utility Functions

### Web App Handlers

#### `doPost(e)`

Handle POST requests to the web app.

**Parameters:**
- `e` (Object): Event object with request data

**Supported Functions:**
- `ping` - Simple connectivity test
- `healthCheck` - Service health check
- `getServiceInfo` - Service information
- `processKerning` - Apply kerning to files

#### `doGet(e)`

Handle GET requests to the web app.

**Parameters:**
- `e` (Object): Event object with query parameters

### Helper Functions

#### `ping(name)`

Simple ping function for testing.

**Parameters:**
- `name` (string, optional): Name to include in response (default: 'World')

**Returns:** Object - Ping response

#### `healthCheck()`

Check health of services.

**Returns:** Object - Health status

#### `getServiceInfo()`

Get service information.

**Returns:** Object - Service details

## Error Handling

### Error Codes

The service uses specific error codes for systematic error handling:

- `OOXML_JSON_001`: Cloud Run service not deployed
- `OOXML_JSON_002`: Invalid manifest format
- `OOXML_JSON_003`: File size exceeds session limit
- `OOXML_JSON_004`: Server-side operation failed
- `OOXML_JSON_005`: Session creation failed
- `OOXML_JSON_006`: GCP billing not enabled
- `OOXML_JSON_007`: Required APIs not enabled

### Exception Handling

All async functions properly handle errors and provide meaningful messages:

```javascript
try {
  const result = await applyKerningToDuarteSlidedoc()
  console.log('Success:', result)
} catch (error) {
  console.error('Error:', error.message)
  // Error message will include specific error code if applicable
}
```

## Configuration Constants

### Default Settings

```javascript
// OOXMLJsonService configuration
{
  REGION: 'us-central1',
  SERVICE: 'ooxml-json',
  PUBLIC: true,
  BUDGET_AMOUNT_UNITS: '5',
  BUDGET_CURRENCY: 'USD'
}

// File size limits
{
  maxFileSizeMB: 100,
  sessionThresholdMB: 25
}
```

### Script Properties

The system uses these Script Properties:

- `GCP_PROJECT_ID`: Google Cloud Project ID
- `CF_BASE`: Cloud Run service URL
- `CLOUD_SERVICE_URL`: Backup service URL storage

## Best Practices

### Function Calling

1. **Always await async functions:**
```javascript
const result = await applyKerningToDuarteSlidedoc()
```

2. **Handle errors appropriately:**
```javascript
try {
  const result = await deployToUSFreeTier()
} catch (error) {
  console.error('Deployment failed:', error.message)
}
```

3. **Check setup before processing:**
```javascript
const setupOk = testKerningSetup()
if (setupOk.success) {
  await applyKerningToDuarteSlidedoc()
}
```

### Performance Considerations

- Files under 25MB are processed directly
- Larger files use session-based processing
- Service calls timeout after 60 seconds (Cloud Run free tier limit)
- Memory limit is 512MB (Cloud Run free tier limit)