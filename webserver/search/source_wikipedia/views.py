from django.shortcuts import render
from django.core.paginator import Paginator
from elasticsearch import Elasticsearch
from .utils.elastic_agent import QueryElastic
import os


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