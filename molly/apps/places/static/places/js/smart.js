function capfirst(s) {
    return s.substr(0,1).toUpperCase() + s.substr(1)
}

$(document).bind('molly-page-change', function(event, url){
    if (url == '/places/') {
        $('.nearby a').click(function(){
            $.ajax({
                url: $(this).attr('href'),
                data: { format: 'json' },
                dataType: 'json',
                success: function(data){parse_results(data, true)}
            })
            return false;
        })
        
        $('.nearby a').addClass('has-ajax-handler')
        
        $('.categories a').click(function(){
            $.ajax({
                url: $(this).attr('href'),
                data: { format: 'json' },
                dataType: 'json',
                success: function(data){parse_results(data, false)}
            })
            return false;
        })
        
        $('.categories a').addClass('has-ajax-handler')
        capture_outbound();
    }
});

function parse_results(data, nearby){
    $('.category-list').remove()
    for (category in data.entity_types) {
        $('#poi-category-selector').append(
            '<div class="header"><h2>' + category + '</h2></div>' +
            '<ul class="link-list"></ul>')
        for (j in data.entity_types[category]) {
            entity_type = data.entity_types[category][j]
            if (nearby) {
                $('#poi-category-selector ul:last').append(
                    '<li><a href="' + current_url + 'nearby/' + entity_type.slug + '/">' + 
                    capfirst(entity_type.verbose_name_plural) +
                    ' <small>(' + entity_type.entities_found + ' within ' + Math.ceil(entity_type.max_distance/10)*10 + 'm)</small>' +
                    '</a></li>')
            } else {
                $('#poi-category-selector ul:last').append(
                    '<li><a href="' + current_url + 'category/' + entity_type.slug + '/">' + 
                    capfirst(entity_type.verbose_name_plural) +
                    '</a></li>')
            }
        }
    }
    $('#poi-category-selector ul').addClass('no-round-bottom')
    $('#poi-category-selector ul:last').removeClass('no-round-bottom')
    capture_outbound();
}
    
function refreshRTI(data){
    function pad2(number) {
        return (number < 10 ? '0' : '') + number
    }
    var now = new Date();
    $('.update-time').html(pad2(now.getHours()) + ':' + pad2(now.getMinutes()) + ':' + pad2(now.getSeconds()))
    if (typeof(data.entity.metadata.real_time_information) != 'undefined') {
        rebuildRTI($('#' + data.entity.identifier_scheme + '-' + data.entity.identifier_value), data.entity.metadata.real_time_information)
    }
    if (typeof(data.entity.metadata.ldb) != 'undefined') {
        rebuildLDB($('#' + data.entity.identifier_scheme + '-' + data.entity.identifier_value), data)
    }
    for (var i in data.entity.associations) {
        for (var j in data.entity.associations[i].entities) {
            var entity = data.entity.associations[i].entities[j]
            if (typeof(entity.metadata.real_time_information) != 'undefined') {
                rebuildRTI($('#' + entity.identifier), entity.metadata.real_time_information)
            }
        }
    }
    setTimeout(function(){
        $.ajax({
            url: window.location.href,
            data: { format: 'json', board: board },
            dataType: 'json',
            success: refreshRTI
        })
    }, refreshFrequency * 1000)
}

function rebuildRTI(elem, metadata){
    elem.empty()
    if (metadata.pip_info.length > 0 || metadata.services.length == 0) {
        elem.append('<ul class="content-list no-round-bottom"></ul>')
        if (metadata.pip_info.length > 0) {
            elem.append('<li></li>')
            var li = elem.find('li')
            for (var i in metadata.pip_info) {
                if (i > 0) {
                    li.append('<br/>')
                }
                li.append(metadata.pip_info[i])
            }
        }
        if (metadata.services.length == 0) {
            li.append('Sorry, there is currently no bus time information for this stop.')
        }
    }
    if (metadata.services.length > 0) {
        elem.append('<div class="section-content no-round-bottom"><div class="pad-5"><table class="real-time-information"><tbody id="bus_times"></tbody></table></div></div>')
        tbody = elem.find('tbody')
        for (var i in metadata.services) {
            var service = metadata.services[i]
            tbody.append('<tr>' + 
            '<td rowspan="2" style="font-size:200%; text-align:center;">' + service.service + '</td>' +
            '<td>' + service.destination + '</td>' +
            '<td>' + service.next + '</td>' +
            '</tr><tr class="notopborder"><td colspan="2"><small>Next: </small></td></tr>')
            var next = tbody.find('tr:last td small')
            if (service.following.length > 0) {
                for (var j in service.following) {
                    if (j > 0) {
                        next.append(', ')
                    }
                    next.append(service.following[j])
                }
            } else {
                next.append('<em>No further info</em>')
            }
        }
    }
}

