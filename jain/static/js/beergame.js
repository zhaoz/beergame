/* visual elements */

$('.step_wrapper').corner("10px");
$('.step').corner("8px");
$('.lead_tile').corner();

/* end visual elements */

/* constants */
CHECK_INTERVAL = 4000; // milliseconds to hit server for updates
FADE_SPEED = 700; // milliseconds for fade
/* end constants */

/* configuration */
// configure AJAX for future requests
if (typeof(window.AJAX_URL) == "undefined") {
    AJAX_URL = 'ajax/'; 
}

$.ajaxSetup({
    url: AJAX_URL, 
    cache: false,
    type: 'POST',
    dataType: 'json'
});
/* end configuration */

/*
 * updates the status message at top of screen
 */
function update_status(message) {
    $('#status-message').text(message);
}

/*
 * get current period based on browser value 
 */
function get_period() {
    var per_elm = $('#period_num');
    var per_num = per_elm.text(); 
    if (isNaN(per_num)) {
        return 0;
    }
    else {
        return parseInt(per_num); 
    }
}

/*
 * set current period on page 
 */
function set_period(period) {
    var per_elm = $('#period_num');
    per_elm.text(period);

    return true;
}

/*
 * get inventory in HTML 
 */
function get_inventory() {
    var inv_elm = $('#inv_amt');
    return parseInt(inv_elm.text());
}

/*
 * set inventory in HTML 
 */
function set_inventory(inventory) {
    var inv_elm = $('#inv_amt');
    inv_elm.text(inventory);
}

/* 
 * get shipment1
 */
function get_shipment1() {
    return parseInt($('#ship1_amt').text()); 
}

/* 
 * set shipment1
 */
function set_shipment1(val) {
    $('#ship1_amt').text(val);
}

/* 
 * get order 
 */
function get_order() {
    var order = parseInt($('#order_amt').text()); 
    if (isNaN(order)) {
        log_error('order was not a number');
        return false;
    }
    return order;
}

/* 
 * set order 
 */
function set_order(order) {
    $('#order_amt').text(order);
}

/* 
 * amount to order is the amount that current team
 * wants to order from supplier
 */
function get_amt_to_order() {
    return parseInt($('#amt_to_order').val());
}

/* 
 * amount to order is the amount that current team
 * wants to order from supplier
 */
function set_amt_to_order(val) {
    $('#amt_to_order').val(val);
}

/*
 * get the shipment amount
 */
function get_shipment() {
    return $('#amt_to_ship').val();
}

/*
 * set the shipment amount
 */
function set_shipment(val, select) {
    var shipment_input = $('#amt_to_ship')
    shipment_input.val(val);

    if (select) {
        shipment_input.select(); 
    }
}

/*
 * returns the ideal amount to ship given backorder, 
 * inventory, and current order
 */
function get_shipment_recommendation(backlog, inventory, order) {

    // backlog
    if (backlog > 0) {
        // can deliver both backlog and order
        if (inventory >= (backlog + order)) {
            return backlog + order;
        }
        // can't deliver full backlog and order
        else {
            return inventory; 
        }
    }
    // no backlog
    else {
        // order is more than inventory
        if (order > inventory) {
            return inventory; 
        }
        // order is less than inventory
        else {
            return order;
        }
    }
}

/*
 * get the backlog and set shipment recommendation
 * 
 */
function set_shipment_recommendation() {
    $.ajax({
            data: {
                    get: 'backlog',
                    period: get_period()
            }, 
            success: function(data, textStatus) {
                if ('error' in data) {
                    log_error(data['error']);
                }
                else if ('backlog' in data) {
                    var amount = get_shipment_recommendation(data.backlog, 
                                                            get_inventory(),
                                                            get_order());
                    set_shipment(amount, true);
                }

            }
    });
}

/*
 * logs error messages to div at bottom of game
 */
function log_error(msg) {
    $('#errors ul').prepend('<li>'+msg+'</li>');
}

/*
 * when getting ready to start another period
 * check if other teams are done so we can start
 */
function check_if_teams_ready() {
    $.ajax({
            data: {
                    check: 'teams_ready',
                    period: get_period()
            },
            success: function(data, textStatus) {
                if ('teams_ready' in data) {
                    if (data['teams_ready']) {
                        var per_btn = $('#next_period_btn');
                        per_btn.attr('disabled', false);
                        per_btn.val('Start next period');
                        $('#order_btn').stopTime();
                    }
                }
                else if ('error' in data) {
                    log_error(data['error']);
                }
            }
    });

}

