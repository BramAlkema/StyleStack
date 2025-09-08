/**
 * StyleStack Typography-First Website
 * Interactive features and animations
 */

// Smooth scrolling for navigation links
document.addEventListener('DOMContentLoaded', function() {
    // Navigation smooth scroll
    const navLinks = document.querySelectorAll('.main-nav a[href^="#"]');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);
            
            if (targetSection) {
                targetSection.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Intersection Observer for scroll animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);

    // Observe elements for animation
    const animatedElements = document.querySelectorAll(
        '.token-layer, .feature-card, .platform-card, .api-endpoint, .type-specimen'
    );
    
    animatedElements.forEach(el => {
        observer.observe(el);
    });

    // Typography specimen interactive features
    initializeTypographyShowcase();
    
    // Token layer hover effects
    initializeTokenLayers();
    
    // Code block syntax highlighting
    initializeCodeBlocks();
    
    // Responsive navigation
    initializeNavigation();
});

/**
 * Initialize typography showcase interactive features
 */
function initializeTypographyShowcase() {
    const specimens = document.querySelectorAll('.type-specimen');
    
    specimens.forEach(specimen => {
        // Add hover effects to typography specimens
        specimen.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.02)';
            this.style.transition = 'all 0.3s ease';
        });
        
        specimen.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });

    // Interactive font size adjustment demo
    const displayText = document.querySelector('.specimen-display');
    if (displayText) {
        let originalSize = window.getComputedStyle(displayText).fontSize;
        
        displayText.addEventListener('click', function() {
            const currentSize = parseFloat(window.getComputedStyle(this).fontSize);
            const newSize = currentSize === parseFloat(originalSize) ? currentSize * 1.2 : parseFloat(originalSize);
            
            this.style.fontSize = newSize + 'px';
            this.style.transition = 'font-size 0.3s ease';
        });
    }
}

/**
 * Initialize token layer interactions
 */
function initializeTokenLayers() {
    const tokenLayers = document.querySelectorAll('.token-layer');
    
    tokenLayers.forEach(layer => {
        const layerType = layer.dataset.layer;
        
        // Add click functionality to expand/collapse token examples
        const layerTitle = layer.querySelector('.layer-title');
        const tokenExamples = layer.querySelector('.token-examples');
        
        if (layerTitle && tokenExamples) {
            layerTitle.style.cursor = 'pointer';
            layerTitle.addEventListener('click', function() {
                const isExpanded = tokenExamples.style.display !== 'none';
                
                if (isExpanded) {
                    tokenExamples.style.display = 'none';
                    layerTitle.style.opacity = '0.6';
                } else {
                    tokenExamples.style.display = 'grid';
                    layerTitle.style.opacity = '1';
                }
                
                // Add visual feedback
                layer.style.transition = 'all 0.3s ease';
            });
        }

        // Color-coded hover effects based on layer type
        layer.addEventListener('mouseenter', function() {
            let hoverColor;
            switch(layerType) {
                case 'system':
                    hoverColor = '#3b82f6';
                    break;
                case 'corporate':
                    hoverColor = '#8b5cf6';
                    break;
                case 'channel':
                    hoverColor = '#f97316';
                    break;
                case 'template':
                    hoverColor = '#525252';
                    break;
                default:
                    hoverColor = '#3b82f6';
            }
            
            this.style.borderLeftColor = hoverColor;
            this.style.borderLeftWidth = '6px';
        });
        
        layer.addEventListener('mouseleave', function() {
            this.style.borderLeftWidth = '4px';
        });
    });

    // Token card copy functionality
    const tokenCards = document.querySelectorAll('.token-card');
    tokenCards.forEach(card => {
        card.addEventListener('click', async function() {
            const tokenName = this.querySelector('.token-name').textContent;
            const tokenValue = this.querySelector('.token-value').textContent;
            const copyText = `${tokenName}: ${tokenValue}`;
            
            try {
                await navigator.clipboard.writeText(copyText);
                showToast('Token copied to clipboard!');
                
                // Visual feedback
                this.style.background = '#dbeafe';
                setTimeout(() => {
                    this.style.background = '#fafafa';
                }, 200);
            } catch (err) {
                console.log('Clipboard API not available');
            }
        });
        
        // Add copy cursor hint
        card.style.cursor = 'pointer';
        card.title = 'Click to copy token';
    });
}

/**
 * Initialize code block features
 */
