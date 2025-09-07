# Build Templates

Build StyleStack OOXML templates using the Python build system.

## Usage
```bash
/build-templates --org [orgname] --channel [present|doc|finance] --products [potx|dotx|xltx]
```

## Action
- Run the StyleStack build system to generate Office templates
- Apply core defaults + org patches + channel overlays
- Validate output templates for quality and accessibility
- Generate artifacts with proper naming convention