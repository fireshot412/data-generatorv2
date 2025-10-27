// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', () => {
    initScrollProgress();
    initScrollAnimations();
    initNavigationHide();
    initSmoothScroll();
    trackResonance();

    // Initialize convergence lines after DOM is ready
    setTimeout(() => {
        updateConvergenceLines();
        animateConvergencePaths();
    }, 100);
});

// ===== SCROLL PROGRESS BAR =====
function initScrollProgress() {
    const progressBar = document.getElementById('progressBar');

    window.addEventListener('scroll', () => {
        const windowHeight = window.innerHeight;
        const documentHeight = document.documentElement.scrollHeight - windowHeight;
        const scrolled = window.scrollY;
        const progress = (scrolled / documentHeight) * 100;

        progressBar.style.width = `${progress}%`;
    });
}

// ===== SCROLL ANIMATIONS =====
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
            }
        });
    }, observerOptions);

    // Add reveal class to elements that should animate in
    const revealElements = document.querySelectorAll(`
        .persona-card,
        .story-block,
        .problem-dimension,
        .cost-card,
        .step-card,
        .transformation-item,
        .matters-stat,
        .contact-card
    `);

    revealElements.forEach(el => {
        el.classList.add('reveal');
        observer.observe(el);
    });
}

// ===== NAVIGATION AUTO-HIDE =====
let lastScrollTop = 0;
let scrollTimeout;

function initNavigationHide() {
    const nav = document.getElementById('nav');

    window.addEventListener('scroll', () => {
        clearTimeout(scrollTimeout);

        scrollTimeout = setTimeout(() => {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

            if (scrollTop > lastScrollTop && scrollTop > 100) {
                // Scrolling down
                nav.classList.add('hidden');
            } else {
                // Scrolling up
                nav.classList.remove('hidden');
            }

            lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
        }, 100);
    });
}

// ===== SMOOTH SCROLL =====
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));

            if (target) {
                const navHeight = document.getElementById('nav').offsetHeight;
                const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - navHeight - 20;

                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// ===== SCROLL TO SECTION =====
function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        const navHeight = document.getElementById('nav').offsetHeight;
        const targetPosition = section.getBoundingClientRect().top + window.pageYOffset - navHeight - 20;

        window.scrollTo({
            top: targetPosition,
            behavior: 'smooth'
        });
    }
}

// ===== SCROLL TO STORY =====
function scrollToStory(personaName) {
    const accordion = document.getElementById(`story-${personaName}`);
    if (accordion) {
        // Expand the accordion
        if (!accordion.classList.contains('expanded')) {
            toggleStoryAccordion(personaName);
        }

        // Scroll to it
        const navHeight = document.getElementById('nav').offsetHeight;
        const targetPosition = accordion.getBoundingClientRect().top + window.pageYOffset - navHeight - 20;

        window.scrollTo({
            top: targetPosition,
            behavior: 'smooth'
        });
    }
}

// ===== ACCORDION TOGGLE =====
function toggleStoryAccordion(personaName) {
    const accordion = document.getElementById(`story-${personaName}`);
    if (!accordion) return;

    const isExpanded = accordion.classList.contains('expanded');

    if (isExpanded) {
        // Collapse this accordion
        accordion.classList.remove('expanded');
        const toggleText = accordion.querySelector('.toggle-text');
        if (toggleText) toggleText.textContent = 'Read Story';
    } else {
        // Expand this accordion
        accordion.classList.add('expanded');
        const toggleText = accordion.querySelector('.toggle-text');
        if (toggleText) toggleText.textContent = 'Close Story';

        // Scroll to the accordion after a brief delay to allow expansion animation
        setTimeout(() => {
            const navHeight = document.getElementById('nav').offsetHeight;
            const targetPosition = accordion.getBoundingClientRect().top + window.pageYOffset - navHeight - 20;
            window.scrollTo({
                top: targetPosition,
                behavior: 'smooth'
            });
        }, 100);
    }
}

// ===== RESONANCE TRACKING =====
const resonanceData = {
    kris: null,
    josephine: null,
    felicia: null,
    ash: null
};