/*
 * waits for other teams to order to begin next period
 */
function wait_for_teams() {

    // TODO make button say "Start Game"
    // TODO short circuit if start of game

    var next_per_btn = $('#next_period_btn');

    if (get_period() == 0) {
        next_per_btn.val('Start Game');
    }
    else {
        // wait for other teams to finish
        next_per_btn.val('Waiting for Other firms to Order');
    }


    $('#order_btn').everyTime(CHECK_INTERVAL, function() {
    });

}


function listen_for_can_ship() {
    $('#step2_btn').everyTime(CHECK_INTERVAL, function() {
        $.ajax({
            data: {
                    check: 'can_ship',
                    period: get_period()
            },
            success: function(data, textStatus) {
                if ('can_ship' in data) {
                    if (data['can_ship']) {
                        $('#ship_btn').attr('disabled',false); 
                        $('#ship_btn').val('Ship'); 
                        $('#step2_btn').stopTime();
                    }
                }
                else if ('error' in data) {
                    log_error(data['error']);
                }
                else {
                    log_error('listen for can ship returned invalid data');
                }
            }
        });
    });
}

function listen_for_can_order() {
    $('#step3_btn').everyTime(CHECK_INTERVAL, function() {
        $.ajax({
                data: {
                        check: 'can_order',
                        period: get_period()
                },
                success: function(data, textStatus) {
                    if ('error' in data) {
                        log_error(data['error']);
                    }
                    else {
                        if ('can_order' in data) {
                            if (data['can_order']) {
                                $('#order_btn').attr('disabled',false); 
                                $('#order_btn').val('Order'); 
                                $('#step3_btn').stopTime();
                            }
                        }
                    }
                }
        });
    });
}

/*
 * sets the buttons in the correct state i.e. enabled
 * or disabled 
 */
function set_buttons() {
    if ($('#next_period_btn').get().length == 1) {
        $.ajax({
                data:   { 
                            query: 'last_clicked'
                        },
                success: function(data, textStatus) {
                    var btns = {
                                    start:  'next_period_btn',
                                    step1:  'step1_btn',
                                    step2:  'step2_btn',
                                    ship:   'ship_btn',
                                    step3:  'step3_btn',
                                    order:  'order_btn'
                                };
                    var last_clicked = data['last_clicked'];
                    var start_index = 0;
                    if (last_clicked == 'none') {
                        for (var btn in btns) {
                            $('#'+btns[btn]).attr('disabled',true);
                        }
                        wait_for_teams();
                    }
                    else if (last_clicked in btns) {
                        var disable = true;
                        for (var btn in btns) {
                            $('#'+btns[btn]).attr('disabled',disable);
                            if (!disable) { disable = true; }
                            if (btn == last_clicked) { disable = false; }
                        }
                        if (!$('#ship_btn').attr('disabled')) {
                            $('#ship_btn').attr('disabled',true); 
                            $('#ship_btn').val('waiting...'); 

                            set_shipment_recommendation();

                            listen_for_can_ship();
                        }
                        else if (!$('#order_btn').attr('disabled')) {
                            $('#order_btn').attr('disabled', true); 
                            $('#order_btn').val('waiting...'); 
                            
                            listen_for_can_order();
                        }
                    }
                    else {
                        log_error('last clicked returned an invalid button: '+last_clicked);
                    }
                }
        });
    }
}

function listen_for_shipment() {
    // starts listening for next shipment
    $('#step1').everyTime(CHECK_INTERVAL, function() {
        $.ajax({
                data: {
                    get: 'shipment_2',
                    period: get_period()
                },
                success: function(data, textStatus) {
                    if ('shipment_2' in data && data['shipment_2'] != null) {
                        $('#step1').stopTime();
                        $('#shipment2').remove();
                        $('#shipment1').after('<div id="shipment2" class="lead_tile">' + 
                            '<h4>Shipment #2</h4><p id="ship2_amt">'+data['shipment_2']+'</p></div>');

                        $('#shipment2').corner();
                       
                        // if shipment arrives after step3, table will
                        // be updated
                        $.ajax({
                                data: {
                                    query: 'last_clicked',
                                    period: get_period()
                                },
                                success: function(data, textStatus) {
                                    if ('last_clicked' in data) {
                                        var last_clicked = data['last_clicked'];
                                        if (last_clicked in ['step3','order','none']) {
                                            reload_period_table();
                                        }
                                    }
                                    else if ('error' in data) {
                                        log_error(data['error']);
                                    }
                                }
                        });
                    }
                    else if ('error' in data) {
                        log_error(data['error']);
                    }
                }        
        });
    });
}