function rebuildLDB(elem, data){
    elem.empty()
    if (data.board) {
        board = data.board
    } else {
        board = 'departures'
    }
    elem.append('<div class="header"><h2>' + data.train_station.title + ' (' + board + ') - ' + data.train_station.metadata.ldb.generatedAt.slice(11, 19) + '</h2></div>');
    
    if (data.train_station.metadata.ldb.nrccMessages) {
        elem.append('<ul class="content-list no-round-bottom"></ul>')
        ul = elem.find('ul:last')
        for (var i in data.train_station.metadata.ldb.nrccMessages.message) {
            elem.append('<li>' + data.train_station.metadata.ldb.nrccMessages.message[i] + '</li>')
        }
    }
    
    elem.append('<table class="content no-round-bottom"><thead><tr></tr></thead><tbody></tbody></table>')
    tr = elem.find('.content thead tr')
    if (board == 'arrivals') {
        tr.append('<th>Origin</th>')
    } else {
        tr.append('<th>Destination</th>')
    }
    if (data.train_station.metadata.ldb.platformAvailable) {
        tr.append('<th>Plat.</th>')
        cols = '4'
    } else {
        cols = '3'
    }
    tr.append('<th>Scheduled</th><th>Expected</th>')
    
    tbody = elem.find('.content tbody')
    if (data.train_station.metadata.ldb.error) {
        tbody.append('<tr><td colspan="' + cols + '"><p>There is currently a problem retrieving live departure information from the National Rail web site.</p>' +
                     '<p>Departure information may still be accessed <a href="http://pda.ojp.nationalrail.co.uk/en/pj/ldbboard/dep/' +  data.train_station.identifiers.crs + '"> directly from their web site</a>.</p></td></tr>')
    }
    if (data.train_station.metadata.ldb.trainServices) {
        for (var i in data.train_station.metadata.ldb.trainServices.service) {
            service = data.train_station.metadata.ldb.trainServices.service[i]
            tbody.append('<tr></tr>')
            tr = tbody.find('tr:last')
            dest = ''
            if (board == 'arrivals') {
                for (var j in service.origin.location) {
                    if (j > 0 && j < service.origin.location.length - 1) {
                        dest += ', '
                    }
                    if (j > 0 && j == service.origin.location.length - 1) {
                        dest += ' &amp; '
                    }
                    if (j > 0) {
                        dest += '<br />'
                    }
                    dest += service.origin.location[j].locationName
                    if (service.origin.location[j].via) {
                        dest += '<br /><small>' + service.origin.location[j].via + '</small>'
                        if (j < service.origin.location.length - 1) {
                            dest += '<br />'
                        }
                    }
                }
            } else {
                for (var j in service.destination.location) {
                    if (j > 0 && j < service.destination.location.length - 1) {
                        dest += ', '
                    }
                    if (j > 0 && j == service.destination.location.length - 1) {
                        dest += ' &amp; '
                    }
                    if (j > 0) {
                        dest += '<br />'
                    }
                    dest += service.destination.location[j].locationName
                    if (service.destination.location[j].via) {
                        dest += '<br /><small>' + service.destination.location[j].via + '</small>'
                        if (j < service.destination.location.length - 1) {
                            dest += '<br />'
                        }
                    }
                }
            }
            if (service.isCircularRoute) {
                dest += '<br /><small>(Circular Route)</small>'
            }
            tr.append('<td><a href="' + data.train_station._url + 'service?id=' + encodeURIComponent(service.serviceID) + '" style="color: inherit;" rel="nofollow">' + dest + '</a></td>')
            if (data.train_station.metadata.ldb.platformAvailable) {
                if (typeof(service.platform) != 'undefined') {
                    tr.append('<td>' + service.platform + '</td>')
                } else {
                    tr.append('<td>&nbsp;</td>')
                }
            }
            if (board == 'arrivals') {
                tr.append('<td>' + service.sta + '</td>')
                tr.append('<td>' + service.eta + '</td>')
            } else {
                tr.append('<td>' + service.std + '</td>')
                tr.append('<td>' + service.etd + '</td>')
            }
        }
        if (data.train_station.metadata.ldb.trainServices.service.length == 0) {
            tbody.append('<tr><td colspan="' + cols + '">There are currently no scheduled ' + board + '.</td></tr>')
        }
    } else {
        tbody.append('<tr><td colspan="' + cols + '">There are currently no scheduled ' + board + '.</td></tr>')
    }
    
    elem.append('<ul class="link-list"></ul>');
    ul = elem.find('ul:last')
    if (board == 'departures') {
        ul.append('<li><a class="ldb-board" href="' + data.train_station._url + '?board=arrivals">View arrivals board</a></li>')
    } else {
        ul.append('<li><a class="ldb-board" href="' + data.train_station._url + '?board=departures">View departures board</a></li>')
    }
    setupLDBButtons()
}

function setupLDBButtons(){
    $('.ldb-board').click(function(){
        $.ajax({
            url: $(this).attr('href'),
            data: { format: 'json' },
            dataType: 'json',
            success: function(data){rebuildLDB($('#ldb'), data)}
        })
        return false;
    })
}

$(function(){
    board = getParameterByName( 'board', window.location.href )
    if (board == '') { board = 'departures'; }
})