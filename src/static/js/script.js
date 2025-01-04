document.addEventListener('DOMContentLoaded', () => {  
    const carousel = document.querySelector('.carousel');  
    const items = document.querySelectorAll('.carousel-item');  
    const nextButton = document.querySelector('.next');  
    const prevButton = document.querySelector('.prev');  
    const photoSelect = document.getElementById('photo-select');  
    let currentIndex = 0;  
    let startX, endX;  
  
    function updateCarousel() {  
        const offset = -currentIndex * 100;  
        carousel.style.transform = `translateX(${offset}%)`;  
        items.forEach((item, index) => {  
            item.style.opacity = index === currentIndex ? 1 : 0.5;  
            item.style.transform = index === currentIndex ? 'scale(1)' : 'scale(0.95)';  
        });  
    }  
  
    nextButton.addEventListener('click', () => {  
        currentIndex = (currentIndex + 1) % items.length;  
        updateCarousel();  
    });  
  
    prevButton.addEventListener('click', () => {  
        currentIndex = (currentIndex - 1 + items.length) % items.length;  
        updateCarousel();  
    });  
  
    photoSelect.addEventListener('change', (e) => {  
        currentIndex = parseInt(e.target.value);  
        updateCarousel();  
    });  
  
    // Handle touch events for mobile swiping  
    carousel.addEventListener('touchstart', (e) => {  
        startX = e.touches[0].clientX;  
    });  
  
    carousel.addEventListener('touchend', (e) => {  
        endX = e.changedTouches[0].clientX;  
        if (startX > endX + 50) {  
            currentIndex = (currentIndex + 1) % items.length;  
            updateCarousel();  
        } else if (startX < endX - 50) {  
            currentIndex = (currentIndex - 1 + items.length) % items.length;  
            updateCarousel();  
        }  
    });  
  
    updateCarousel();  
  
    // Add dynamic bounce effect to recruiter button  
    const ctaButton = document.querySelector('.cta-button');  
    ctaButton.addEventListener('mouseover', () => {  
        ctaButton.classList.add('bounce');  
    });  
  
    ctaButton.addEventListener('animationend', () => {  
        ctaButton.classList.remove('bounce');  
    });  
  
    // Surprise effect: Randomly change background color of header on click  
    const header = document.querySelector('.header');  
    const colors = ['#ff7f50', '#ff6347', '#84fab0', '#8fd3f4', '#333', '#f9f9f9'];  
    header.addEventListener('click', () => {  
        const randomColor = colors[Math.floor(Math.random() * colors.length)];  
        header.style.background = `linear-gradient(135deg, ${randomColor}, ${randomColor})`;  
    });  
  
    // Add unique colors and fade-in animation to paragraphs  
    document.querySelectorAll('.description').forEach((description, index) => {  
        description.classList.add(`p-${index}`);  
    });  
  
    // Add animation to select dropdown  
    photoSelect.addEventListener('mouseover', () => {  
        photoSelect.style.animation = 'selectAnimation 0.5s';  
    });  
  
    photoSelect.addEventListener('mouseout', () => {  
        photoSelect.style.animation = '';  
    });  
});  