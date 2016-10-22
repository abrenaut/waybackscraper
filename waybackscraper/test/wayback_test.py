# -*- coding: utf-8 -*-

import unittest
import os
from datetime import datetime, timedelta
from waybackscraper import wayback


class TestWayback(unittest.TestCase):
    def test_list_archives_timestamp(self):
        """
        Extract a list of memento timestamps from the resources/memento_list.txt file
        """
        # Mock the memento URL
        wayback.WEB_ARCHIVE_CDX_TEMPLATE = 'file://' + os.path.abspath('resources/memento_list.json')

        # List the snapshot found in the test memento
        timestamps = wayback.list_archive_timestamps('', datetime(2015, 1, 1), datetime(2017, 1, 1), '')

        self.assertEquals(len(timestamps), 840)

    def test_timedelta_filter(self):
        """
        Test the function that makes sure there is a minimum time delta between each date in the given list
        """
        dates = [datetime(2016, 1, 1), datetime(2016, 1, 25), datetime(2016, 1, 15), datetime(2016, 1, 31)]

        filtered_dates = [archive for archive in wayback.timedelta_filter(dates, timedelta(days=16))]

        self.assertEqual(filtered_dates, [datetime(2016, 1, 1), datetime(2016, 1, 25)])

    def test_to_absolute_urls(self):
        """
        Test the function which prepends the Web Archive URL to each URLs found in a string
        """
        archive_timestamp = datetime(2016, 3, 12, 14, 8, 2)
        archive_content = '<img src="/web/20160312140802im_/test.jpg">'

        archive_content = wayback.to_absolute_urls(archive_content, archive_timestamp)

        self.assertEquals(archive_content, '<img src="' + wayback.WEB_ARCHIVE_URL + '/web/20160312140802im_/test.jpg">')
