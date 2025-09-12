// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  tutorialSidebar: [
    {
      type: 'doc',
      id: 'intro',
      label: 'Introduction',
    },
    {
      type: 'category',
      label: 'Getting Started',
      collapsed: false,
      items: [
        'getting-started/quick-start',
        'getting-started/installation',
        'getting-started/first-template',
      ],
    },
    {
      type: 'category',
      label: 'Licensing',
      items: [
        'licensing/overview',
        'licensing/request-license',
        'licensing/pricing',
        'licensing/technical-implementation',
        'licensing/troubleshooting',
      ],
    },
    {
      type: 'category',
      label: 'Design Tokens',
      items: [
        'design-tokens/overview',
        'design-tokens/hierarchy',
        'design-tokens/customization',
        'design-tokens/variables',
        'design-tokens/aspect-ratio-tokens',
        'design-tokens/extraction',
      ],
    },
    {
      type: 'category',
      label: 'SuperThemes',
      collapsed: false,
      items: [
        'superthemes/overview',
        'superthemes/quick-start',
        'superthemes/architecture',
        'superthemes/aspect-ratios',
        'superthemes/design-variants',
        'superthemes/generation',
        'superthemes/validation',
        'superthemes/cli-reference',
        'superthemes/troubleshooting',
      ],
    },
    {
      type: 'category',
      label: 'Typography',
      items: [
        'typography/overview',
      ],
    },
    {
      type: 'category',
      label: 'Fork Management',
      items: [
        'fork-management/creating-fork',
        'fork-management/customizing',
        'fork-management/syncing-upstream',
        'fork-management/governance',
      ],
    },
    {
      type: 'category',
      label: 'Customization',
      items: [
        'customization/branding',
      ],
    },
    {
      type: 'category',
      label: 'Deployment',
      items: [
        'deployment/ci-cd',
      ],
    },
    {
      type: 'category',
      label: 'API Reference',
      items: [
        'api/build-system',
        'api/extraction-api',
      ],
    },
    {
      type: 'category',
      label: 'Examples',
      items: [
        'examples/university',
      ],
    },
    {
      type: 'doc',
      id: 'acknowledgements',
      label: 'Acknowledgements',
    },
  ],
};

module.exports = sidebars;