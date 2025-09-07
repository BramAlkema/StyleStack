# Selector Registry Architecture

## Overview

A variable-driven OOXML patching system that eliminates hardcoded element names, attributes, and values from patches. All selectors and names live in a central registry, with patches using only variables and token references.

## Core Principles

1. **No Literals in Patches** - Patches never hardcode element/attr names or values
2. **Central Registry** - One lookup table for all OOXML names and paths
3. **Variable-Driven XPath** - Use `local-name()` + `namespace-uri()` with bound variables
4. **Lean Base Templates** - Don't prepopulate every possible path
5. **Smart Upserts** - Create missing elements on demand from fragments

## Architecture Components

### 1. Selector Registry (`selectors.yaml`)

Central lookup table containing:
- Namespace definitions
- Element names with namespaces
- Attribute names
- Reusable XPath patterns

```yaml
ns:
  a: "http://schemas.openxmlformats.org/drawingml/2006/main"
  p: "http://schemas.openxmlformats.org/presentationml/2006/main"
  w: "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

el:
  clrScheme: { name: "clrScheme", ns: "$ns.a" }
  accent1:   { name: "accent1",   ns: "$ns.a" }
  srgbClr:   { name: "srgbClr",   ns: "$ns.a" }
  
attr:
  val:   "val"
  type:  "type"
  styleId: "styleId"

paths:
  accent1_color_attr: >
    //*[local-name()=$clrScheme and namespace-uri()=$nsA]
      /*[local-name()=$accent1 and namespace-uri()=$nsA]
      /*[local-name()=$srgbClr and namespace-uri()=$nsA]/@*[local-name()=$val]
```

### 2. Fragment Library

Reusable XML snippets for elements that may not exist:

```yaml
fragments:
  footerPlaceholder: |
    <p:sp xmlns:p="..." xmlns:a="...">
      <p:nvSpPr>
        <p:cNvPr id="{tokens.ids.footer}" name="Footer"/>
        <p:nvPr><p:ph type="ftr" idx="1"/></p:nvPr>
      </p:nvSpPr>
      <!-- ... -->
    </p:sp>
```

### 3. Enhanced Patch Operations

Beyond basic set/insert/remove:

- **ensurePath** - Create element if missing, then operate
- **ensurePart** - Create entire OOXML part if missing
- **ensureAttr** - Set attribute, creating parent if needed

### 4. Variable-Aware XPath Executor

Runtime that:
1. Loads selector registry
2. Builds variable map (element names, namespaces, attributes)
3. Binds variables to XPath at evaluation time
4. Executes with lxml

## Benefits

1. **Maintainability** - Change selectors in one place
2. **Safety** - No hardcoded strings scattered across patches
3. **Flexibility** - Swap registries for different OOXML flavors
4. **Cleaner Diffs** - Selector changes are registry edits, not patch hunts
5. **Lean Templates** - Base templates stay minimal
6. **Dynamic Creation** - Build missing structures on demand

## Implementation Strategy

### Phase 1: Core Infrastructure
- Selector registry schema and loader
- Variable-aware XPath executor
- Integration with existing token system

### Phase 2: Enhanced Operations
- ensurePath operation
- ensurePart operation  
- Fragment library system
- ID collision prevention

### Phase 3: Registry Population
- Complete OOXML element/attribute catalog
- Common path patterns library
- Product-specific registries (PPT/Word/Excel)

### Phase 4: Migration
- Convert existing patches to use registry
- Remove all hardcoded selectors
- Validate coverage

## Technical Considerations

### XPath 1.0 Limitations

Cannot use `$prefix:tag` syntax. Must use:
```xpath
*[local-name()=$elementName and namespace-uri()=$namespaceUri]
```

### Variable Binding

Variables bound at XPath evaluation time:
```python
xp = ET.XPath(xpath_str)
nodes = xp(tree, **varmap)  # varmap has all $vars
```

### Namespace Management

Keep namespaces organized:
- `$nsA` for DrawingML
- `$nsP` for PresentationML  
- `$nsW` for WordprocessingML
- `$nsS` for SpreadsheetML

## Example Usage

### Patch Using Registry

```yaml
targets:
  - file: ppt/theme/theme1.xml
    ops:
      - set:
          xpathRef: "accent1_color_attr"  # Reference from registry
          value: "{tokens.colors.primary}"  # Token value
          
      - ensurePath:
          xpathRef: "footer_placeholder"
          anchorRef: "spTree_root"
          fragmentRef: "fragments.footerPlaceholder"
```

### No Hardcoded Names

Before (hardcoded):
```yaml
xpath: "//a:clrScheme/a:accent1/a:srgbClr/@val"
```

After (variable-driven):
```yaml
xpathRef: "accent1_color_attr"  # Resolved from registry
```

## Backlog Structure

See `backlog/selector-registry.md` for implementation tasks.