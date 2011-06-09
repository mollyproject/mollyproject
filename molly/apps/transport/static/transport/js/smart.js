function refreshTransport(data){
    transportAjax = null;
    clear_loading_screen()
    $('#park_and_rides .section-content').empty()
    for (var i in data.park_and_rides) {
        var entity = data.park_and_rides[i]
        var title = entity.title
        if (title.slice(-13) == 'Park and Ride') {
            title = title.slice(0, -14)
        }
        if (title.slice(-11) == 'Park & Ride') {
            title = title.slice(0, -12)
        }
        $('#park_and_rides .section-content').append('<div class="park-and-ride"><h3><a href="' + entity._url + '">' + title + '</a></h3></div>')
        if (entity.metadata.park_and_ride) {
            if (entity.metadata.park_and_ride.unavailable) {
                spaces = '?'
                $('.park-and-ride:last').append('<p><em>' + gettext('Space information currently unavailable') + '</em></p>')
            } else {
                $('.park-and-ride:last').append('<div class="capacity-bar"><div style="width: ' + entity.metadata.park_and_ride.percentage.toString() + '%; height:7px;background-color: #960300;">&nbsp;</div></div>')
                spaces = entity.metadata.park_and_ride.spaces.toString()
            }
            // Translators: Spaces: Free spaces / Capactity
            var spaces = interpolate(gettext('Spaces: %(spaces)s / %(capacity)s'),
                                     { spaces: spaces,
                                       capacity: entity.metadata.park_and_ride.capacity },
                                     true)
            $('.park-and-ride:last').append('<p>' + spaces + '</p>')
        }
        if (i < (data.park_and_rides.length - 1) || i%2 == 1) {
            $('.park-and-ride:last').css('float', 'left')
        }
        if (i%2 == 0) {
            $('.park-and-ride:last').css('clear', 'left')
        }
    }
    
    function pad2(number) {
        return (number < 10 ? '0' : '') + number
    }
    var now = new Date();
    now = pad2(now.getHours()) + ':' + pad2(now.getMinutes()) + ':' + pad2(now.getSeconds())
    for (var type in data.nearby) {
        $('#' + type + ' h2:first').html(data.nearby[type].results_type + ' ' + data.nearby[type].type.verbose_name_plural + ' - ' + now)
        tbody = $('#' + type + ' .content tbody')
        tbody.empty()
        for (var i in data.nearby[type].entities) {
            entity = data.nearby[type].entities[i]
            tbody.append('<tr class="sub-section-divider"><th colspan="3"><a href="' + entity._url  + '" style="color:inherit;">' + entity.title + '</a></th></tr>')
            if (entity.distance) {
                // Translators: e.g., about 100 metres NW
                var about = interpolate(gettext('about %(distance)s %(bearing)s'),
                                        { distance: Math.ceil(entity.distance/10)*10,
                                          bearing: entity.bearing }, true)
                tbody.find('th').append('<small>(' + about + ')</small>')
            }
            if (entity.metadata.real_time_information) {
                if (entity.metadata.real_time_information.pip_info.length > 0) {
                    tbody.append('<tr><td colspan="3"></td></tr>')
                    var td = tbody.find('td:last')
                    for (var j in entity.metadata.real_time_information.pip_info) {
                        if (j > 0) {
                            td.append('<br/>')
                        }
                        td.append(entity.metadata.real_time_information.pip_info[i])
                    }
                }
                
                if (entity.metadata.real_time_information.services.length > 0) {
                    for (var j in entity.metadata.real_time_information.services) {
                        service = entity.metadata.real_time_information.services[j]
                        tbody.append('<tr></tr>')
                        tr = tbody.find('tr:last')
                        tr.append('<td style="text-align: center;"><big>' + service.service + '</big></td>')
                        tr.append('<td>' + service.destination + '</td>')
                        tr.append('<td>' + service.next + '</td>')
                        td = tr.find('td:last')
                        if (service.following.length > 0) {
                            td.append('<small>, ' + service.following[0])
                            if (service.following.length > 1) {
                                td.append(', &hellip;</small>')
                            }
                        }
                    }
                } else {
                    tbody.append('<tr><td colspan="3">' + gettext('Sorry, there is currently no real time information for this stop.') + '</td></tr>')
                }
            } else {
                tbody.append('<tr><td colspan="3">' + gettext('Sorry, there is currently no real time information for this stop.') + '</td></tr>')
            }
        }
        if (data.nearby[type].results_type == 'Favourite') {
            $('.switcher').html('<a href="?' + type + '=nearby" class="nearby-switcher has-ajax-handler">' +
                                interpolate(gettext('View nearby %(entitytype)s'), {
                                    entitytype: data.nearby[type].type.verbose_name_plural
                                }, true) +
                                '</a>')
        } else {
            $('.switcher').html('<a href="?' + type + '=favourites" class="favourites-switcher has-ajax-handler">' +
                                interpolate(gettext('View favourite %(entitytype)s'), {
                                    entitytype: data.nearby[type].type.verbose_name_plural
                                }, true) +
                                '</a>')
        }
        enableNearbySwitcher();
    }
    
    rebuildLDB($('#ldb'), data);
    transportLDBButtons()
    capture_outbound();
    
    ul = $('#travel_news .content-list')
    ul.empty()
    for (var i in data.travel_alerts) {
        ul.append('<li><a href="' + data.travel_alerts[i]._url + '" style="color: inherit;">' + data.travel_alerts[i].title + '</a></li>')
    }
    
    capture_outbound();
}