function handleResonance(persona, response) {
    resonanceData[persona] = response;

    // Store in localStorage
    localStorage.setItem('resonanceData', JSON.stringify(resonanceData));

    // Visual feedback
    const buttons = event.target.closest('.resonance-buttons').querySelectorAll('.resonance-btn');
    buttons.forEach(btn => {
        btn.style.opacity = '0.5';
        btn.disabled = true;
    });

    event.target.closest('.resonance-btn').style.opacity = '1';
    event.target.closest('.resonance-btn').style.background = response === 'yes' ? '#f0fdf4' : '#fef2f2';
    event.target.closest('.resonance-btn').style.borderColor = response === 'yes' ? '#00cc66' : '#ff4444';

    // Show thank you message
    setTimeout(() => {
        const thankYouMsg = document.createElement('div');
        thankYouMsg.textContent = 'Thanks for your feedback!';
        thankYouMsg.style.cssText = `
            margin-top: 1rem;
            padding: 0.5rem;
            background: #f0fdf4;
            color: #00cc66;
            border-radius: 8px;
            text-align: center;
            font-weight: 600;
            animation: fadeInUp 0.5s ease;
        `;

        event.target.closest('.story-resonance').appendChild(thankYouMsg);
    }, 300);

    console.log('Resonance feedback:', { persona, response, allData: resonanceData });

    // Thumbs down behavior: collapse current and expand next
    if (response === 'no') {
        const personaOrder = ['kris', 'josephine', 'felicia', 'ash'];
        const currentIndex = personaOrder.indexOf(persona);

        // Collapse current story after a brief delay
        setTimeout(() => {
            const currentAccordion = document.getElementById(`story-${persona}`);
            if (currentAccordion && currentAccordion.classList.contains('expanded')) {
                toggleStoryAccordion(persona);
            }

            // If there's a next story, expand it
            if (currentIndex < personaOrder.length - 1) {
                const nextPersona = personaOrder[currentIndex + 1];
                setTimeout(() => {
                    const nextAccordion = document.getElementById(`story-${nextPersona}`);
                    if (nextAccordion && !nextAccordion.classList.contains('expanded')) {
                        toggleStoryAccordion(nextPersona);
                    }
                }, 400); // Delay to allow collapse animation to complete
            }
        }, 1000); // Wait 1 second to show the thank you message
    }
}

function trackResonance() {
    // Load existing resonance data from localStorage
    const stored = localStorage.getItem('resonanceData');
    if (stored) {
        const data = JSON.parse(stored);
        Object.assign(resonanceData, data);
    }
}

// ===== OVERALL FEEDBACK =====
function handleOverallFeedback(response) {
    // Store in localStorage
    localStorage.setItem('overallFeedback', response);

    // Visual feedback
    const buttons = event.target.closest('.feedback-buttons').querySelectorAll('.feedback-btn');
    buttons.forEach(btn => {
        btn.style.opacity = '0.5';
        btn.disabled = true;
    });

    const clickedButton = event.target.closest('.feedback-btn');
    clickedButton.style.opacity = '1';

    if (response === 'yes') {
        clickedButton.style.background = '#f0fdf4';
        clickedButton.style.borderColor = '#00cc66';
    } else if (response === 'maybe') {
        clickedButton.style.background = '#fffbeb';
        clickedButton.style.borderColor = '#ffbb33';
    } else {
        clickedButton.style.background = '#fef2f2';
        clickedButton.style.borderColor = '#ff4444';
    }

    // Show thank you message
    setTimeout(() => {
        const thankYouMsg = document.createElement('div');
        thankYouMsg.textContent = 'Thank you for your honest feedback!';
        thankYouMsg.style.cssText = `
            margin-top: 1.5rem;
            padding: 1rem;
            background: #f0fdf4;
            color: #00cc66;
            border-radius: 8px;
            text-align: center;
            font-weight: 600;
            font-size: 1.125rem;
            animation: fadeInUp 0.5s ease;
        `;

        event.target.closest('.feedback-prompt').appendChild(thankYouMsg);
    }, 300);

    console.log('Overall feedback:', response);
}

