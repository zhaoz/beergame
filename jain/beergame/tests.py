"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase
from django.test.client import Client

from beergame.models import Game, Team, Period

class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.failUnlessEqual(1 + 1, 2)

__test__ = {"doctest": """
Another way to test that 1 + 1 is equal to 2.

>>> 1 + 1 == 2
True
"""}


class GameTestCase(TestCase):
    def testCreateGame(self):
        """Test the creation of games"""
        game_name = 'test_game' 
        c = Client()
        response = c.post('/create_game', {'name': game_name})
        self.assertEquals(200, response.status_code)

        game_qs = Game.objects.filter(name=game_name)

        # get the current game object
        self.assertEquals(1, game_qs.count())

        # get teams

        teams_qs = Team.objects.filter(game__name=game_name)

        self.assertEquals(4, teams_qs.count())