function ajaxTransportUpdate(){
    transportAjax = $.ajax({
        url: current_url,
        data: $.extend({ format: 'json', board: board }, transportViews),
        dataType: 'json',
        success: refreshTransport
    })
}

var transportTimer = null;
var transportViews = {};
var transportAjax = null;

function transportRefreshTimer(){
    if (transportAjax == null) {
        ajaxTransportUpdate();
    }
    transportTimer = setTimeout(transportRefreshTimer, 30000);
}

function enableNearbySwitcher(){
    $('.nearby-switcher').click(function(){
        display_loading_screen()
        var results_type = $(this).parents('.section').attr('id');
        transportViews[results_type] = 'nearby'
        transportAjax = $.ajax({
            url: current_url,
            data: $.extend({ format: 'json', board: board }, transportViews),
            dataType: 'json',
            success: function(data){async_load_xhr = null;refreshTransport(data)},
            error: ajax_failure
        })
        async_load_xhr = transportAjax;
        return false;
    })
    $('.favourites-switcher').click(function(){
        display_loading_screen()
        var results_type = $(this).parents('.section').attr('id');
        transportViews[results_type] = 'favourites'
        transportAjax = $.ajax({
            url: current_url,
            data: $.extend({ format: 'json', board: board }, transportViews),
            dataType: 'json',
            success: function(data){async_load_xhr = null;refreshTransport(data)},
            error: ajax_failure
        })
        async_load_xhr = transportAjax;
        return false;
    })
}

function transportLDBButtons(){
    $('.ldb-board').click(function(){
        display_loading_screen()
        transportAjax = $.ajax({
            url: $(this).attr('href'),
            data: $.extend({ format: 'json' }, transportViews),
            dataType: 'json',
            success: function(data){
                transportAjax = null;
                refreshTransport(data);
                clear_loading_screen();
                async_load_xhr = null;
            },
            error: ajax_failure
        })
        async_load_xhr = transportAjax;
        return false;
    })
    $('.ldb-board').addClass('has-ajax-handler')
}

$(document).bind('molly-page-change', function(event, url){
    if (url == '/transport/') {
        transportTimer = setTimeout(transportRefreshTimer, 30000)
        $(document).bind('molly-location-update', ajaxTransportUpdate)
        transportLDBButtons();
        enableNearbySwitcher();
    } else {
        $(document).unbind('molly-location-update', ajaxTransportUpdate)
        if (transportAjax != null) {
            transportAjax.abort()
        }
        clearTimeout(transportTimer)
    }
});