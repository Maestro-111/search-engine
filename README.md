# Search Engine App.

## Abstract

This project is a scalable search engine system with web crawling, data indexing, and a web interface. 
It's built using a microservices architecture with Docker Compose for easy deployment.

## Architecture 

## Set up

1. Clone the repository

```shell
git clone https://github.com/yourusername/search-engine.git
cd search-engine
```

2. Install Poetry

```shell
# For Linux/macOS
curl -sSL https://install.python-poetry.org | python3 -

# For Windows
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

3. Run Makefile commands

```shell
# for local dev
make local build up

#for prod dev
make prod build up
```


## TO DO:

1) ngnix for load balance 
2) wiki app (cont)
3) better design for menu app (cont - home tab spacing)
4) elastic query class (implement query_specified_fields method)
5) rewise how crawling - indexing - search pipeline should look like (cont)
6) add celery
7) add postgres sql
8) add "custom data source" option
