from django.db import models

class Game(models.Model):
    date_started = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=40, unique=True)

    def __unicode__(self):
        return self.name

class Team(models.Model):
    ROLE_CHOICES = (
                        ('Factory','Factory'),
                        ('Distributor','Distributor'),
                        ('Wholesaler','Wholesaler'),
                        ('Retailer','Retailer')
                    )

    BUTTONS = (
                    ('start','start'),
                    ('step1','step1'),
                    ('step2','step2'),
                    ('ship','ship'),
                    ('step3','step3'),
                    ('order','order'),
                    ('none','none')
                )

    game = models.ForeignKey(Game)
    role = models.CharField(max_length=12, choices=ROLE_CHOICES)
    last_completed_period = models.IntegerField(default=0)
    last_clicked_button = models.CharField(max_length=12, choices=BUTTONS) 

    def save(self, *args, **kwargs):
        ret = super(self.__class__, self).save(*args, **kwargs)
        Period(team=self).save()

        return ret

    def __unicode__(self):
        return "%s playing in %s" % (self.role, self.game.name)

class Period(models.Model):
    team = models.ForeignKey(Team)
    number = models.IntegerField(default=0)
    inventory = models.IntegerField(default=12)
    backlog = models.IntegerField(default=0)
    demand = models.IntegerField(blank=True, null=True)
    order_1 = models.IntegerField(blank=True, null=True, default=4)
    order_2 = models.IntegerField(blank=True, null=True, default=4)
    shipment_1 = models.IntegerField(blank=True, null=True, default=4)
    shipment_2 = models.IntegerField(blank=True, null=True, default=4)
    shipped = models.IntegerField(blank=True, null=True)
    cost = models.DecimalField(max_digits=8, decimal_places=2, default='0.00')
    cumulative_cost = models.DecimalField(max_digits=8, decimal_places=2, default='0.00')
    order = models.IntegerField(blank=True, null=True, default=0)

    def __unicode__(self):
        return "%d / %s / %s" % (self.number, self.team.role, self.team.game.name)
