# Create your views here.
from datetime import datetime, timedelta
import json

from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse
from django.db.models import F

from django.forms.models import modelformset_factory

from beergame.models import Game, Team, Period
from beergame.forms import GameForm
from jain import settings


def start(request):
    # grab games started in the last hour
    hour_before = datetime.now() - timedelta(hours=72) 
    games = Game.objects.filter(date_started__gt=hour_before)

    return render_to_response('start.html', 
                                {
                                    'games': games,
                                },
                                context_instance=RequestContext(request))

def create_game(request):
    req = request.POST.copy()

    game = Game(name=req['name'])
    game.save()

    # create teams
    for role in Team.ROLE_CHOICES:
        Team(game=game, role=role[0], last_clicked_button='none').save()
    
    return render_to_response('create_game.html', {'game': game})

def join_game(request, game):
    game = get_object_or_404(Game, pk=game)

    roles = Team.ROLE_CHOICES 
    return render_to_response('join_game.html', {'game':game,'roles':roles}) 

def game(request, game, role):
    game = get_object_or_404(Game, pk=game)

    # get team
    # team = Team.objects.filter(game=game).filter(role=role)
    team = get_object_or_404(Team, game=game, role=role)

    try:
        period = Period.objects.filter(team=team).order_by('-number')[0]

    # should never happen
    # TODO throw an error
    except Period.DoesNotExist:
        # new game at period 0
        period = 0

    if team.last_clicked_button in ['step3', 'order', 'none']:
        period_range = 0 
    else:
        period_range = 1 

    # if second period, last completed would be 1 so [0:1] which returns only second period
    all_periods = Period.objects.filter(team=team).exclude(number=0).order_by('-number')[period_range:]

    return render_to_response('game.html', {
                                            'game': game,
                                            'role': role,
                                            'period': period,
                                            'all_periods':all_periods,
                                            'display_orders':settings.DISPLAY_ORDERS,
                                            })

def _get_period(game, role, period):
    #game = get_object_or_404(Game, pk=game)
    team = get_object_or_404(Team, game=game, role=role)
    return Period.objects.filter(team=team).get(number=int(period))

def _set_period_value(game, role, period, field, val):
    period = _get_period(game, role, period)
    setattr(period, field, val)
    period.save()

