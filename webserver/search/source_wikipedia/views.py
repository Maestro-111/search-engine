from django.http import HttpResponse
from django.shortcuts import render
from django.core.paginator import Paginator
from elasticsearch import Elasticsearch
from .utils.elastic_agent import QueryElastic
import os
from .forms import WikipediaCrawlForm
import logging

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

            starting_url = form.cleaned_data['starting_url']
            crawl_depth = form.cleaned_data['crawl_depth']
            max_pages = form.cleaned_data['max_pages']
            mongodb_collection = form.cleaned_data['mongodb_collection']

            logger.info(f"Starting crawl {starting_url} with depth {crawl_depth} and max_pages {max_pages}."
                        f"Going to  store the results in {mongodb_collection}")

            logger.info(f"Finished crawling {starting_url}.")


            return HttpResponse('Success!')
    else:
        form = WikipediaCrawlForm()

    return render(request, 'source_wikipedia/wikipedia_crawl.html', {'form': form})