// ===== FORM HANDLERS =====
function handleProblemForm(e) {
    e.preventDefault();

    const formData = new FormData(e.target);
    const data = {
        type: 'problem',
        name: formData.get('name'),
        email: formData.get('email'),
        role: formData.get('role'),
        experience: formData.get('experience'),
        timestamp: new Date().toISOString(),
        resonanceData: resonanceData
    };

    console.log('Problem form submission:', data);

    // Store in localStorage
    const submissions = JSON.parse(localStorage.getItem('formSubmissions') || '[]');
    submissions.push(data);
    localStorage.setItem('formSubmissions', JSON.stringify(submissions));

    // Show success message
    showFormSuccess(e.target);
}

function handleInvestorForm(e) {
    e.preventDefault();

    const formData = new FormData(e.target);
    const data = {
        type: 'investor',
        name: formData.get('name'),
        email: formData.get('email'),
        company: formData.get('company'),
        message: formData.get('message'),
        timestamp: new Date().toISOString()
    };

    console.log('Investor form submission:', data);

    // Store in localStorage
    const submissions = JSON.parse(localStorage.getItem('formSubmissions') || '[]');
    submissions.push(data);
    localStorage.setItem('formSubmissions', JSON.stringify(submissions));

    // Show success message
    showFormSuccess(e.target);
}

function handleWaitlistForm(e) {
    e.preventDefault();

    const formData = new FormData(e.target);
    const data = {
        type: 'waitlist',
        name: formData.get('name'),
        email: formData.get('email'),
        role: formData.get('role'),
        company: formData.get('company') || '',
        timestamp: new Date().toISOString()
    };

    console.log('Waitlist form submission:', data);

    // Store in localStorage
    const submissions = JSON.parse(localStorage.getItem('formSubmissions') || '[]');
    submissions.push(data);
    localStorage.setItem('formSubmissions', JSON.stringify(submissions));

    // Show success message
    showFormSuccess(e.target);
}

function handleCofounderForm(e) {
    e.preventDefault();

    const formData = new FormData(e.target);
    const data = {
        type: 'cofounder',
        name: formData.get('name'),
        email: formData.get('email'),
        background: formData.get('background'),
        why: formData.get('why'),
        timestamp: new Date().toISOString()
    };

    console.log('Co-founder form submission:', data);

    // Store in localStorage
    const submissions = JSON.parse(localStorage.getItem('formSubmissions') || '[]');
    submissions.push(data);
    localStorage.setItem('formSubmissions', JSON.stringify(submissions));

    // Show success message
    showFormSuccess(e.target);
}

function showFormSuccess(form) {
    // Hide the form
    form.style.display = 'none';

    // Create success message
    const successMsg = document.createElement('div');
    successMsg.style.cssText = `
        padding: 2rem;
        background: #f0fdf4;
        border: 2px solid #00cc66;
        border-radius: 12px;
        text-align: center;
        animation: fadeInUp 0.5s ease;
    `;

    successMsg.innerHTML = `
        <div style="font-size: 3rem; margin-bottom: 1rem;">✓</div>
        <h3 style="font-size: 1.5rem; margin-bottom: 0.5rem; color: #00cc66;">Thank You!</h3>
        <p style="color: #6c757d;">We've received your submission and will be in touch soon.</p>
    `;

    form.parentElement.appendChild(successMsg);
}

// ===== SHARE FUNCTIONS =====
function shareLinkedIn() {
    const url = encodeURIComponent(window.location.href);
    const title = encodeURIComponent('The Problem With SaaS Demo Data');
    const text = encodeURIComponent('Four people, different roles, one universal problem. Does this resonate with you?');

    window.open(
        `https://www.linkedin.com/sharing/share-offsite/?url=${url}`,
        '_blank',
        'width=600,height=600'
    );

    console.log('Shared on LinkedIn');
}

