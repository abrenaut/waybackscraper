# Wayback scraper

Scrapes a website archives on [The Wayback Machine](https://archive.org/web/) using Python's asyncio.

## Prerequisites

This project requires Python >= 3.5

## Installing 

To install, simply:
 
    pip install waybackscraper

To download one archive per year of google.com between 2000 and 2005:

    waybackscraper "http://google.com" -d 365 -from 2000-01-01 -to 2005-01-01

To download the comics previously featured on Cyanide and Happiness:

    waybackscraper "http://explosm.net" -x "//img[@id=\"featured-comic\"]"
   
![C&H](https://raw.githubusercontent.com/abrenaut/waybackscraper/master/cyanide.jpg)
    
## Developing

To download the project:

    git clone https://github.com/abrenaut/waybackscraper.git
    cd waybackscraper
    
To download dependencies:
    
    python setup.py install

## Features

* Download the archive of a Website using [The Wayback Machine](https://archive.org/web/)
* Filter the downloaded archive using xpath expressions
* If the xpath expression match images, download the images
    
## Usage
    
    usage: waybackscraper [-h] [-f FROM] [-t TO] [-x XPATH] [-c CONCURRENCY]
                          [-d DELTA] [-q] [-r TARGET_FOLDER]
                          website_url
    
    Scrape a website archives.
    
    positional arguments:
      website_url           The url of the website to scrape
    
    optional arguments:
      -h, --help            show this help message and exit
      -f FROM, --from FROM  Filter archives older than this date - format YYYY-MM-
                            DD (default: 30 days ago)
      -t TO, --to TO        Filter archives newer than this date - format YYYY-MM-
                            DD (default: today)
      -x XPATH, --xpath XPATH
                            A xpath expression to use for the scraping. If the
                            expression matches images, the images are downloaded.
                            Otherwise the content of the elements matched is
                            downloaded. (default: None)
      -c CONCURRENCY, --concurrency CONCURRENCY
                            Maximum number of concurrent requests to the wayback
                            machine (default: 2)
      -d DELTA, --delta DELTA
                            Minimum number of days between two archives (default:
                            1)
      -q, --quiet           Don't print progress (default: False)
      -r TARGET_FOLDER, --target-folder TARGET_FOLDER
                            The folder where scraped images are stored (default:
                            Temporary folder) (default: None)
      -u USER_AGENT, --user-agent USER_AGENT
                            The user agent used when querying the Internet Archive
                            (default: waybackscraper)                            