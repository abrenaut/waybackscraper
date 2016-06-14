# -*- coding: utf-8 -*-

import logging
import re
import asyncio
import aiohttp
import json
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from datetime import datetime
from .exceptions import ScrapeError

logger = logging.getLogger('waybackscraper.wayback')

WEB_ARCHIVE_CDX_TEMPLATE = "http://web.archive.org/cdx/search/cdx?{params}"
WEB_ARCHIVE_TIMESTAMP_FORMAT = '%Y%m%d%H%M%S'
WEB_ARCHIVE_URL = 'http://web.archive.org'
WEB_ARCHIVE_TEMPLATE = "http://web.archive.org/web/{timestamp}/{url}"


class Archive:
    """
    A website archive on the wayback machine
    """

    def __init__(self, timestamp, url):
        self.timestamp = timestamp
        self.date = datetime.strptime(timestamp, WEB_ARCHIVE_TIMESTAMP_FORMAT)
        self.url = WEB_ARCHIVE_TEMPLATE.format(timestamp=timestamp, url=url)


def scrape_archives(url, scrape_function, min_date, max_date, timedelta=None, concurrency=5):
    """
    Scrape the archives of the given URL.
    The min_date and start_date parameters allow to restrict the archives to a given period.
    A minimum time delta between two archives can be specified with the timedelta parameter.
    The concurrency parameter limits the number of concurrent connections to the web archive.
    """
    # Get the list of archive available for the given url
    archives = list_archives(url, min_date, max_date)

    # Filter the archives to keep only the one between min_date and max_date and to have a minimum timedelta between
    # each archive
    archives = [archive for archive in archive_delta_filter(archives, timedelta)]

    # Scrape each archives asynchronously and gather the results
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(run_scraping(archives, scrape_function, concurrency))
    result = loop.run_until_complete(future)

    return result


async def run_scraping(archives, scrape_function, concurrency):
    """
    Run the scraping function asynchronously on the given archives.
    The concurrency parameter limits the number of concurrent connections to the web archive.
    """
    # Use a semaphore to limit the number of concurrent connections to the web archive
    sem = asyncio.Semaphore(concurrency)

    # Create scraping tasks for each archive
    tasks = [scrape_archive(archive, scrape_function, sem) for archive in archives]

    # Gather each scraping result
    responses = await asyncio.gather(*tasks)

    # Compile each valid scraping results in a dictionary
    return {response[0]: response[1] for response in responses if response[1] is not None}


async def scrape_archive(archive, scrape_function, sem):
    """
    Download the archive and run the scraping function on the archive content.
    Returns a tuple containing the scraped archive and the result of the scraping. If the scraping failed, the result
    is None
    """
    scrape_result = None

    try:
        # Limit the number of concurrent connections
        with (await sem):
            logger.info('Scraping the archive {archive_url}'.format(archive_url=archive.url))

            # Download the archive content
            async with aiohttp.ClientSession() as session:
                async with session.get(archive.url) as response:
                    response = await response.read()

                    # Transform relative URLs in the archive into absolute URLs
                    response = to_absolute_urls(response, archive)

                    # Scrape the archive content
                    scrape_result = await scrape_function(archive, response)

    except ScrapeError as e:
        logger.warn('Could not scrape the archive {url} : {msg}'.format(url=archive.url, msg=str(e)))
    except HTTPError as e:
        logger.warn('Could not download the archive {url} : {msg}'.format(url=archive.url, msg=str(e)))
    except Exception as e:
        logger.exception('Error while scraping the archive {url}'.format(url=archive.url, msg=str(e)))

    return archive, scrape_result


def list_archives(url, min_date, max_date):
    """
    List the available archive between min_date and max_date for the given URL
    """
    logger.info('Listing the archives for the url {url}'.format(url=url))

    # Download the memento list
    parameters = {'url': url,
                  'output': 'json',
                  'from': min_date.strftime(WEB_ARCHIVE_TIMESTAMP_FORMAT),
                  'to': max_date.strftime(WEB_ARCHIVE_TIMESTAMP_FORMAT)}
    cdx_url = WEB_ARCHIVE_CDX_TEMPLATE.format(params=urlencode(parameters))
    req = Request(cdx_url, None, {'User-Agent': 'Mozilla/5.0'})
    memento_json = urlopen(req).read().decode("utf-8")

    # Parse the json response
    memento_list = json.loads(memento_json)

    # A row contains the following columns: "urlkey","timestamp","original","mimetype","statuscode","digest","length"
    archives = [Archive(archive[1], url) for archive in memento_list[1:] if archive[4] == '200']

    logger.info('Found {count} archives for the url {url}'.format(count=len(archives), url=url))

    return archives


def archive_delta_filter(archive_list, timedelta):
    """
    Make sure there is a minimum time delta between each archive
    """
    # Sort the list of archive by their date
    archive_list.sort(key=lambda x: x.date)

    # For each archive, make sure there is a minimum of days between the archive and the previous archive in the list
    prev_date = None
    for archive in archive_list:
        if timedelta is None or prev_date is None or archive.date - prev_date > timedelta:
            yield archive
            prev_date = archive.date


def to_absolute_urls(content, archive):
    """
    Preprend the Web Archive URL to each relative URLs found in the string passed as parameter and returns the result
    """
    root_pat = re.compile(('([\'"])(/web/' + archive.timestamp + ')').encode('utf-8'))
    content = re.sub(root_pat, (r"\1" + WEB_ARCHIVE_URL + r"\2").encode('utf-8'), content)
    return content
