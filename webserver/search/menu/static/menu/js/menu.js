// JavaScript for the menu page

document.addEventListener('DOMContentLoaded', function() {
    // Add hover effect sound (optional)
    const sourceCards = document.querySelectorAll('.source-card');

    sourceCards.forEach(card => {
        // Add click event for mobile touch feedback
        card.addEventListener('click', function() {
            // Add a brief highlight effect when clicked
            this.classList.add('card-clicked');

            // Remove the effect after animation completes
            setTimeout(() => {
                this.classList.remove('card-clicked');
            }, 300);
        });

        // Add accessibility features
        card.setAttribute('role', 'button');
        card.setAttribute('aria-label', `Search ${card.querySelector('.source-name').textContent} data`);
    });

    // Optional: Add search/filter functionality for many sources
    const searchInput = document.getElementById('source-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();

            sourceCards.forEach(card => {
                const sourceName = card.querySelector('.source-name').textContent.toLowerCase();

                if (sourceName.includes(searchTerm)) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }
});
