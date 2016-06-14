# -*- coding: utf-8 -*-

import logging
import argparse
import tempfile
from datetime import datetime, timedelta
from .wayback import scrape_archives
from .scraper import Scraper

logger = logging.getLogger('waybackscraper')

CLI_DATE_FORMAT = '%Y-%m-%d'


def parse_args():
    parser = argparse.ArgumentParser(prog='waybackscraper', description='Scrape a website archives.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('website_url', help='The url of the website to scrape')

    # Archive minimum date defaults to 30 days ago
    default_max_date = datetime.now()
    default_min_date = default_max_date - timedelta(days=30)

    # Optional arguments
    parser.add_argument('-from', "--from_date", help="Ignore archives older than this date - format YYYY-MM-DD",
                        default=default_min_date.strftime(CLI_DATE_FORMAT))
    parser.add_argument('-to', "--to_date", help="Ignore archives newer than this date - format YYYY-MM-DD",
                        default=default_max_date.strftime(CLI_DATE_FORMAT))
    parser.add_argument("-x", "--xpath",
                        help="A xpath expression to use for the scraping. "
                             "If the expression matches images, the images are downloaded. "
                             "Otherwise the content of the elements matched is downloaded.")
    parser.add_argument("-c", "--concurrency", type=int, default=10,
                        help="Maximum number of concurrent requests to the wayback machine")
    parser.add_argument("-d", "--delta", type=int, default=1, help="Minimum number of days between two archives")
    parser.add_argument("-q", "--quiet", action="store_true", help="Don't print progress")
    parser.add_argument("-r", "--target-folder",
                        help="The folder where scraping results are stored (default: Temporary folder)")

    args = parser.parse_args()

    return args


def main():
    args = parse_args()

    logging.basicConfig(level=(logging.WARN if args.quiet else logging.INFO))

    # Don't allow more than 20 concurrent requests to the wayback machine
    concurrency = min(args.concurrency, 20)

    # Scrape results are stored in a temporary folder if no folder specified
    target_folder = args.target_folder if args.target_folder else tempfile.gettempdir()

    logger.info('Writing scrape results in the folder {target_folder}'.format(target_folder=target_folder))

    # Parse the minimum date entered by the user (throws an exception if the date is not correctly formatted)
    from_date = datetime.strptime(args.from_date, CLI_DATE_FORMAT)
    to_date = datetime.strptime(args.to_date, CLI_DATE_FORMAT)

    # The scraper downloads the elements matching the given xpath expression in the archives
    scraper = Scraper(target_folder, args.xpath)

    # Launch the scraping
    scrape_archives(args.website_url, scraper.scrape, from_date, to_date, timedelta(days=args.delta), concurrency)
