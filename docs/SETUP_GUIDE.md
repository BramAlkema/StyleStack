# PPTX Processor v2 - Setup Guide

This guide walks you through setting up the PPTX Processor v2 from scratch.

## Prerequisites

1. **Google Account** with access to:
   - Google Apps Script
   - Google Drive
   - Google Cloud Platform

2. **Google Cloud Project** with:
   - Billing enabled
   - Cloud Run API access

## Step-by-Step Setup

### Phase 1: Create Google Apps Script Project

1. **Create GAS Project**
   - Go to [script.google.com](https://script.google.com)
   - Click "New Project"
   - Name it "PPTX Processor v2"

2. **Copy Source Files**
   - Delete the default `Code.gs` file
   - Create these files and copy the content:

   **Main Files:**
   - `Main.js` → Copy from `src/Main.js`
   - `OOXMLDeployment.js` → Copy from `src/OOXMLDeployment.js`

   **Library Files:**
   - `OOXMLJsonService.js` → Copy from `lib/OOXMLJsonService.js`
   - `FFlatePPTXService.js` → Copy from `lib/FFlatePPTXService.js`

   **Example Files:**
   - `KerningProcessor.js` → Copy from `examples/KerningProcessor.js`
   - `DeployFromGAS.js` → Copy from `examples/DeployFromGAS.js`

3. **Configure OAuth Scopes**
   - Click the gear icon (Project Settings)
   - Check "Show 'appsscript.json' manifest file in editor"
   - Replace `appsscript.json` content with:

   ```json
   {
     "timeZone": "America/New_York",
     "dependencies": {
       "enabledAdvancedServices": []
     },
     "exceptionLogging": "STACKDRIVER",
     "oauthScopes": [
       "https://www.googleapis.com/auth/drive",
       "https://www.googleapis.com/auth/drive.file",
       "https://www.googleapis.com/auth/presentations",
       "https://www.googleapis.com/auth/script.external_request",
       "https://www.googleapis.com/auth/cloud-platform"
     ],
     "runtimeVersion": "V8",
     "webapp": {
       "access": "ANYONE",
       "executeAs": "USER_DEPLOYING"
     }
   }
   ```

### Phase 2: Deploy Cloud Run Service

1. **Set Project ID**
   ```javascript
   // Run this function in GAS
   setupProjectId()
   ```
   - Replace 'your-project-id-here' with your actual GCP project ID
   - This saves the project ID to Script Properties

2. **Run Preflight Checks**
   ```javascript
   // This opens a sidebar to verify setup
   showPreflightChecks()
   ```
   - Click the "Enable Billing" link if needed
   - Ensure your GCP project has billing enabled

3. **Deploy to Cloud Run**
   ```javascript
   // Deploy to US free tier
   deployToUSFreeTier()
   ```
   - This creates the Cloud Run service in us-central1
   - Takes 2-5 minutes to complete
   - Returns the service URL when complete

4. **Test Deployment**
   ```javascript
   // Verify the service is working
   testDeployedService()
   ```
   - Checks service health
   - Confirms PPTX processing capabilities

### Phase 3: Setup Kerning Processing

1. **Create Drive Folder**
   - Go to [drive.google.com](https://drive.google.com)
   - Create a new folder named "temp"
   - Note: Must be exactly "temp" (lowercase)

2. **Upload Test File**
   - Upload your PPTX file to the temp folder
   - Rename it to: `Duarte_Slidedoc_Download (1).pptx`
   - Note: Filename must match exactly

3. **Test Kerning Setup**
   ```javascript
   // Verify kerning is ready
   testKerningFunction()
   ```
   - Checks temp folder exists
   - Confirms PPTX file is present
   - Validates service connectivity

### Phase 4: Apply Kerning

1. **Process PPTX File**
   ```javascript
   // Apply advanced kerning
   applyKerningToDuarteSlidedoc()
   ```
   - Extracts PPTX to JSON manifest
   - Applies kerning rules to all slides
   - Creates enhanced output file

2. **Review Results**
   - Check the console output for processing statistics
   - Find the enhanced file in Google Drive
   - Compare typography with original

## Configuration Options

### Custom File Processing

```javascript
// Process a different file
applyKerningToDuarteSlidedoc({
  fileName: 'MyPresentation.pptx',
  outputName: 'MyPresentation_Enhanced.pptx',
  addMetadata: true
})
```

### Alternative Deployment

```javascript
// Quick deployment (skip preflight checks)
quickDeployToFreeTier()
```

## Verification Commands

### Check Deployment Status
```javascript
checkDeploymentStatus()
```

### Test Service Health
```javascript
OOXMLJsonService.healthCheck()
```

### Validate Kerning Setup
```javascript
testKerningSetup()
```

## Troubleshooting

### Common Setup Issues

**"PROJECT_ID not configured"**
- Solution: Run `setupProjectId()` with your GCP project ID

**"Billing not enabled"**
- Solution: Enable billing in GCP Console → Billing

**"Required APIs not enabled"**
- Solution: APIs are enabled automatically during deployment

**"temp folder not found"**
- Solution: Create "temp" folder in Google Drive root

**"Duarte slidedoc not found"**
- Solution: Upload file with exact name to temp folder

### Support Functions

**Show complete setup instructions:**
```javascript
showSetupInstructions()
```

**Reset deployment:**
```javascript
// Clear stored service URL
PropertiesService.getScriptProperties().deleteProperty('CF_BASE')
```

## Next Steps

Once setup is complete:

1. **Regular Usage**: Call `applyKerningToDuarteSlidedoc()` to process files
2. **Monitoring**: Use `checkDeploymentStatus()` to verify service health
3. **Customization**: Modify kerning rules in `KerningProcessor.js`

## Cost Considerations

- **Cloud Run**: Free tier provides 2 million requests/month
- **Storage**: Minimal GCS usage for temporary files
- **Typical Cost**: $0/month for normal usage patterns

The service is optimized for the Google Cloud free tier and should not incur charges for typical presentation processing workloads.