# -*- coding: utf-8 -*-

import logging
import re
import asyncio
import aiohttp
import json
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from .exceptions import ScrapeError

logger = logging.getLogger('waybackscraper.wayback')

WEB_ARCHIVE_CDX_TEMPLATE = "http://web.archive.org/cdx/search/cdx?{params}"
WEB_ARCHIVE_TIMESTAMP_FORMAT = '%Y%m%d%H%M%S'
WEB_ARCHIVE_URL = 'http://web.archive.org'
WEB_ARCHIVE_TEMPLATE = "http://web.archive.org/web/{timestamp}/{url}"


def scrape_archives(url, scrape_function, min_date, max_date, user_agent, min_timedelta=None, concurrency=5):
    """
    Scrape the archives of the given URL.
    The min_date and start_date parameters allow to restrict the archives to a given period.
    A minimum time delta between two archives can be specified with the timedelta parameter.
    The concurrency parameter limits the number of concurrent connections to the web archive.
    """
    # Get the list of archive available for the given url
    archive_timestamps = list_archive_timestamps(url, min_date, max_date, user_agent)

    # Filter the timestamps to have a minimum timedelta between each timestamp
    if min_timedelta and len(archive_timestamps):
        archive_timestamps = timedelta_filter(archive_timestamps, min_timedelta)

    loop = asyncio.get_event_loop()

    # Scrape each archives asynchronously and gather the results
    scraping_task = loop.create_task(run_scraping(url, archive_timestamps, scrape_function, concurrency, user_agent))

    try:
        loop.run_until_complete(scraping_task)
    finally:
        loop.close()

    return scraping_task.result()


async def run_scraping(url, timestamps, scrape_function, concurrency, user_agent):
    """
    Run the scraping function asynchronously on the given archives.
    The concurrency parameter limits the number of concurrent connections to the web archive.
    """
    # Use a semaphore to limit the number of concurrent connections to the internet archive
    sem = asyncio.Semaphore(concurrency)

    # Use one session to benefit from connection pooling
    async with aiohttp.ClientSession(headers={'User-Agent': user_agent}) as session:
        # Create scraping coroutines for each archive
        coroutines = [scrape_archive(session, url, timestamp, scrape_function, sem) for timestamp in timestamps]

        # Wait for coroutines to finish and gather the results
        results = await asyncio.gather(*coroutines)

    # Compile each valid scraping results in a dictionary
    return {timestamp: result for timestamp, result in results if result is not None}


async def scrape_archive(session, url, archive_timestamp, scrape_function, sem):
    """
    Download the archive and run the scraping function on the archive content.
    Returns a tuple containing the scraped archive and the result of the scraping. If the scraping failed, the result
    is None
    """
    scraping_result = None

    # Limit the number of concurrent connections
    with (await sem):
        archive_url = get_archive_url(url, archive_timestamp)

        logger.info('Scraping the archive {archive_url}'.format(archive_url=archive_url))

        # Download the archive content
        async with session.get(archive_url) as response:
            try:
                archive_content = await response.text(encoding="utf-8")

                # Transform relative URLs in the archive into absolute URLs
                archive_content = to_absolute_urls(archive_content, archive_timestamp)

                # Scrape the archive content
                scraping_result = await scrape_function(session, archive_url, archive_timestamp, archive_content)
            except ScrapeError as e:
                logger.warn('Could not scrape the archive {url} : {msg}'.format(url=archive_url, msg=str(e)))
            except HTTPError as e:
                logger.warn('Could not download the archive {url} : {msg}'.format(url=archive_url, msg=str(e)))
            except Exception as e:
                logger.exception('Error while scraping the archive {url} : {msg}'.format(url=archive_url, msg=str(e)))

    return archive_timestamp, scraping_result


def list_archive_timestamps(url, min_date, max_date, user_agent):
    """
    List the available archive between min_date and max_date for the given URL
    """
    logger.info('Listing the archives for the url {url}'.format(url=url))

    # Construct the URL used to download the memento list
    parameters = {'url': url,
                  'output': 'json',
                  'from': min_date.strftime(WEB_ARCHIVE_TIMESTAMP_FORMAT),
                  'to': max_date.strftime(WEB_ARCHIVE_TIMESTAMP_FORMAT)}
    cdx_url = WEB_ARCHIVE_CDX_TEMPLATE.format(params=urlencode(parameters))

    req = Request(cdx_url, None, {'User-Agent': user_agent})
    with urlopen(req) as cdx:
        memento_json = cdx.read().decode("utf-8")

        timestamps = []
        # Ignore the first line which contains column names
        for url_key, timestamp, original, mime_type, status_code, digest, length in json.loads(memento_json)[1:]:
            # Ignore archives with a status code != OK
            if status_code == '200':
                timestamps.append(datetime.strptime(timestamp, WEB_ARCHIVE_TIMESTAMP_FORMAT))

    return timestamps


def timedelta_filter(dates, timedelta):
    """
    Make sure there is a minimum time delta between each date in the given list
    """
    filtered_dates = [dates[0]]
    for date in sorted(dates[1:]):
        if date - filtered_dates[-1] > timedelta:
            filtered_dates.append(date)
    return filtered_dates


def to_absolute_urls(content, archive_timestamp):
    """
    Preprend the Web Archive URL to each relative URLs found in the string passed as parameter and returns the result
    """
    root_pat = re.compile(('([\'"])(/web/' + archive_timestamp.strftime(WEB_ARCHIVE_TIMESTAMP_FORMAT) + ')'))
    content = re.sub(root_pat, r"\1" + WEB_ARCHIVE_URL + r"\2", content)
    return content


def get_archive_url(url, timestamp):
    """
    Returns the archive url for the given url and timestamp
    """
    return WEB_ARCHIVE_TEMPLATE.format(timestamp=timestamp.strftime(WEB_ARCHIVE_TIMESTAMP_FORMAT), url=url)