function initializeCodeBlocks() {
    const codeBlocks = document.querySelectorAll('.code-block');
    
    codeBlocks.forEach(block => {
        // Add copy button to code blocks
        const copyButton = document.createElement('button');
        copyButton.textContent = 'Copy';
        copyButton.className = 'copy-button';
        copyButton.style.cssText = `
            position: absolute;
            top: 1rem;
            right: 1rem;
            background: #374151;
            color: #f3f4f6;
            border: 1px solid #4b5563;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            font-size: 0.75rem;
            cursor: pointer;
            transition: all 0.15s ease;
        `;
        
        // Position the parent relatively
        block.parentElement.style.position = 'relative';
        block.parentElement.appendChild(copyButton);
        
        copyButton.addEventListener('click', async function() {
            const code = block.textContent;
            try {
                await navigator.clipboard.writeText(code);
                this.textContent = 'Copied!';
                this.style.background = '#059669';
                setTimeout(() => {
                    this.textContent = 'Copy';
                    this.style.background = '#374151';
                }, 2000);
            } catch (err) {
                this.textContent = 'Error';
                setTimeout(() => {
                    this.textContent = 'Copy';
                }, 2000);
            }
        });
        
        copyButton.addEventListener('mouseenter', function() {
            this.style.background = '#4b5563';
        });
        
        copyButton.addEventListener('mouseleave', function() {
            if (this.textContent === 'Copy') {
                this.style.background = '#374151';
            }
        });
    });
}

/**
 * Initialize responsive navigation
 */
function initializeNavigation() {
    // Add active state management for navigation
    const navLinks = document.querySelectorAll('.main-nav a');
    const sections = document.querySelectorAll('.section[id]');
    
    // Intersection observer for active navigation state
    const navObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            const navLink = document.querySelector(`.main-nav a[href="#${entry.target.id}"]`);
            
            if (entry.isIntersecting && navLink) {
                // Remove active class from all nav links
                navLinks.forEach(link => link.classList.remove('active'));
                // Add active class to current nav link
                navLink.classList.add('active');
            }
        });
    }, {
        threshold: 0.3,
        rootMargin: '-20% 0px -20% 0px'
    });
    
    sections.forEach(section => {
        navObserver.observe(section);
    });
}

/**
 * Utility function to show toast notifications
 */
function showToast(message, duration = 3000) {
    const toast = document.createElement('div');
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        background: #1f2937;
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        font-size: 0.875rem;
        font-weight: 500;
        z-index: 1000;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        transform: translateY(100px);
        transition: transform 0.3s ease;
    `;
    
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => {
        toast.style.transform = 'translateY(0)';
    }, 10);
    
    // Animate out and remove
    setTimeout(() => {
        toast.style.transform = 'translateY(100px)';
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, duration);
}

/**
 * Parallax effect for hero section
 */
function initializeParallax() {
    const hero = document.querySelector('.hero');
    if (!hero) return;
    
    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        const parallax = hero.querySelector('.hero-content');
        
        if (parallax && scrolled < hero.offsetHeight) {
            const speed = scrolled * 0.3;
            parallax.style.transform = `translateY(${speed}px)`;
        }
    });
}

/**
 * Advanced typography controls (experimental)
 */
function initializeAdvancedTypography() {
    // Font feature settings toggle (for supported browsers)
    const toggleFeatures = document.createElement('button');
    toggleFeatures.textContent = 'Toggle Advanced Typography';
    toggleFeatures.style.cssText = `
        position: fixed;
        bottom: 1rem;
        left: 1rem;
        background: #374151;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-size: 0.75rem;
        cursor: pointer;
        z-index: 100;
        opacity: 0.7;
        transition: opacity 0.3s ease;
    `;
    
    let advancedEnabled = true;
    
    toggleFeatures.addEventListener('click', function() {
        advancedEnabled = !advancedEnabled;
        
        const fontFeatures = advancedEnabled 
            ? "'kern' 1, 'liga' 1, 'calt' 1, 'pnum' 1, 'tnum' 0, 'onum' 1, 'lnum' 0, 'dlig' 1"
            : "'kern' 0, 'liga' 0, 'calt' 0";
        
        document.body.style.fontFeatureSettings = fontFeatures;
        this.textContent = advancedEnabled ? 'Disable Advanced Typography' : 'Enable Advanced Typography';
        
        showToast(advancedEnabled ? 'Advanced typography enabled' : 'Advanced typography disabled');
    });
    
    toggleFeatures.addEventListener('mouseenter', function() {
        this.style.opacity = '1';
    });
    
    toggleFeatures.addEventListener('mouseleave', function() {
        this.style.opacity = '0.7';
    });
    
    document.body.appendChild(toggleFeatures);
}

// CSS for animations (added dynamically)
const animationStyles = `
    .animate-in {
        animation: fadeInUp 0.6s ease-out forwards;
    }
    
    .main-nav a.active {
        background-color: #2563eb;
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    @media (prefers-reduced-motion: reduce) {
        .animate-in {
            animation: none;
        }
    }
`;

// Add styles to document
const styleSheet = document.createElement('style');
styleSheet.textContent = animationStyles;
document.head.appendChild(styleSheet);

// Initialize advanced features on load
window.addEventListener('load', function() {
    initializeParallax();
    initializeAdvancedTypography();
});