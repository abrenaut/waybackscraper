# -*- coding: utf-8 -*-

import logging
import lxml.html
from urllib import parse
from os.path import join, basename

logger = logging.getLogger('waybackscraper.scraper')


class Scraper:
    def __init__(self, target_folder, xpath):
        """
        :param target_folder: The folder where scrape results are stored
        :param xpath: A xpath expression to use when scraping
        :return:
        """
        self.target_folder = target_folder
        self.xpath = xpath

    async def scrape(self, session, archive_url, archive_timestamp, archive_content):
        """
        If the scraper has no xpath attribute, the content of the archives is stored as is.
        If the scraper has a xpath attribute, store the matching elements in a file.
        If the matching elements are images, download the images.
        """
        result = ''

        timestamp_str = archive_timestamp.strftime("%Y%m%d%H%M%S")

        if self.xpath:
            # If a xpath expression is set, use it to filter the archive
            tree = lxml.html.fromstring(archive_content)
            matches = tree.xpath(self.xpath)

            if not matches:
                logger.warn(
                        "The expression '{xpath}' doesn't match any element in the archive {archive_url}".format(
                                xpath=self.xpath,
                                archive_url=archive_url))
            else:
                for match in matches:
                    # If the xpath expression matches an image, download it
                    if match.tag == 'img':
                        disassembled = parse.urlparse(match.get('src'))
                        filename = basename(disassembled.path)
                        target_file_path = join(self.target_folder, timestamp_str + filename)
                        await self.download_img(session, match.get('src'), target_file_path)
                    # Otherwise, add the element to the result
                    else:
                        result += lxml.html.tostring(match).decode('utf-8')
        else:
            # If no xpath expression, download the whole document
            result = archive_content

        # Store result of the scraping in a file
        if result:
            output_file_path = join(self.target_folder, timestamp_str + '.html')
            with open(output_file_path, 'w') as output_file:
                output_file.write(result)

    @staticmethod
    async def download_img(session, img_url, target_file_path):
        """
        Download an image asynchronously
        """
        # Stream the image content to a file
        async with session.get(img_url) as response:
            with open(target_file_path, 'wb') as target_file:
                async for chunk in response.content.iter_chunked(8192):
                    target_file.write(chunk)
