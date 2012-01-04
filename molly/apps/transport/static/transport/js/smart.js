// Updating functions relating to rail
var railTimer = null;
var railAjax = null;

function ajaxRailUpdate(){
    railAjax = $.ajax({
        url: current_url,
        data: { format: 'json', board: board },
        dataType: 'json',
        success: refreshRail
    })
}

function railRefreshTimer(){
    // Only make a new request if there isn't one already in process
    if (railAjax == null) {
        ajaxRailUpdate();
    }
    railTimer = setTimeout(railRefreshTimer, 60000);
}

function refreshRail(data){
    clear_loading_screen()
    railAjax = null;
    rebuildLDB($('#ldb-' + data.entity.identifier_scheme + '-' + data.entity.identifier_value), data.board, data.entity);
    railLDBButtons()
    capture_outbound();
}

function railLDBButtons(){
    // Allow switching between departure and arrivals boards
    $('.ldb-board').click(function(){
        display_loading_screen()
        railAjax = $.ajax({
            url: $(this).attr('href'),
            data: { format: 'json' },
            dataType: 'json',
            success: function(data){
                refreshRail(data);
                async_load_xhr = null;
            },
            error: ajax_failure
        })
        async_load_xhr = railAjax;
        return false;
    })
    $('.ldb-board').addClass('has-ajax-handler')
}

// Updating functions relating to park and rides
var PAndRTimer = null;
var PAndRAjax = null;

function ajaxPAndRUpdate(){
    PAndRAjax = $.ajax({
        url: current_url,
        data: { format: 'json' },
        dataType: 'json',
        success: refreshPAndR
    })
}

function PAndRRefreshTimer(){
    // Only make a new request if there isn't one already in process
    if (PAndRAjax == null) {
        ajaxPAndRUpdate();
    }
    PAndRTimer = setTimeout(PAndRRefreshTimer, 60000);
}

function refreshPAndR(data){
    PAndRAjax = null;
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
                $('.park-and-ride:last').append('<div class="capacity-bar"><div class="capacity-bar-red" style="width: ' + entity.metadata.park_and_ride.percentage.toString() + '%;">&nbsp;</div></div>')
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
    capture_outbound();
}

// Updating functions relating to public transport pages
var ptTimer = null;
var ptAjax = null;

function ajaxPTUpdate(){
    ptAjax = $.ajax({
        url: current_url,
        data: { format: 'json' },
        dataType: 'json',
        success: refreshPT
    })
}

function ptRefreshTimer(){
    // Only make a new request if there isn't one already in process
    if (ptAjax == null) {
        ajaxPTUpdate();
    }
    ptTimer = setTimeout(ptRefreshTimer, 30000);
}

function rebuildPT(tbody, entities){
    tbody.empty()
    for (var i in entities) {
        entity = entities[i]
        if (entity.distance) {
            // Translators: e.g., about 100 metres NW
            var about = ' (' + interpolate(gettext('about %(distance)s %(bearing)s'),
                                    { distance: entity.distance,
                                      bearing: entity.bearing }, true) + ')'
        } else {
            var about = ''
        }
        tbody.append('<tr class="sub-section-divider"><th colspan="3"><a href="' + entity._url  + '" class="subtle-link">' + entity.title + about + '</a></th></tr>')
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
                    if (service.route) {
                        var route_link = '<a href="' + entity._url + 'service?route=' + encodeURIComponent(service.service) + '" class="subtle-link">' + service.service + '</a>'
                    } else if (service.journey) {
                        var route_link = '<a href="' + entity._url + 'service?journey=' + service.journey.id + '" class="subtle-link">' + service.service + '</a>'
                    } else {
                        var route_link = service.service
                    }
                    tr.append('<td class="center"><big>' + route_link + '</big></td>')
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
    capture_outbound();
}

function refreshPT(data){
    ptAjax = null;
    clear_loading_screen()
    
    function pad2(number) {
        return (number < 10 ? '0' : '') + number
    }
    var now = new Date();
    now = pad2(now.getHours()) + ':' + pad2(now.getMinutes()) + ':' + pad2(now.getSeconds())
    
    // Do transit status
    if (data.line_status) {
        rebuildLineStatus($('#transit-status'), data.line_status.line_statuses);
    }
    
    // Do favourite entities
    if (data.favourites) {
        $('#entities-favourites h2:first').html(gettext('Favourite') + ' ' + data.type.verbose_name_plural + ' - ' + now);
        tbody = $('#entities-favourites .content tbody');
        rebuildPT(tbody, data.favourites);
    }
    
    // Do nearby entities
    $('#entities-nearby h2:first').html(gettext('Nearby') + ' ' + data.type.verbose_name_plural + ' - ' + now);
    tbody = $('#entities-nearby .content tbody');
    rebuildPT(tbody, data.entities);
}

$(document).bind('molly-page-change', function(event, url){
    
    if (url == '/transport/rail/') {
        // Rail view - update every 60 seconds
        railTimer = setTimeout(railRefreshTimer, 60000);
        // Also update if location changes
        $(document).bind('molly-location-update', ajaxRailUpdate);
        railLDBButtons();
    } else {
        $(document).unbind('molly-location-update', ajaxRailUpdate);
        if (railAjax != null) {
            railAjax.abort();
        }
        clearTimeout(railTimer);
    }
    
    if (url == '/transport/park-and-ride/') {
        // P&R view - update every 5 minutes
        transportTimer = setTimeout(PAndRRefreshTimer, 300000);
    } else {
        if (PAndRAjax != null) {
            PAndRAjax.abort()
        }
        clearTimeout(PAndRTimer)
    }
    
    $(document).unbind('molly-location-update', ajaxPTUpdate)
    if (ptAjax != null) {
        ptAjax.abort()
    }
    clearTimeout(ptTimer)
    if (url.match(/^\/transport\/[^\/]+\/$/)) {
        // Public transport view - refresh every 30 seconds and on location move
        ptTimer = setTimeout(ptRefreshTimer, 30000)
        $(document).bind('molly-location-update', ajaxPTUpdate)
    }
    
});
