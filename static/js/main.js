document.addEventListener('DOMContentLoaded', () => {
    const nav = document.querySelector('.site-nav');
    const backToTop = document.getElementById('backToTop');
    const loader = document.getElementById('pageLoader');

    const toggleChrome = () => {
        if (window.scrollY > 40) {
            nav?.classList.add('navbar-scrolled');
            backToTop && (backToTop.style.display = 'grid');
        } else {
            nav?.classList.remove('navbar-scrolled');
            backToTop && (backToTop.style.display = 'none');
        }
    };

    toggleChrome();
    window.addEventListener('scroll', toggleChrome);
    backToTop?.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
    window.addEventListener('load', () => { if (loader) loader.style.display = 'none'; });

    const counters = document.querySelectorAll('[data-counter]');
    counters.forEach((counter) => {
        const target = Number(counter.getAttribute('data-counter') || 0);
        let current = 0;
        const step = Math.max(1, Math.ceil(target / 120));
        const tick = () => {
            current += step;
            counter.textContent = current >= target ? target.toLocaleString() : current.toLocaleString();
            if (current < target) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
    });
});
