from django.forms import ModelForm

from beergame.models import Game

class GameForm(ModelForm):
    class Meta:
        model = Game

