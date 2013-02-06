"""
Test contents of HTTP_RESPONSE_CODES value dictionary
"""

import os,re
import unittest
from jsontester.responsecodes import HTTP_RESPONSE_CODES,response_code_text

class test_responsecodes(unittest.TestCase):
    def test_response_code_keys(self):
        for item in HTTP_RESPONSE_CODES.keys():
            self.assertIsInstance(item,int)
            self.assertTrue(item>0)
            self.assertTrue(item<600)

    def test_response_code_values(self):
        unique_values = []
        for item in HTTP_RESPONSE_CODES.values():
            self.assertIsInstance(item,basestring)
            self.assertTrue(item not in unique_values)
            unique_values.append(item)

    def test_response_code_lookup(self):
        for code,value in HTTP_RESPONSE_CODES.items():
            self.assertEquals(response_code_text(code),value)

suite = unittest.TestLoader().loadTestsFromTestCase(test_responsecodes)