function shareTwitter() {
    const url = encodeURIComponent(window.location.href);
    const text = encodeURIComponent('Four people, different roles, one universal problem with SaaS data generation. Does this resonate with you?');

    window.open(
        `https://twitter.com/intent/tweet?url=${url}&text=${text}`,
        '_blank',
        'width=600,height=600'
    );

    console.log('Shared on Twitter');
}

function shareEmail() {
    const subject = encodeURIComponent('The Problem With SaaS Demo Data');
    const body = encodeURIComponent(`I thought you might find this interesting:\n\n${window.location.href}\n\nFour people, different roles, one universal problem with SaaS data generation. Does this resonate with you?`);

    window.location.href = `mailto:?subject=${subject}&body=${body}`;

    console.log('Shared via email');
}

// ===== ANALYTICS HELPER =====
// This function logs all stored data - useful for debugging and understanding engagement
function getAnalyticsData() {
    return {
        resonanceData: JSON.parse(localStorage.getItem('resonanceData') || '{}'),
        overallFeedback: localStorage.getItem('overallFeedback'),
        formSubmissions: JSON.parse(localStorage.getItem('formSubmissions') || '[]'),
        pageViews: localStorage.getItem('pageViews') || 0,
        timeSpent: localStorage.getItem('timeSpent') || 0
    };
}

// Track page view
const pageViews = parseInt(localStorage.getItem('pageViews') || '0') + 1;
localStorage.setItem('pageViews', pageViews.toString());

// Track time spent on page
let startTime = Date.now();
window.addEventListener('beforeunload', () => {
    const timeSpent = parseInt(localStorage.getItem('timeSpent') || '0') + (Date.now() - startTime);
    localStorage.setItem('timeSpent', timeSpent.toString());
});

// Make analytics accessible via console
window.getAnalyticsData = getAnalyticsData;

// Log to console for debugging
console.log('Page initialized. Analytics available via: getAnalyticsData()');
console.log('Current analytics:', getAnalyticsData());

// ===== SCROLL INDICATOR CLICK =====
document.querySelector('.scroll-indicator')?.addEventListener('click', () => {
    const personasSection = document.getElementById('personas');
    if (personasSection) {
        const navHeight = document.getElementById('nav').offsetHeight;
        const targetPosition = personasSection.getBoundingClientRect().top + window.pageYOffset - navHeight - 20;

        window.scrollTo({
            top: targetPosition,
            behavior: 'smooth'
        });
    }
});

// ===== HERO SCROLL PROMPT CLICK =====
document.querySelector('.hero-scroll-prompt')?.addEventListener('click', () => {
    const missionSection = document.getElementById('mission');
    if (missionSection) {
        const navHeight = document.getElementById('nav').offsetHeight;
        const targetPosition = missionSection.getBoundingClientRect().top + window.pageYOffset - navHeight - 20;

        window.scrollTo({
            top: targetPosition,
            behavior: 'smooth'
        });
    }
});

// ===== MISSION SCROLL INDICATOR CLICK =====
document.querySelector('.mission-scroll-indicator')?.addEventListener('click', () => {
    const personasSection = document.getElementById('personas');
    if (personasSection) {
        const navHeight = document.getElementById('nav').offsetHeight;
        const targetPosition = personasSection.getBoundingClientRect().top + window.pageYOffset - navHeight - 20;

        window.scrollTo({
            top: targetPosition,
            behavior: 'smooth'
        });
    }
});

// ===== ENHANCED PERSONA CARD HOVER EFFECTS =====
document.querySelectorAll('.persona-card').forEach(card => {
    card.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-8px) scale(1.02)';
    });

    card.addEventListener('mouseleave', function() {
        this.style.transform = '';
    });
});

