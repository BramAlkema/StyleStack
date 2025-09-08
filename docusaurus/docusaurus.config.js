// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

const config = {
  title: 'StyleStack',
  tagline: 'Typography as a Service - Design Tokens for Professional Office Templates',
  favicon: 'img/favicon.ico',

  // GitHub Pages deployment config
  url: 'https://BramAlkema.github.io',
  baseUrl: '/StyleStack/docs/',
  
  // GitHub deployment config
  organizationName: 'BramAlkema',
  projectName: 'StyleStack',
  deploymentBranch: 'gh-pages',
  trailingSlash: false,

  onBrokenLinks: 'warn',
  onBrokenMarkdownLinks: 'warn',

  // Internationalization
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
    // Ready for future: 'en', 'es', 'de', 'fr', 'nl', 'zh-cn'
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          routeBasePath: '/',
          sidebarPath: './sidebars.js',
          editUrl: 'https://github.com/BramAlkema/StyleStack/tree/main/docusaurus/',
          // Versioning configuration
          lastVersion: 'current',
          versions: {
            current: {
              label: 'Current',
              path: '/',
            },
          },
        },
        blog: false, // Disable blog
        theme: {
          customCss: './src/css/custom.css',
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      navbar: {
        title: 'StyleStack',
        logo: {
          alt: 'StyleStack Logo',
          src: 'img/logo.svg',
        },
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'tutorialSidebar',
            position: 'left',
            label: 'Documentation',
          },
          {
            href: 'https://BramAlkema.github.io/StyleStack/',
            label: 'Downloads',
            position: 'left',
          },
          {
            href: 'https://github.com/BramAlkema/StyleStack',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Documentation',
            items: [
              {
                label: 'Getting Started',
                to: '/getting-started',
              },
              {
                label: 'Design Tokens',
                to: '/design-tokens',
              },
              {
                label: 'Fork Management',
                to: '/fork-management',
              },
            ],
          },
          {
            title: 'Community',
            items: [
              {
                label: 'GitHub',
                href: 'https://github.com/BramAlkema/StyleStack',
              },
              {
                label: 'Issues',
                href: 'https://github.com/BramAlkema/StyleStack/issues',
              },
              {
                label: 'Discussions',
                href: 'https://github.com/BramAlkema/StyleStack/discussions',
              },
            ],
          },
          {
            title: 'More',
            items: [
              {
                label: 'Releases',
                href: 'https://github.com/BramAlkema/StyleStack/releases',
              },
              {
                label: 'Roadmap',
                href: 'https://github.com/BramAlkema/StyleStack/blob/main/docs/PRODUCT_BACKLOG.md',
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} StyleStack. Built with Docusaurus.`,
      },
      prism: {
        theme: require('prism-react-renderer').themes.github,
        darkTheme: require('prism-react-renderer').themes.dracula,
        additionalLanguages: ['python', 'yaml', 'xml-doc'],
      },
    }),
};

module.exports = config;