def ajax(request, game, role):
    game = get_object_or_404(Game, pk=game)
    
    data = request.REQUEST.copy()

    if data.has_key('period') and data.has_key('get'):
        
        period = _get_period(game, role, data['period']) 

        try:
            value = getattr(period, data['get'])
        except KeyError, ex:
            return HttpResponse(json.dumps({'error': 'attribute does not exist'}),
                        mimetype='text/javascript')
        return HttpResponse(json.dumps({data['get']:value, 'display_orders':settings.DISPLAY_ORDERS}),
                mimetype='text/javascript')

    elif data.has_key('period') and data.has_key('check'):
        if data['check'] == 'teams_ready':
            teams = Team.objects.filter(game=game)
            for team in teams:
                if team.last_completed_period != int(data['period']):
                    return HttpResponse(json.dumps({'teams_ready':False}),
                            mimetype='text/javascript')
            return HttpResponse(json.dumps({'teams_ready':True}),
                        mimetype='text/javascript')

        elif data['check'] == 'can_ship':
            if role == 'Retailer':
                return HttpResponse(json.dumps({'can_ship':True}),
                        mimetype='text/javascript')

            downstream_roles = {'Factory':'Distributor',
                                'Distributor':'Wholesaler',
                                'Wholesaler':'Retailer'}

            team = get_object_or_404(Team, game=game, role=downstream_roles[role])   
            period = Period.objects.filter(team=team).order_by('-number')[0]

            if period.shipment_2 == None:
                return HttpResponse(json.dumps({'can_ship':True}),
                        mimetype='text/javascript')

            return HttpResponse(json.dumps({'can_ship':False}),
                     mimetype='text/javascript')

        elif data['check'] == 'can_order':
            if role == 'Factory':
                return HttpResponse(json.dumps({'can_order':True}),
                        mimetype='text/javascript')

            upstream_roles = {'Distributor':'Factory',
                                'Wholesaler':'Distributor',
                                'Retailer':'Wholesaler'}

            team = get_object_or_404(Team, game=game, role=upstream_roles[role])   

            #if team.last_completed_period != (int(data['period'])-1):
            #    return HttpResponse(json.dumps({'error':'period inconsistency'}),
            #            mimetype='text/javascript')

            try:
                period = Period.objects.filter(team=team).filter(number=int(data['period']))[0] 
                return HttpResponse(json.dumps({'can_order':period.order_2 == None}),
                        mimetype='text/javascript')

            # other team hasn't started period yet
            except IndexError:
                return HttpResponse(json.dumps({'can_order': False}),
                        mimetype='text/javascript')

        return HttpResponse(json.dumps({'error': 'check argument not valid'}),
                    mimetype='text/javascript')

    elif data.has_key('query'):
        if data['query'] == 'last_clicked':
            team = get_object_or_404(Team, game=game, role=role) 
            return HttpResponse(json.dumps({'last_clicked':team.last_clicked_button}),
                     mimetype='text/javascript')

        return HttpResponse(json.dumps({'error': 'query argument not valid'}),
                    mimetype='text/javascript')

    elif data.has_key('set') and data.has_key('value'):
        team = get_object_or_404(Team, game=game, role=role)
        if data['set'] == 'last_clicked':

            def in_tuple(val, tuple):
                for tup in tuple:
                    if val in tup:
                        return True
                return False

            if in_tuple(data['value'], Team.BUTTONS):
                team.last_clicked_button = data['value']
                team.save()
                return HttpResponse(json.dumps({'success':'set last clicked button'}),
                        mimetype='text/javascript')
            else:
                return HttpResponse(json.dumps({'error':'button name does not exist'}),
                        mimetype='text/javascript')
        return HttpResponse(json.dumps({'error':'set argument does not exist'}),
                    mimetype='text/javascript')

    elif data.has_key('step') and data.has_key('period'): 
        team = get_object_or_404(Team, game=game, role=role)
        # start
        if data['step'] == 'start':
            per = int(data['period'])
            latest_period = Period.objects.filter(team=team).order_by('-number')[0]

            # check for consistency
            if latest_period.number != per:
                return HttpResponse(json.dumps({'error':'periods are incorrect'}),
                        mimetype='text/javascript')

            next_per = per+1 

            period = Period(team=team, number=next_per,
                        inventory=latest_period.inventory, backlog=latest_period.backlog, 
                        order_1=latest_period.order_1, order_2=latest_period.order_2, 
                        shipment_1=latest_period.shipment_1, shipment_2=latest_period.shipment_2, 
                        cumulative_cost=latest_period.cumulative_cost)
            period.save()
            
            return HttpResponse(json.dumps({'success':'completed start step'}),
                        mimetype='text/javascript')

        # step 1
        if data['step'] == 'step1':
            #_set_period_attr(game, role, int(data['period']), 
            #                    'shipment_1', int(data['shipment1'])) 
            period = Period.objects.filter(team=team).order_by('-number')[0]

            # check for consistency
            if period.number != int(data['period']):
                return HttpResponse(json.dumps({'error':'periods are incorrect'}),
                        mimetype='text/javascript')

            period.inventory = period.inventory + period.shipment_1
            period.shipment_1 = period.shipment_2
            period.shipment_2 = None

            period.save()

            return HttpResponse(json.dumps({'success':'completed step 1'}),
                    mimetype='text/javascript')

        elif data['step'] == 'step2':
            period = Period.objects.filter(team=team).order_by('-number')[0]

            # check for consistency
            if period.number != int(data['period']):
                return HttpResponse(json.dumps({'error':'periods are incorrect'}),
                        mimetype='text/javascript')

            period.demand = period.order_1
            period.order_1 = period.order_2
            period.order_2 = None

            if role == 'Retailer':
                per_num = int(data['period'])
                if per_num < 3:
                    period.order_2 = 4 
                else:
                    period.order_2 = 8

            period.save()

            return HttpResponse(json.dumps({'step2':period.demand}),
                    mimetype='text/javascript')

        elif data['step'] == 'step3':
            team = Team.objects.filter(game=game).filter(role=role)
            all_periods = Period.objects.filter(team=team).exclude(number=0).order_by('-number')
            return render_to_response('period_table.html', {'all_periods':all_periods}) 
             
    elif data.has_key('shipment') and data.has_key('period'):
        # TODO test whether can_ship is true

        shipment = int(data['shipment'])

        downstream_roles = {'Factory':'Distributor',
                            'Distributor':'Wholesaler',
                            'Wholesaler':'Retailer'}

        team = get_object_or_404(Team, game=game, role=role) 
        period = Period.objects.filter(team=team).order_by('-number')[0]

        # check for consistency
        if period.number != int(data['period']):
            return HttpResponse(json.dumps({'error':'periods are incorrect'}),
                    mimetype='text/javascript')

        if role != 'Retailer':
            downstream = get_object_or_404(Team, game=game, role=downstream_roles[role])   
            #downstream_period = Period.objects.filter(team=downstream).order_by('-number')[0]
            try:
                downstream_period = Period.objects.filter(team=downstream).filter(number=int(data['period']))[0]
            except KeyError:
                return HttpResponse(json.dumps({'error':'periods are incorrect'}),
                    mimetype='text/javascript')
                
            downstream_period.shipment_2 = shipment 
            downstream_period.save()

        period.shipped = shipment 

        # reduce inventory
        if period.inventory >= shipment:
            period.inventory = period.inventory - shipment 
        else:
            return HttpResponse(json.dumps({'error':'cannot ship more than inventory amount'}),
                    mimetype='text/javascript')

        from decimal import Decimal
        # handle backlog
        if shipment < period.demand:
            backlog = period.demand - shipment
            period.backlog = period.backlog + backlog
            period.cost = period.cost + Decimal(str(period.backlog)) 

        # reduce backlog if more sent
        if shipment > period.demand:
            if period.backlog != 0:
                period.backlog = period.backlog - (shipment - period.demand)

        # inventory costs
        period.cost = period.cost + Decimal(str(period.inventory * .5))

        # total costs
        period.cumulative_cost = period.cumulative_cost + period.cost

        period.save()

        return HttpResponse(json.dumps({'success':'shipped %d' % shipment}),
                mimetype='text/javascript')

    elif data.has_key('order') and data.has_key('period'):
        order = int(data['order'])
        team = get_object_or_404(Team, game=game, role=role)

        period = Period.objects.filter(team=team).order_by('-number')[0] 
        period.order = order 
        period.save()

        upstream_roles = {'Distributor':'Factory',
                            'Wholesaler':'Distributor',
                            'Retailer':'Wholesaler'}

        if role == 'Factory':
            period.shipment_2 = order
            period.save()

        else: 
            upstream = get_object_or_404(Team, game=game, role=upstream_roles[role])
            upstream_period = Period.objects.filter(team=upstream).order_by('-number')[0]
            upstream_period.order_2 = order
            upstream_period.save()

        team.last_completed_period = int(data['period'])
        team.save()

        return HttpResponse(json.dumps({'success':'ordered %d' % order}),
                    mimetype='text/javascript')

    elif data.has_key('html'):
        if data['html'] == 'period_table':
            team = Team.objects.filter(game=game).filter(role=role)
            all_periods = Period.objects.filter(team=team).exclude(number=0).order_by('-number')
            return render_to_response('period_table.html', {'all_periods':all_periods}) 

    else:
        return HttpResponse(json.dumps({'error': 'missing required arguments'}),
                    mimetype='text/javascript')