// ===== CONVERGENCE PATH ANIMATION =====
function updateConvergenceLines() {
    const svg = document.querySelector('.convergence-svg');
    const names = document.querySelectorAll('.convergence-name');
    const centerCircle = document.querySelector('.convergence-center');

    if (!svg || names.length !== 4 || !centerCircle) {
        console.error('Convergence elements not found');
        return;
    }

    // Get SVG dimensions
    const svgRect = svg.getBoundingClientRect();
    const svgViewBox = svg.viewBox.baseVal;
    const svgWidth = svgViewBox.width;
    const svgHeight = svgViewBox.height;

    // Calculate center circle position in viewBox coordinates
    const circleCenterX = svgWidth / 2;
    const circleCenterY = svgViewBox.height - 40; // Near bottom, accounting for circle

    // Get the paths
    const paths = svg.querySelectorAll('.convergence-line');

    if (paths.length !== 4) {
        console.error('Expected 4 convergence lines');
        return;
    }

    // For each name, calculate its center and update the corresponding path
    names.forEach((nameEl, index) => {
        const nameRect = nameEl.getBoundingClientRect();
        const svgOffset = svg.getBoundingClientRect();

        // Calculate name center in page coordinates
        const nameCenterX = nameRect.left + (nameRect.width / 2);

        // Convert to SVG viewBox coordinates
        const svgX = ((nameCenterX - svgOffset.left) / svgOffset.width) * svgWidth;

        // Y coordinate - start just below the names (small offset)
        const startY = 20;

        // Update the path
        const path = paths[index];
        const newPath = `M ${svgX} ${startY} Q ${svgX} 150, ${circleCenterX} ${circleCenterY}`;
        path.setAttribute('d', newPath);
    });
}

function animateConvergencePaths() {
    const paths = document.querySelectorAll('.convergence-path .path-line');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Update line positions before animating
                updateConvergenceLines();

                paths.forEach((path, index) => {
                    setTimeout(() => {
                        path.style.animation = `pathGrow 1s ease forwards`;
                    }, index * 100);
                });
                observer.disconnect();
            }
        });
    }, { threshold: 0.3 });

    const convergenceSection = document.querySelector('.convergence-visual');
    if (convergenceSection) {
        observer.observe(convergenceSection);
    }
}

// Update lines on window resize to maintain alignment
window.addEventListener('resize', () => {
    updateConvergenceLines();
});

// Initial update when page loads
window.addEventListener('load', () => {
    setTimeout(updateConvergenceLines, 100); // Small delay to ensure layout is complete
});

// Add path grow animation to stylesheet dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes pathGrow {
        from {
            height: 0;
            opacity: 0;
        }
        to {
            height: 250px;
            opacity: 1;
        }
    }

    .convergence-path .path-line {
        height: 0;
        opacity: 0;
    }
`;
document.head.appendChild(style);

animateConvergencePaths();

// ===== KEYBOARD NAVIGATION =====
document.addEventListener('keydown', (e) => {
    // ESC to scroll to top
    if (e.key === 'Escape') {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
});

// ===== PRINT ANALYTICS ON DEMAND =====
// Useful for demoing the feedback collection
window.printAnalytics = function() {
    const data = getAnalyticsData();
    console.log('=== ANALYTICS REPORT ===');
    console.log('\nResonance by Persona:');
    console.log(`  Kris: ${data.resonanceData.kris || 'No response'}`);
    console.log(`  Josephine: ${data.resonanceData.josephine || 'No response'}`);
    console.log(`  Felicia: ${data.resonanceData.felicia || 'No response'}`);
    console.log(`  Ash: ${data.resonanceData.ash || 'No response'}`);
    console.log(`\nOverall Feedback: ${data.overallFeedback || 'No response'}`);
    console.log(`\nForm Submissions: ${data.formSubmissions.length}`);
    data.formSubmissions.forEach((sub, i) => {
        console.log(`  ${i + 1}. ${sub.type} - ${sub.name} (${sub.email})`);
    });
    console.log(`\nPage Views: ${data.pageViews}`);
    console.log(`Time Spent: ${Math.round(data.timeSpent / 1000)} seconds`);
    console.log('========================');
};

// ===== PERFORMANCE MONITORING =====
window.addEventListener('load', () => {
    // Log performance metrics
    if ('performance' in window) {
        const perfData = performance.getEntriesByType('navigation')[0];
        if (perfData) {
            console.log('Page Load Performance:');
            console.log(`  DOM Content Loaded: ${Math.round(perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart)}ms`);
            console.log(`  Total Load Time: ${Math.round(perfData.loadEventEnd - perfData.loadEventStart)}ms`);
        }
    }
});

// ===== LAZY LOADING ENHANCEMENT =====
// Add loading="lazy" to images if not already present
document.querySelectorAll('img:not([loading])').forEach(img => {
    img.setAttribute('loading', 'lazy');
});

// ===== ACCESSIBILITY ENHANCEMENTS =====
// Add skip to content link for keyboard users
const skipLink = document.createElement('a');
skipLink.href = '#personas';
skipLink.textContent = 'Skip to content';
skipLink.style.cssText = `
    position: absolute;
    top: -100px;
    left: 0;
    background: #0066cc;
    color: white;
    padding: 0.5rem 1rem;
    z-index: 10000;
    transition: top 0.3s;