function listen_for_order() {
    $('#step2').everyTime(CHECK_INTERVAL,function() {
        $.ajax({
                data: {
                    period: get_period(),
                    get: 'order_2'
                },
                success: function(data, textStatus) {
                    if ('order_2' in data && data['order_2'] != null) {
                        $('#step2').stopTime();
                        if ('display_orders' in data) {
                            if (data['display_orders']) {
                                $('#order2_amt').text(data['order_2']);
                            }
                        }
                        $('#order2_amt').text('');
                    }
                    else if ('error' in data) {
                        log_error(data['error']);
                    }
                }
        });
    });
}

function check_response(data, callback) {
    if ('success' in data) {
        if (data['success']) {
            return true;
        }
        else {
            callback.call();
        }
    }
    else {
        log_error('response did not contain success argument');
    }
}

function set_timers() {
    $.ajax({
            data: {
                   query: 'last_clicked',
                   period: get_period()
            },
            success: function(data, textStatus) {
                if ('last_clicked' in data) {
                    var last_clicked = data['last_clicked'];

                    if (last_clicked == 'step1' || last_clicked == 'step2' || 
                        last_clicked == 'ship' || last_clicked == 'step3' 
                        || last_clicked == 'order') {

                        listen_for_shipment();    

                        if (last_clicked != 'step1') {
                            listen_for_order();
                        }
                    }
                }
            }
    });
}

function btnEvent(fn, name, id) {
    // set last clicked
    $.ajax({
                data: {
                        set: 'last_clicked',
                        value: name
                },
                success:function(data, textStatus) {
                    if ('error' in data) {
                        log_error(data['error']);
                    }
                }
            });

    // disable current button
    $('#'+id).attr('disabled',true);

    // enable next button
    var next_buttons = {
                        'start':'step1_btn',
                        'step1':'step2_btn',
                        'step2':'ship_btn',
                        'ship':'step3_btn',
                        'step3':'order_btn'
                       }
    $('#'+next_buttons[name]).attr('disabled',false);

    // execute passed function
    fn.call(); 
}

function reload_period_table() {
    $.ajax({
            dataType: 'html',
            data: {
                    html: 'period_table',
                    period: get_period()
            },
            success: function(result, textStat) {
                $('#period_table').html(result);
            }
    });
}