# admin views
def cp(request):
    games = Game.objects.all()
        
    return render_to_response('cp.html',    {
                                                'months': xrange(1,13),
                                                'days': xrange(1,32),
                                                'years': xrange(2009,2010),
                                                'hours': xrange(1, 13),
                                                'minutes': ['00','15','30','45'],
                                                'now': datetime.now(),
                                                'games': games,
                                                'game_form': GameForm(),
                                            })

def get_chart(request):
    data = request.REQUEST.copy()
    if data.has_key('id'):
        game = get_object_or_404(Game, pk=data['id'])
        teams = Team.objects.filter(game=game)
       
        periods = {}
        for team in teams:
            periods[team.role] = Period.objects.filter(team=team).order_by('number')

        orders = {}
        max_order = 0
        for role in periods:
            orders[role] = '' 
            for period in periods[role]:
                if period.order is not None:
                    if period.order > max_order:
                        max_order = period.order
                    orders[role] += str(period.order)+','
            orders[role] = orders[role][0:-1]

        url = 'http://chart.apis.google.com/chart?'+\
                '&cht=ls'+\
                '&chs=500x325'+\
                '&chd=t:%s|%s|%s|%s' % (orders['Factory'], orders['Distributor'], 
                                        orders['Wholesaler'], orders['Retailer'])+\
                '&chds=0,%d' % max_order+\
                '&chco=ff0000,336699,cccccc,000000'+\
                '&chls=2'+\
                '&chtt=Beer+Game+Results+for+%s' % game.name+\
                '&chts=000000,20'+\
                '&chdl=Factory|Distributor|Wholesaler|Retailer'+\
                '&chxt=x,y'+\
                '&chxr=0,0,%d,1|1,0,%d' % (teams.get(role='Factory').last_completed_period,
                                            max_order)+\
                '&chxl=3:|Period'

        return HttpResponse(json.dumps({'chart': url,'id':data['id'], 'name': game.name}),
                    mimetype='text/javascript')
        
    else:
        return HttpResponse(json.dumps({'error': 'missing required arguments'}),
                    mimetype='text/javascript')
        

