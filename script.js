// Loading Screen
document.addEventListener('DOMContentLoaded', () => {
    const loadingScreen = document.querySelector('.loading-screen');
    
    // Ensure minimum loading time of 2 seconds
    setTimeout(() => {
        loadingScreen.classList.add('fade-out');
        // Enable scrolling after loading
        document.body.style.overflow = 'visible';
    }, 2000);
});

// Disable scrolling during loading
document.body.style.overflow = 'hidden';

// Slider Logic with Fade Effect
let slides = document.querySelectorAll('.slide');
let currentIndex = 0;

function showSlide(index) {
    slides.forEach((slide, i) => {
        slide.classList.toggle('active', i === index);
    });
}

setInterval(() => {
    currentIndex = (currentIndex + 1) % slides.length;
    showSlide(currentIndex);
}, 5000);

// Header Scroll Effect
window.addEventListener('scroll', () => {
    const header = document.querySelector('header');
    if (window.scrollY > 50) {
        header.classList.add('scrolled');
    } else {
        header.classList.remove('scrolled');
    }
});

// Mobile Menu
const menuBtn = document.querySelector('.menu-btn');
const nav = document.querySelector('nav');
let menuOpen = false;

menuBtn.addEventListener('click', () => {
    if (!menuOpen) {
        menuBtn.classList.add('active');
        nav.classList.add('active');
        menuOpen = true;
    } else {
        menuBtn.classList.remove('active');
        nav.classList.remove('active');
        menuOpen = false;
    }
});

// Close menu when clicking nav links
const navLinks = document.querySelectorAll('nav a');
navLinks.forEach(link => {
    link.addEventListener('click', () => {
        menuBtn.classList.remove('active');
        nav.classList.remove('active');
        menuOpen = false;
    });
}); 