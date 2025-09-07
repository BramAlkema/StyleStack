# Validate Templates

Run quality validation on generated templates to check accessibility, style compliance, and OOXML structure.

## Usage
```bash
/validate-templates [template-path]
```

## Action
- Check contrast ratios for accessibility compliance
- Ban tacky effects (3D shadows, bevels, glows)
- Validate OOXML structure with xmllint
- Verify custom properties are present
- Generate validation report