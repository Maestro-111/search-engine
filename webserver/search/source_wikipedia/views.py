from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from elasticsearch import Elasticsearch
from .utils.elastic_agent import QueryElastic
import os
from .forms import WikipediaCrawlForm
import logging

import aiohttp
import asyncio

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


async def crawl_wikipedia(request):
    if request.method == 'POST':
        form = WikipediaCrawlForm(request.POST)
        if form.is_valid():
            starting_url = form.cleaned_data['starting_url']
            crawl_depth = form.cleaned_data['crawl_depth']
            max_pages = form.cleaned_data['max_pages']
            mongodb_collection = form.cleaned_data['mongodb_collection']

            logger.info(f"Starting crawl {starting_url} with depth {crawl_depth} and max_pages {max_pages}. "
                        f"Going to store the results in {mongodb_collection}")

            # Call the crawler API
            async with aiohttp.ClientSession() as session:
                crawler_url = "http://crawler:5000/api/crawl"  # Use the service name from docker-compose
                payload = {
                    'starting_url': starting_url,
                    'crawl_depth': crawl_depth,
                    'max_pages': max_pages,
                    'mongodb_collection': mongodb_collection
                }

                try:
                    async with session.post(crawler_url, json=payload) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.info(f"Crawler API response: {result}")

                            # Store job_id in session for status checking
                            request.session['crawler_job_id'] = result.get('job_id')

                            # Redirect to job status page
                            return redirect('crawler_job_status')
                        else:
                            error_text = await response.text()
                            logger.error(f"Crawler API error: {error_text}")
                            return render(request, 'source_wikipedia/crawl_error.html', {
                                'error': f"API returned status {response.status}: {error_text}",
                                'form': form
                            })
                except Exception as e:
                    logger.error(f"Exception calling crawler API: {str(e)}")
                    return render(request, 'source_wikipedia/crawl_error.html', {
                        'error': str(e),
                        'form': form
                    })
    else:
        form = WikipediaCrawlForm()

    return render(request, 'source_wikipedia/wikipedia_crawl.html', {'form': form})


async def crawler_job_status(request):
    """View to check the status of a crawler job"""
    job_id = request.session.get('crawler_job_id')

    if not job_id:
        return redirect('crawl_wikipedia')

    async with aiohttp.ClientSession() as session:
        crawler_url = f"http://crawler:5000/api/jobs/{job_id}"

        try:
            async with session.get(crawler_url) as response:
                if response.status == 200:
                    job_data = await response.json()

                    # If job is complete, show completion page
                    if job_data['status'] in ['completed', 'failed']:
                        return render(request, 'source_wikipedia/crawl_complete.html', {
                            'job': job_data
                        })

                    # Otherwise show status page with refresh
                    return render(request, 'source_wikipedia/crawl_status.html', {
                        'job': job_data
                    })
                else:
                    error_text = await response.text()
                    return render(request, 'source_wikipedia/crawl_error.html', {
                        'error': f"API returned status {response.status}: {error_text}"
                    })
        except Exception as e:
            return render(request, 'source_wikipedia/crawl_error.html', {
                'error': str(e)
            })


async def all_crawler_jobs(request):
    """View to list all crawler jobs"""
    async with aiohttp.ClientSession() as session:
        crawler_url = "http://crawler:5000/api/jobs"

        try:
            async with session.get(crawler_url) as response:
                if response.status == 200:
                    jobs_data = await response.json()
                    return render(request, 'source_wikipedia/crawl_jobs.html', {
                        'jobs': jobs_data['jobs']
                    })
                else:
                    error_text = await response.text()
                    return render(request, 'source_wikipedia/crawl_error.html', {
                        'error': f"API returned status {response.status}: {error_text}"
                    })
        except Exception as e:
            return render(request, 'source_wikipedia/crawl_error.html', {
                'error': str(e)
            })