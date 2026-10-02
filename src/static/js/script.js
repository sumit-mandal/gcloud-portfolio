// ── Trip chapter reveal + open ──
(function () {
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const trips = document.querySelectorAll('.trip');

    function openFromTrip(trip) {
        try {
            openLightbox(JSON.parse(trip.dataset.section));
        } catch (_) { /* ignore bad payload */ }
    }

    trips.forEach((trip) => {
        trip.addEventListener('click', () => openFromTrip(trip));
        trip.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                openFromTrip(trip);
            }
        });
    });

    if (reduceMotion) {
        trips.forEach(trip => trip.classList.add('in-view'));
        return;
    }

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add('in-view');
            }
        });
    }, { threshold: 0.35 });

    trips.forEach(trip => observer.observe(trip));
})();

// ── Lightbox / Image Carousel ──
let lbCurrentIndex = 0;
let lbTotalImages = 0;
let touchStartX = 0;
let touchEndX = 0;

function openLightbox(section) {
    const lb = document.getElementById('lightbox');
    const track = document.getElementById('lightbox-track');
    document.getElementById('lightbox-title').textContent = section.title;
    document.getElementById('lightbox-desc').textContent = section.description;

    track.innerHTML = '';
    lbCurrentIndex = 0;
    lbTotalImages = section.images ? section.images.length : 0;

    if (lbTotalImages > 0) {
        section.images.forEach(img => {
            const slide = document.createElement('div');
            slide.className = 'lb-slide';
            const el = document.createElement('img');
            el.src = img.url;
            el.alt = section.title;
            slide.appendChild(el);
            track.appendChild(slide);
        });
    }

    updateSlider();
    lb.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function updateSlider() {
    const track = document.getElementById('lightbox-track');
    track.style.transform = `translateX(-${lbCurrentIndex * 100}%)`;

    const counter = document.getElementById('lb-counter');
    const prevBtn = document.getElementById('lb-prev');
    const nextBtn = document.getElementById('lb-next');

    if (lbTotalImages <= 1) {
        counter.style.display = 'none';
        prevBtn.style.display = 'none';
        nextBtn.style.display = 'none';
    } else {
        counter.style.display = '';
        prevBtn.style.display = '';
        nextBtn.style.display = '';
        counter.textContent = `${lbCurrentIndex + 1} / ${lbTotalImages}`;
        prevBtn.classList.toggle('hidden', lbCurrentIndex === 0);
        nextBtn.classList.toggle('hidden', lbCurrentIndex === lbTotalImages - 1);
    }
}

function slideImage(dir) {
    const newIndex = lbCurrentIndex + dir;
    if (newIndex < 0 || newIndex >= lbTotalImages) return;
    lbCurrentIndex = newIndex;
    updateSlider();
}

function closeLightbox(event) {
    if (event && event.target !== event.currentTarget) return;
    const lb = document.getElementById('lightbox');
    lb.classList.remove('active');
    document.body.style.overflow = '';
}

document.addEventListener('keydown', (e) => {
    const lb = document.getElementById('lightbox');
    if (!lb.classList.contains('active')) return;
    if (e.key === 'Escape') closeLightbox();
    if (e.key === 'ArrowLeft') slideImage(-1);
    if (e.key === 'ArrowRight') slideImage(1);
});

document.addEventListener('DOMContentLoaded', () => {
    const slider = document.getElementById('lightbox-slider');
    if (!slider) return;
    slider.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });
    slider.addEventListener('touchend', (e) => {
        touchEndX = e.changedTouches[0].screenX;
        const diff = touchStartX - touchEndX;
        if (Math.abs(diff) > 50) {
            slideImage(diff > 0 ? 1 : -1);
        }
    }, { passive: true });
});

// ── Soft hero parallax ──
(function () {
    const hero = document.querySelector('.hero');
    if (!hero) return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    window.addEventListener('scroll', () => {
        const y = window.scrollY;
        hero.style.transform = `translateY(${y * 0.18}px)`;
        hero.style.opacity = String(Math.max(0.2, 1 - y / 780));
    }, { passive: true });
})();
