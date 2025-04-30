from django import forms

class WikipediaCrawlForm(forms.Form):
    starting_url = forms.URLField(
        label="Starting URL",
        help_text="The Wikipedia page to start crawling from",
        widget=forms.URLInput(attrs={'class': 'form-control'})
    )
    crawl_depth = forms.IntegerField(
        label="Crawl Depth",
        help_text="How many links deep to crawl (1-5 recommended)",
        min_value=1,
        max_value=10,
        initial=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    mongodb_database = forms.CharField(
        label="MongoDB DB",
        help_text="Name of MongoDB DB",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    mongodb_collection = forms.CharField(
        label="MongoDB Collection",
        help_text="Name of MongoDB Collection",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    max_pages = forms.IntegerField(
        label="Maximum Pages",
        help_text="Maximum number of pages to crawl",
        min_value=1,
        max_value=100000,
        initial=20,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    elastic_index = forms.CharField(
        label="Elasticsearch Index",
        help_text="Index name for Elasticsearch (leave blank to use same as MongoDB collection)",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    batch_size = forms.IntegerField(
        label="Indexing Batch Size",
        help_text="Number of documents to index in each batch",
        min_value=10,
        max_value=1000,
        initial=100,
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )