from unittest import TestCase

from horseracing.math import resolveBetValue, oddsToDecimal, previewCalc

class MathTest(TestCase):
    def test_single_win_value_resolution(self):
        # Single Win resolution
        
        place = 1
        stake = 10
        odds = "2:1"
        eachWay = 0

        result = resolveBetValue(place,stake,odds,eachWay)

        self.assertEqual(result, 30.0)

    def test_each_way_win_value_resolution(self):
        # Each-way Win resolution
        
        place = 1
        stake = 10
        odds = "2:1"
        eachWay = 1

        result = resolveBetValue(place,stake,odds,eachWay)

        self.assertEqual(result, 44.0)

    def test_each_way_place_resolution(self):
        # Each-way Place resolution
        
        place = 2
        stake = 10
        odds = "2:1"
        eachWay = 1

        result = resolveBetValue(place,stake,odds,eachWay)

        self.assertEqual(result, 14.0)

    def test_no_win_value_resolution(self):
        # No-win resolution
        
        place = 4
        stake = 10
        odds = "2:1"
        eachWay = 1

        result = resolveBetValue(place,stake,odds,eachWay)

        self.assertEqual(result, 0)