`;
skipLink.addEventListener('focus', () => {
    skipLink.style.top = '0';
});
skipLink.addEventListener('blur', () => {
    skipLink.style.top = '-100px';
});
document.body.insertBefore(skipLink, document.body.firstChild);

// ===== EXPORT DATA FUNCTION =====
// Allow users to export their feedback data
window.exportFeedbackData = function() {
    const data = getAnalyticsData();
    const dataStr = JSON.stringify(data, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `feedback-data-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
    console.log('Feedback data exported');
};

console.log('💡 Tip: Use printAnalytics() to see collected feedback');
console.log('💡 Tip: Use exportFeedbackData() to download feedback as JSON');

// ===== LOGIN PAGE NAVIGATION =====
function navigateToLogin() {
    // Hide all main content sections
    const mainSections = document.querySelectorAll('section:not(#login-page)');
    mainSections.forEach(section => {
        section.style.display = 'none';
    });

    // Hide footer
    const footer = document.querySelector('.footer');
    if (footer) footer.style.display = 'none';

    // Show login page
    const loginPage = document.getElementById('login-page');
    if (loginPage) {
        loginPage.style.display = 'flex';
    }

    // Hide navigation
    const nav = document.getElementById('nav');
    if (nav) nav.style.display = 'none';

    // Hide progress bar
    const progressBar = document.getElementById('progressBar');
    if (progressBar) progressBar.style.display = 'none';

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'instant' });
}

function navigateToHome() {
    // Show all main content sections
    const mainSections = document.querySelectorAll('section:not(#login-page)');
    mainSections.forEach(section => {
        section.style.display = '';
    });

    // Show footer
    const footer = document.querySelector('.footer');
    if (footer) footer.style.display = '';

    // Hide login page
    const loginPage = document.getElementById('login-page');
    if (loginPage) {
        loginPage.style.display = 'none';
    }

    // Show navigation
    const nav = document.getElementById('nav');
    if (nav) nav.style.display = '';

    // Show progress bar
    const progressBar = document.getElementById('progressBar');
    if (progressBar) progressBar.style.display = '';

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function handleLogin(e) {
    e.preventDefault();

    const formData = new FormData(e.target);
    const data = {
        email: formData.get('email'),
        password: formData.get('password'),
        remember: formData.get('remember') === 'on',
        timestamp: new Date().toISOString()
    };

    console.log('Login attempt:', { email: data.email, remember: data.remember });

    // Show success message (since this is just for show)
    const loginBox = document.querySelector('.login-box');
    const successMsg = document.createElement('div');
    successMsg.style.cssText = `
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        padding: 2rem;
        background: #f0fdf4;
        border: 2px solid #00cc66;
        border-radius: 12px;
        text-align: center;
        z-index: 1000;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    `;

    successMsg.innerHTML = `
        <div style="font-size: 3rem; margin-bottom: 1rem;">✓</div>
        <h3 style="font-size: 1.5rem; margin-bottom: 0.5rem; color: #00cc66;">Login Successful!</h3>
        <p style="color: #6c757d; margin-bottom: 0;">This is just a demo page</p>
    `;

    loginBox.appendChild(successMsg);

    // Navigate back to home after 2 seconds
    setTimeout(() => {
        navigateToHome();
        successMsg.remove();
        e.target.reset();
    }, 2000);
}
