document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.querySelector('form');
    const resultsContainer = document.querySelector('.bbc-results');
    const loadingSpinner = document.querySelector('.loading-spinner');
    const paginationControls = document.querySelector('.pagination-controls');

    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            performSearch(1);
        });
    }

    function performSearch(page) {

        const query = document.querySelector('input[name="query"]').value;
        if (!query) return;

        resultsContainer.innerHTML = '';
        loadingSpinner.style.display = 'block';

        console.log(`${searchForm.action}?query=${encodeURIComponent(query)}&page=${page}`)

        fetch(`${searchForm.action}?query=${encodeURIComponent(query)}&page=${page}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            // Hide loading spinner
            loadingSpinner.style.display = 'none';

            displayResults(data);

            const url = new URL(window.location);
            url.searchParams.set('query', query);
            url.searchParams.set('page', page);
            window.history.pushState({}, '', url);

        })
        .catch(error => {
            loadingSpinner.style.display = 'none';
            resultsContainer.innerHTML = `<div class="error">Error performing search: ${error.message}</div>`;
        });
    }

    function displayResults(data) {
        if (data.results.length === 0) {
            resultsContainer.innerHTML = '<div class="no-results">No results found</div>';
            paginationControls.innerHTML = '';
            return;
        }

        let html = '';

        // Generate HTML for results
        data.results.forEach(result => {

            html += `
                <div class="bbc-article">
                    <h3><a href="${result.url}" target="_blank">${result.title}</a></h3>
                    <div class="article-excerpt">${result.excerpt}</div>
                    <div class="article-meta">
                        <span class="last-updated">Updated: ${result.last_updated}</span>
                    </div>
                </div>
            `;
        });

        resultsContainer.innerHTML = html;

        let paginationHtml = '';
        if (data.has_previous) {
            paginationHtml += `<a href="#" class="page-link" data-page="${data.page_number - 1}">Previous</a>`;
        }

        paginationHtml += `<span class="page-info">Page ${data.page_number} of ${data.num_pages}</span>`;

        if (data.has_next) {
            paginationHtml += `<a href="#" class="page-link" data-page="${data.page_number + 1}">Next</a>`;
        }

        paginationControls.innerHTML = paginationHtml;

        document.querySelectorAll('.page-link').forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const page = this.getAttribute('data-page');
                performSearch(page);
                window.scrollTo(0, 0);
            });
        });
    }

    const urlParams = new URLSearchParams(window.location.search);
    const initialQuery = urlParams.get('query');
    const initialPage = urlParams.get('page') || 1;

    if (initialQuery) {
        document.querySelector('input[name="query"]').value = initialQuery;
        performSearch(initialPage);
    }
});