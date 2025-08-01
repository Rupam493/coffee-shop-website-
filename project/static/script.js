document.addEventListener('DOMContentLoaded', function () {
  try {
    // Verify Swiper library is loaded
    if (typeof Swiper === 'undefined') {
      console.error('Swiper library not loaded. Check CDN or local file.');
      return;
    }

    // Initialize Swiper for testimonials slider
    const swiper = new Swiper('.swiper', {
      slidesPerView: 1,
      spaceBetween: 20,
      autoHeight: true,
      loop: true,
      pagination: {
        el: '.swiper-pagination',
        clickable: true,
      },
      navigation: {
        nextEl: '.swiper-button-next',
        prevEl: '.swiper-button-prev',
      },
      breakpoints: {
        640: {
          slidesPerView: 2,
          spaceBetween: 30,
        },
        1024: {
          slidesPerView: 3,
          spaceBetween: 40,
        },
      },
    });

    console.log('Swiper initialized successfully:', swiper);
  } catch (error) {
    console.error('Error initializing Swiper:', error);
  }

  // Mobile menu toggle
  const menuOpenButton = document.getElementById('menu-open-button');
  const menuCloseButton = document.getElementById('menu-close-button');
  const navMenu = document.querySelector('.nav-menu');

  if (menuOpenButton && navMenu) {
    menuOpenButton.addEventListener('click', () => {
      navMenu.classList.add('active');
      console.log('Menu opened');
    });
  }

  if (menuCloseButton && navMenu) {
    menuCloseButton.addEventListener('click', () => {
      navMenu.classList.remove('active');
      console.log('Menu closed');
    });
  }
});