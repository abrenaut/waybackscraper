# -*- coding: utf-8 -*-

import unittest
import os
from datetime import datetime, timedelta
from waybackscraper import wayback


class TestWayback(unittest.TestCase):
    def test_list_snapshots(self):
        """
        Extract a list of memento from the resources/memento_list.txt file
        """
        # Mock the memento URL
        wayback.WEB_ARCHIVE_CDX_TEMPLATE = 'file://{memento_list}'.format(
                memento_list=os.path.abspath('resources/memento_list.json'))

        # List the snapshot found in the test memento
        snapshots = wayback.list_archives('', datetime(2015, 1, 1, 0, 0),
                                          datetime(2017, 1, 1, 0, 0), '')

        self.assertEquals(len(snapshots), 840)

    def test_next_date_with_offset(self):
        """
        Test the function that filters a list of archive to keep the one matching the given criteria
        """
        archives = [
            wayback.Archive('201601010000', ''),
            wayback.Archive('201601050000', ''),
            wayback.Archive('201601070000', ''),
            wayback.Archive('201601100000', '')
        ]

        filtered_archives = [archive for archive in wayback.archive_delta_filter(archives, timedelta(days=2))]

        self.assertEqual([archive.date for archive in filtered_archives],
                         [datetime(2016, 1, 1, 0, 0), datetime(2016, 1, 5, 0, 0), datetime(2016, 1, 10, 0, 0)])


    def test_to_absolute_urls(self):
        """
        Test the function which prepends the Web Archive URL to each URLs found in a string
        """
        archive = wayback.Archive('20160312140802', '')
        archive_content = '<img id="featured-comic" src="/web/20160312140802im_/http://files.explosm.net/comics/lunarbabboon_02.jpg">'.encode(
            'utf-8')

        archive_content = wayback.to_absolute_urls(archive_content, archive)

        self.assertEquals(archive_content.decode('utf-8'),
                          '<img id="featured-comic" src="' + wayback.WEB_ARCHIVE_URL + '/web/20160312140802im_/http://files.explosm.net/comics/lunarbabboon_02.jpg">')
