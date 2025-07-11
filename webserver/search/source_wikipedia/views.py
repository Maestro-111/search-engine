from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import WikipediaCrawlForm
from .models import CrawlJob, IndexJob
from common_utils.tasks import run_crawl_job
from .utils.elastic_wiki import WikipediaElastic
import logging
from django.core.cache import cache
from django.http import JsonResponse


logger = logging.getLogger("webserver")


def wiki_search(request):

    query = ""
    results = []

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    es = WikipediaElastic(logger)

    if request.method == "POST":
        query = request.POST.get("query", "")
    elif request.method == "GET":
        query = request.GET.get("query", "")

    if query:
        cache_key = f"wiki_elasticsearch_results:{query}"
        raw_results = cache.get(cache_key)
        if raw_results is None:

            prompt = es.generate_prompt_wiki(query)
            entities = es.extract_entities_with_openai(prompt)
            search_body = es.build_elasticsearch_query_wiki(entities)

            raw_results = es.query_specified_fields(
                search_body=search_body, index="wikipedia"
            )
            cache.set(cache_key, raw_results, 3600)

        paginator = Paginator(raw_results, 10)
        page_number = request.GET.get("page", 1)
        results = paginator.get_page(page_number)

    if is_ajax:

        # Return JSON response for AJAX requests

        result_data = []

        for result in results:
            result_data.append(
                {
                    "title": result["title"],
                    "url": result["url"],
                    "excerpt": result["excerpt"],
                    "categories": list(result["categories"]),
                    "last_updated": str(result["last_updated"]),
                }
            )

        return JsonResponse(
            {
                "query": query,
                "results": result_data,
                "has_next": results.has_next(),  # type: ignore
                "has_previous": results.has_previous(),  # type: ignore
                "page_number": results.number,  # type: ignore
                "num_pages": results.paginator.num_pages,  # type: ignore
            }
        )

    context = {"query": query, "results": results}
    return render(request, "source_wikipedia/wikipedia_search.html", context)


def wiki_crawl(request):
    if request.method == "POST":
        form = WikipediaCrawlForm(request.POST)
        if form.is_valid():

            starting_url = form.cleaned_data["starting_url"]
            crawl_depth = form.cleaned_data["crawl_depth"]
            max_pages = form.cleaned_data["max_pages"]
            mongodb_database = form.cleaned_data["mongodb_database"]
            mongodb_collection = form.cleaned_data["mongodb_collection"]
            spider_name = "wikipedia_spider"

            elastic_index = form.cleaned_data["elastic_index"]
            batch_size = form.cleaned_data["batch_size"]

            # Log the request
            logger.info(
                f"Starting Wiki crawl {starting_url} with depth {crawl_depth} and max_pages {max_pages}. "
                f"Going to store the results in db called {mongodb_database} in {mongodb_collection}"
            )

            crawl_job = CrawlJob.objects.create(
                status="queued",
                starting_url=starting_url,
                crawl_depth=crawl_depth,
                max_pages=max_pages,
                mongodb_collection=mongodb_collection,
                mongodb_db=mongodb_database,
                spider_name=spider_name,
            )

            index_job = IndexJob.objects.create(
                mongodb_db=mongodb_database,
                mongodb_collection=mongodb_collection,
                elastic_index=elastic_index,
                batch_size=batch_size,
                crawl_job=crawl_job,
            )

            logger.info(f"Created 2 job objects {crawl_job}, {index_job}")

            run_crawl_job.delay(crawl_job.id)

            messages.success(
                request, "Wiki Crawl/Index job has been submitted successfully."
            )
            return redirect("wiki_crawler_job_status", job_id=crawl_job.id)
    else:
        form = WikipediaCrawlForm()

    return render(request, "source_wikipedia/wikipedia_crawl.html", {"form": form})


def wiki_crawler_job_status(request, job_id):
    """View to check the status of a crawler job"""

    try:
        job = CrawlJob.objects.get(id=job_id)
        return render(
            request, "source_wikipedia/wikipedia_crawl_status.html", {"job": job}
        )
    except CrawlJob.DoesNotExist:
        messages.error(request, "Job not found.")
        return redirect("wiki_crawl")


def wiki_remove_job(request, job_id):
    """Remove a crawler job"""

    if request.method == "POST":  # Require POST for deletion (security best practice)
        crawl_job = get_object_or_404(CrawlJob, id=job_id)
        job_id = crawl_job.id  # Save ID for message

        if hasattr(crawl_job, "index_jobs"):
            crawl_job.index_jobs.all().delete()

        logger.info(f"Removing crawler job {job_id}.")

        crawl_job.delete()
        messages.success(request, f"Crawler job #{job_id} has been deleted.")

    return redirect("wiki_all_crawler_jobs")


def wiki_all_crawler_jobs(request):
    """View to list all crawler jobs"""

    jobs = CrawlJob.objects.filter(spider_name="wikipedia_spider").order_by(
        "-created_at"
    )
    paginator = Paginator(jobs, 10)  # 10 jobs per page

    page_number = request.GET.get("page", 1)
    jobs_page = paginator.get_page(page_number)

    return render(
        request, "source_wikipedia/wikipedia_crawl_jobs.html", {"jobs": jobs_page}
    )
