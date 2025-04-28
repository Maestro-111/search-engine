
from django.core.paginator import Paginator
from .utils.elastic_agent import QueryElastic
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import WikipediaCrawlForm
from .models import CrawlJob
from .tasks import run_crawl_job  # This will be your Celery task
import logging

# import aiohttp
# import asyncio

logger = logging.getLogger("webserver")

def search_wikipedia(request):

    query = ""
    results = []

    if request.method == "POST":
        query = request.POST.get('query', '')

    elif request.method == "GET":
        query = request.GET.get('query', '')


    if query:

        es = QueryElastic()
        raw_results = es.query_general(query)

        paginator = Paginator(raw_results, 10)
        page_number = request.GET.get('page', 1)
        results = paginator.get_page(page_number)

    context = {
        'query': query,
        'results': results
    }

    return render(request, 'source_wikipedia/wikipedia_search.html', context)


def crawl_wikipedia(request):
    if request.method == 'POST':
        form = WikipediaCrawlForm(request.POST)
        if form.is_valid():
            # Extract form data
            starting_url = form.cleaned_data['starting_url']
            crawl_depth = form.cleaned_data['crawl_depth']
            max_pages = form.cleaned_data['max_pages']
            mongodb_collection = form.cleaned_data['mongodb_collection']

            # Log the request
            logger.info(f"Starting crawl {starting_url} with depth {crawl_depth} and max_pages {max_pages}. "
                        f"Going to store the results in {mongodb_collection}")

            # Create a job record in the database
            job = CrawlJob.objects.create(
                status="queued",
                starting_url=starting_url,
                crawl_depth=crawl_depth,
                max_pages=max_pages,
                mongodb_collection=mongodb_collection
            )

            # Send the task to Celery
            run_crawl_job.delay(job.id)

            # Redirect to the job status page
            messages.success(request, "Crawl job has been submitted successfully.")
            return redirect('crawler_job_status', job_id=job.id)
    else:
        form = WikipediaCrawlForm()

    return render(request, 'source_wikipedia/wikipedia_crawl.html', {'form': form})


def crawler_job_status(request, job_id):
    """View to check the status of a crawler job"""
    try:
        job = CrawlJob.objects.get(id=job_id)
        return render(request, 'source_wikipedia/wikipedia_crawl_status.html', {'job': job})
    except CrawlJob.DoesNotExist:
        messages.error(request, "Job not found.")
        return redirect('crawl_wikipedia')


def all_crawler_jobs(request):
    """View to list all crawler jobs"""
    jobs = CrawlJob.objects.all().order_by('-created_at')
    return render(request, 'source_wikipedia/wikipedia_crawl_jobs.html', {'jobs': jobs})