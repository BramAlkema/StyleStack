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
      label: 'Design Tokens',
      items: [
        'design-tokens/overview',
        'design-tokens/hierarchy',
        'design-tokens/customization',
        'design-tokens/variables',
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
        'customization/localization',
        'customization/compliance',
        'customization/accessibility',
      ],
    },
    {
      type: 'category',
      label: 'Deployment',
      items: [
        'deployment/ci-cd',
        'deployment/distribution',
        'deployment/add-ins',
        'deployment/monitoring',
      ],
    },
    {
      type: 'category',
      label: 'API Reference',
      items: [
        'api/build-system',
        'api/token-resolver',
        'api/ooxml-processor',
        'api/cli',
      ],
    },
    {
      type: 'category',
      label: 'Examples',
      items: [
        'examples/university',
        'examples/government',
        'examples/enterprise',
        'examples/international',
      ],
    },
  ],
};

module.exports = sidebars;