$(document).ready(function() {

    $('#chart-select').change(function() {
        if ($(this).val() != 'none') {
            $('#chart-output').text('loading chart...');
            $.ajax({
                    url: 'chart/',
                    data: {
                            id: $(this).val() 
                    },
                    success: function(data, textStatus) {
                        $('#chart-output').html('<a href="'+data['chart']+'">Beer game results for '+data['name']+'</a>');
                    }
            });
        }
    });

    
    if ($('#next_period_btn').get().length == 1) {
        set_buttons();
        set_timers();
    }

    // start button
    $('#next_period_btn').click(function() { 
        btnEvent(function() {

            $.post('ajax/',
                    {
                        step: 'start',
                        period: get_period()
                    }, function(data, textStatus) {
                        if ('error' in data) {
                            log_error(data['error']);
                        }
                    }, 'json');

            // increment the period
            cur_period = get_period(); 
            set_period(cur_period + 1);

            // remove shipped amount
            $('#amt_to_ship').val('');

            // remove ordered amount
            $('#amt_to_order').val('');
        }, 'start', this.id);
    });


    $('#step1_btn').click(function() {
        btnEvent(function() {
            $.post('ajax/',
                {
                    step: 'step1',
                    period: get_period()
                }, function(data, textStatus) {
                    if ('error' in data) {
                        log_error(data['error']);
                    }
                }, 'json');

            var ship_div = $('#shipment1');

            // remove shipment 1 div
            ship_div.fadeOut(FADE_SPEED, function() { 
                // increment the inventory
                set_inventory(get_inventory()+get_shipment1());

                ship_div.remove(); 

                // change ship2 to ship1
                var ship2_div = $('#shipment2');
                ship2_div.attr('id','shipment1');
                $('#ship2_amt').attr('id','ship1_amt');
                $('#shipment1 > h4').text('Shipment1'); 
                $('#shipment1').after('<div id="shipment2" class="lead_tile">' + 
                    '<h4>Shipment2</h4><p id="ship2_amt">Waiting for Shipment from Supplier</p></div>');

                $('#shipment2').corner();
              
                listen_for_shipment();
            });
        }, 'step1', this.id);
    });

    $('#step2_btn').click(function() {
        btnEvent(function() {
            $.ajax({
                    data: {
                            period: get_period(),
                            step: 'step2'
                    },
                    success: function(data, textStatus) {
                        if ('error' in data) {
                            log_error(data['error']);
                        }
                        else if ('step2' in data) {
                            if (data['step2'] != null) {
                                set_order(data['step2']); 
                            }
                            else {
                                log_error('current order returned null value');
                            }
                        }
                        else {
                            log_error('error returning step2');
                        }
                    }

            });
            $('#ship_btn').attr('disabled',true); 
            $('#ship_btn').val('waiting...'); 
            listen_for_can_ship();

            $('#order1').fadeOut(FADE_SPEED, function() {
                $('#order1').remove();
                $('#order2').attr('id','order1');
                $('#order2_amt').attr('id','order1_amt');
                $('#order1 > h4').text('Incoming Order #1');
                $('#order1').after('<div id="order2" class="lead_tile">' + 
                    '<h4>Incoming Order #2</h4><p id="order2_amt">Waiting for Order from Customer</p></div>');
                
                $('#order2').corner();

                set_shipment_recommendation();

                listen_for_order();
            });
        }, 'step2', this.id);
    });
    
    $('#ship_btn').click(function() {
        btnEvent(function() {
            // clear shipment errors
            $('#amt_to_ship').focus(function() {
                $('#shipment_errors').text('');
            });

            // handle amount to ship
            var amt_to_ship = parseInt($('#amt_to_ship').val());

            // check validate
            if (isNaN(amt_to_ship)) {
                $('#shipment_errors').text('Please enter a value!');
                $('#ship_btn').attr('disabled', false);
            }
            // validates 
            else {

                if (amt_to_ship > get_inventory()) {
                    $('#shipment_errors').text('Cannot ship more than inventory!');

                    $.ajax({
                            data: {
                                set: 'last_clicked',
                                value: 'step2'
                            },
                            success: function(data, textStatus) {
                                if ('error' in data) {
                                    log_errror(data['error']);
                                }
                                else if (!'success' in data) {
                                    log_error('set last clicked server communication failed');
                                }
                            }
                    });
                    $('#ship_btn').attr('disabled', false);
                }
                else {
                    // take out inventory
                    set_inventory(get_inventory() - parseInt(amt_to_ship));
                    $.ajax({
                            data: {
                                    shipment: amt_to_ship,
                                    period: get_period()
                            },
                            success: function(data, textStatus) {
                                if ('error' in data) {
                                    log_error(data['error']);
                                }
                            }
                    });
                }
            }
        }, 'ship', this.id);
    });

    $('#step3_btn').click(function() {
        btnEvent(function() {
            $.ajax({
                    dataType: 'html',
                    data: {
                            period: get_period(),
                            step: 'step3'
                    },
                    success: function(data, textStatus) {
                        $('#period_table').html(data);
                    }
            });

            $('#order_btn').attr('disabled', true); 
            $('#order_btn').val('waiting...'); 
            listen_for_can_order();
        }, 'step3', this.id);
    });

    $('#order_btn').click(function() {
        btnEvent(function() {
            // clear order errors
            $('#amt_to_order').focus(function() {
                $('#order_errors').text('');
            });
            var order = get_amt_to_order();

            if (isNaN(order)) {
                $('#order_errors').text('Please enter a value to order!');
                $('#order_btn').attr('disabled',false);
            }
            else { 
                $.ajax({
                        data: {
                                order: order,
                                period: get_period()
                        },
                        success: function(data, textStatus) {
                            // after ordering refresh period table
                            reload_period_table();
                                                        
                            $.ajax({
                                    data: {
                                            set: 'last_clicked',
                                            value: 'none'
                                    },
                                    success: function(data, textStatus) {
                                        if ('error' in data) {
                                            log_error(data['error']);
                                        }
                                    }
                            });
                            
                            wait_for_teams();
                        }
                    });
                }
        }, 'order', this.id);
    });
});
