import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import HomepageFeatures from '@site/src/components/HomepageFeatures';
import Heading from '@theme/Heading';

import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <Heading as="h1" className={clsx('hero__title', styles.heroTitle)}>
          <span className={styles.titleAccent}>Style</span>
          <span className={styles.titlePrimary}>Stack</span>
        </Heading>
        <p className={clsx('hero__subtitle', styles.heroSubtitle)}>
          {siteConfig.tagline}
        </p>
        <div className={styles.heroDescription}>
          <p className={styles.heroLead}>
            Transform Office templates through hierarchical design tokens delivered via intelligent Office add-ins.
          </p>
          <p className={styles.heroTagline}>
            Professional typography • Accessible design • Brand compliance
          </p>
        </div>
        <div className={styles.buttons}>
          <Link
            className={clsx('button button--secondary button--lg', styles.getStartedButton)}
            to="/getting-started/quick-start">
            Get Started
          </Link>
          <Link
            className={clsx('button button--outline button--lg', styles.apiButton)}
            to="/api/extraction-api">
            API Documentation
          </Link>
        </div>
      </div>
    </header>
  );
}

export default function Home() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={`${siteConfig.title} - Typography as a Service`}
      description="Professional Office templates with modern design tokens, EMU-based typography, and cross-platform compatibility">
      <HomepageHeader />
      <main>
        <HomepageFeatures />
        
        {/* Quick Overview Section */}
        <section className={styles.quickOverview}>
          <div className="container">
            <div className="row">
              <div className="col col--8 col--offset-2">
                <div className={styles.overviewCard}>
                  <Heading as="h2" className={styles.overviewTitle}>
                    Design Tokens as a Service
                  </Heading>
                  <p className={styles.overviewDescription}>
                    StyleStack revolutionizes Office template creation through a four-layer 
                    hierarchical design token system. From global design foundations to 
                    channel-specific implementations, every template maintains perfect 
                    brand compliance and accessibility standards.
                  </p>
                  
                  <div className={styles.tokenHierarchy}>
                    <div className={styles.tokenLayer}>
                      <div className={styles.layerNumber}>1</div>
                      <div className={styles.layerContent}>
                        <h4>Design System 2025</h4>
                        <p>Global foundation with typography, accessibility, and grid systems</p>
                      </div>
                    </div>
                    
                    <div className={styles.tokenLayer}>
                      <div className={styles.layerNumber}>2</div>
                      <div className={styles.layerContent}>
                        <h4>Corporate Layer</h4>
                        <p>Brand overrides for colors, fonts, and identity elements</p>
                      </div>
                    </div>
                    
                    <div className={styles.tokenLayer}>
                      <div className={styles.layerNumber}>3</div>
                      <div className={styles.layerContent}>
                        <h4>Channel Layer</h4>
                        <p>Use-case specialization for presentations, documents, and reports</p>
                      </div>
                    </div>
                    
                    <div className={styles.tokenLayer}>
                      <div className={styles.layerNumber}>4</div>
                      <div className={styles.layerContent}>
                        <h4>Template Layer</h4>
                        <p>Final resolved variables in OOXML extension format</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className={styles.codeExample}>
                    <pre>
                      <code>{`# Extract design tokens from existing templates
python tools/design_token_extractor.py extract/presentation.pptx

# Generate branded templates with design tokens
python build.py --tokens corporate-tokens.yaml --org acme --out branded.potx

# Templates automatically update when users open documents`}</code>
                    </pre>
                  </div>
                  
                  <div className={styles.overviewButtons}>
                    <Link
                      className="button button--primary button--lg"
                      to="/design-tokens/extraction">
                      Try Token Extraction
                    </Link>
                    <Link
                      className="button button--outline button--lg"
                      to="/typography/overview">
                      Typography System
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}