def output_csv(request):
    import csv
    from datetime import datetime
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=beergame.csv'

    data = request.REQUEST.copy()

    start_time = datetime.strptime("%s %s %s %s %s %s" % (data['month'], data['day'],
                    data['year'], data['hour'], data['minute'], data['ampm']),
                                    "%m %d %Y %I %M %p")


    writer = csv.writer(response)
    writer.writerow(['Index','Game','Role','Number','Inventory','Backlog',
        'Demand','Order1','Order2','Shipment1','Shipment2','Shipped','Cost',
        'Cumulative Cost','Order'])

    games = Game.objects.filter(date_started__gte=start_time)

    for game in games:
        teams = Team.objects.filter(game=game)
        
        for team in teams:
            periods = Period.objects.filter(team=team).order_by('number')
            
            idx = 0
            for period in periods:
                idx += 1
                vals = [period.pk, period.team.game, period.team.role, period.number, 
                period.inventory, period.backlog,period.demand,period.order_1, 
                period.order_2, period.shipment_1, period.shipment_2, period.shipped, 
                period.cost, period.cumulative_cost, period.order]

                writer.writerow(vals)

                if idx == 40:
                    break
            
            while idx < 40:
                idx += 1
                writer.writerow([])
    
    return response

def js_test(request):
    # the game and role is loaded from the test fixtures
    game = Game.objects.get(id=1) 
    team = get_object_or_404(Team, game=game, role='Factory')
    role = 'Factory'
    period = Period.objects.filter(team=team).order_by('-number')[0]

    if team.last_clicked_button in ['step3', 'order', 'none']:
        period_range = 0 
    else:
        period_range = 1 

    all_periods = Period.objects.filter(team=team).exclude(number=0).order_by('-number')[period_range:]

    return render_to_response('jstest.html', {
                                                'game': game,
                                                'role': role,
                                                'period': period,
                                                'all_periods':all_periods,
                                                'display_orders':settings.DISPLAY_ORDERS,
                                            })
