document.addEventListener('DOMContentLoaded', function() {
    // Initialize any common functionality here
    console.log('Web Crawler Search App initialized');

    // Add active class to current navigation item
    const currentLocation = window.location.pathname;
    const navLinks = document.querySelectorAll('.main-nav a');

    navLinks.forEach(link => {
        const linkPath = link.getAttribute('href');
        if (currentLocation === linkPath ||
            (linkPath !== '/' && currentLocation.startsWith(linkPath))) {
            link.classList.add('active');
        }
    });
});