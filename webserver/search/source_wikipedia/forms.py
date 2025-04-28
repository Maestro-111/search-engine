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

    mongodb_collection = forms.CharField(
        label="MongoDB Collection",
        help_text="Name of MongoDB Collection",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    max_pages = forms.IntegerField(
        label="Maximum Pages",
        help_text="Maximum number of pages to crawl",
        min_value=1,
        max_value=100,
        initial=20,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )