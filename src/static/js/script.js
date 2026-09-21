document.addEventListener("DOMContentLoaded", () => {
    const sections = document.querySelectorAll(".section");
    const nav = document.querySelector(".site-nav");
    const chips = document.querySelectorAll(".skill-chip");

    const reveal = () => {
        if (window.scrollY > 24) {
            nav.classList.add("scrolled");
        } else {
            nav.classList.remove("scrolled");
        }

        sections.forEach((section) => {
            const rect = section.getBoundingClientRect();
            if (rect.top < window.innerHeight * 0.85 && rect.bottom > 60) {
                section.classList.add("visible");
            }
        });
    };

    window.addEventListener("scroll", reveal, { passive: true });
    reveal();

    document.querySelectorAll(".site-nav a").forEach((anchor) => {
        anchor.addEventListener("click", (e) => {
            const href = anchor.getAttribute("href");
            if (!href || !href.startsWith("#")) return;
            const target = document.querySelector(href);
            if (!target) return;
            e.preventDefault();
            target.scrollIntoView({ behavior: "smooth" });
        });
    });

    chips.forEach((chip, index) => {
        chip.style.transitionDelay = `${(index % 8) * 30}ms`;
    });
});
