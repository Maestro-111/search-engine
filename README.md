# Search Engine App

## Abstract

This project is a scalable search engine system with web crawling, data indexing, and a web interface.
It's built using a microservices architecture with Docker Compose for easy deployment.

You can also use local k8s cluster (like minikube) to deploy the app.
You can index existing data sources (whatever is available on the menu tab) or upload your own data source (tbd)

![Project Introduction](icons/intro.gif)

## Architecture 

**Web Crawling**: We use Scrapy for Crawling. Crawling module is wrapped into fast api app for http requests from webserver. Scrapy will save the found docs in Mongo DB.

**Indexing**: We use ElasticSearch to index documents from Mongo DB. 

**Webserver**: UI tool built with Django/Celery to monitor/schedule crawling job/ search elastic.

We use LLM (gpt-4) to break down the request to search engine from user into entities and pass them to elastic client for more accurate mapping.



## Set up with Docker

1. Clone the repository

```shell
git clone https://github.com/yourusername/search-engine.git
cd search-engine
```

2. Run Makefile commands

```shell
# for local dev
make local build up

#for prod dev
make prod build up
```


## TO DO:


1) how to rank elastic response?
    1) first elastic ranks by additional fields
    2) then, use learn-to rank (collect user metadata like clicks) and train on top of that
2) unit testing for django (webserver)
3) CI (cont)
4) Custom source for indexing (cont)
5) k8s file for GKE
6) configure help for easier k8s app run 
7) configure jobs for k8s to run crawl/index on schedule
8) dotabuff match simulator (cont)