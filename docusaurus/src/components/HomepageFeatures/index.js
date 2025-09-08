import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

const FeatureList = [
  {
    title: 'Design Tokens as a Service',
    Svg: require('@site/static/img/design-tokens.svg').default,
    description: (
      <>
        Hierarchical design tokens that cascade from global design systems through 
        corporate branding to channel-specific templates. Professional typography, 
        accessibility, and brand compliance built-in.
      </>
    ),
  },
  {
    title: 'Typography Intelligence',
    Svg: require('@site/static/img/typography.svg').default,
    description: (
      <>
        EMU-based precision typography with golden ratio scaling, advanced OpenType 
        features, and WCAG AAA accessibility compliance. Professional typography 
        that rivals InDesign-level control.
      </>
    ),
  },
  {
    title: 'Multi-Platform Distribution',
    Svg: require('@site/static/img/multi-platform.svg').default,
    description: (
      <>
        Universal template distribution across Microsoft Office, LibreOffice, and 
        Google Workspace. Embedded add-ins automatically update design tokens when 
        documents open.
      </>
    ),
  },
  {
    title: 'Reverse Engineering',
    Svg: require('@site/static/img/extraction.svg').default,
    description: (
      <>
        Extract design tokens from existing templates with our drop-and-extract workflow. 
        Modernize legacy Office templates and convert them into maintainable design systems.
      </>
    ),
  },
];

function Feature({Svg, title, description}) {
  return (
    <div className={clsx('col col--6')}>
      <div className="text--center">
        <Svg className={styles.featureSvg} role="img" />
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}