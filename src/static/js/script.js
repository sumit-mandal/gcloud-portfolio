// ── Particles ──
(function () {
    const canvas = document.getElementById('particles');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let w, h, dots = [];

    function resize() {
        w = canvas.width = window.innerWidth;
        h = canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener('resize', resize);

    const COUNT = Math.min(60, Math.floor(window.innerWidth / 20));
    for (let i = 0; i < COUNT; i++) {
        dots.push({
            x: Math.random() * w,
            y: Math.random() * h,
            r: Math.random() * 1.5 + 0.5,
            dx: (Math.random() - 0.5) * 0.3,
            dy: (Math.random() - 0.5) * 0.3,
            o: Math.random() * 0.3 + 0.1
        });
    }

    function draw() {
        ctx.clearRect(0, 0, w, h);
        dots.forEach(d => {
            d.x += d.dx;
            d.y += d.dy;
            if (d.x < 0) d.x = w;
            if (d.x > w) d.x = 0;
            if (d.y < 0) d.y = h;
            if (d.y > h) d.y = 0;
            ctx.beginPath();
            ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(249,115,22,${d.o})`;
            ctx.fill();
        });
        // Draw connections
        for (let i = 0; i < dots.length; i++) {
            for (let j = i + 1; j < dots.length; j++) {
                const dx = dots[i].x - dots[j].x;
                const dy = dots[i].y - dots[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 120) {
                    ctx.beginPath();
                    ctx.moveTo(dots[i].x, dots[i].y);
                    ctx.lineTo(dots[j].x, dots[j].y);
                    ctx.strokeStyle = `rgba(249,115,22,${0.06 * (1 - dist / 120)})`;
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                }
            }
        }
        requestAnimationFrame(draw);
    }
    draw();
})();

// ── Scroll-triggered card entrance ──
(function () {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry, i) => {
            if (entry.isIntersecting) {
                // Stagger the animation based on position
                const card = entry.target;
                const cards = Array.from(document.querySelectorAll('.card'));
                const idx = cards.indexOf(card);
                card.style.animationDelay = `${idx * 0.08}s`;
                card.classList.add('visible');
                observer.unobserve(card);
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.card').forEach(card => observer.observe(card));
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

// Touch swipe support
document.addEventListener('DOMContentLoaded', () => {
    const slider = document.getElementById('lightbox-slider');
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

// ── Smooth parallax on hero ──
(function () {
    const hero = document.querySelector('.hero');
    if (!hero) return;
    window.addEventListener('scroll', () => {
        const y = window.scrollY;
        hero.style.transform = `translateY(${y * 0.3}px)`;
        hero.style.opacity = Math.max(0, 1 - y / 600);
    }, { passive: true });
})();
