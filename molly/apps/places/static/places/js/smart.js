function capfirst(s) {
    return s.substr(0,1).toUpperCase() + s.substr(1)
}

entitydetail_ajax_refresh = null;

$(document).bind('molly-page-change', function(event, url){
    
    clearTimeout(entitydetail_ajax_refresh)
    
    if (url == '/places/') {
        // IndexView
        $('.nearby a').click(function(){
            display_loading_screen()
            $.ajax({
                url: $(this).attr('href'),
                data: { format: 'json' },
                dataType: 'json',
                success: function(data){parse_results(data, true);clear_loading_screen();},
                error: ajax_failure
            })
            return false;
        })
        
        $('.nearby a').addClass('has-ajax-handler')
        
        $('.categories a').click(function(){
            display_loading_screen()
            $.ajax({
                url: $(this).attr('href'),
                data: { format: 'json' },
                dataType: 'json',
                success: function(data){parse_results(data, false);clear_loading_screen();},
                error: ajax_failure
            })
            return false;
        })
        
        $('.categories a').addClass('has-ajax-handler')
    }
    
    if (url.match(/^\/places\/category\/[^\/;]/)) {
        // Category detail view
        $('li.next a').click(function(){
            display_loading_screen()
            $.ajax({
                url: $(this).attr('href'),
                data: { format: 'json' },
                dataType: 'json',
                success: function(data){
                    $('.current-page').html(data.entities.number)
                    
                    if (data.entities.has_next) {
                        $('li.next a').attr('href', '?page=' + (data.entities.number + 1).toString(10))
                    } else {
                        $('li.next').remove()
                        $('.section-content').removeClass('no-round-bottom')
                    }
                    for (i in data.entities.objects) {
                        item = data.entities.objects[i]
                        $('#category-list').append('<li><a href="' + item._url + '">' +
                                                    item.title + 
                                                    '</a></li>')
                        if (i == 0) {
                            $('#category-list li:last').addClass('page-break')
                        }
                    }
                    clear_loading_screen()
                },
                error: ajax_failure
            })
            return false;
        })
        $('li.next a').addClass('has-ajax-handler')
    }
    
    if (url.match(/^\/places\/[a-z_\-]+:[\da-zA-Z]+\/$/)) {
        // Entity detail view
        
        entitydetail_ajax_refresh = setTimeout(function(){
        $.ajax({
            url: to_absolute(current_url),
            data: { format: 'json' },
            dataType: 'json',
            success: refreshRTI
        })
        }, 30000) // default to 30 seconds here because we don't actually know
                  // what the refresh frequency is - future requests will be
                  // spaced correctly
        
        $('.nearby a').click(function(){
            display_loading_screen()
            $.ajax({
                url: $(this).attr('href'),
                data: { format: 'json' },
                dataType: 'json',
                success: function(data){parse_results(data, true);clear_loading_screen();},
                error: ajax_failure
            })
            return false;
        })
        $('.nearby a').addClass('has-ajax-handler')
        setupLDBButtons();
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

function getTimestamp(date){   
    function pad2(number) {
        return (number < 10 ? '0' : '') + number
    }
    return pad2(date.getHours()) + ':' + pad2(date.getMinutes()) + ':' + pad2(date.getSeconds())
}

function refreshRTI(data){
    var now = new Date();
    $('.update-time').html(getTimestamp(now))
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
    if (data.entity.metadata.meta_refresh) {
        entitydetail_ajax_refresh = setTimeout(function(){
            $.ajax({
                url: to_absolute(current_url),
                data: { format: 'json', board: board },
                dataType: 'json',
                success: refreshRTI
            })
        }, data.entity.metadata.meta_refresh * 1000)
    }
}

function rebuildRTI(elem, metadata){
    elem.empty()
    if ((typeof(metadata.pip_info) != 'undefined' && metadata.pip_info.length > 0) || metadata.services.length == 0) {
        elem.append('<ul class="content-list no-round-bottom"></ul>')
        if (metadata.pip_info.length > 0) {
            elem.find('ul').append('<li></li>')
            var li = elem.find('li')
            for (var i in metadata.pip_info) {
                if (i > 0) {
                    li.append('<br/>')
                }
                li.append(metadata.pip_info[i])
            }
        }
        if (metadata.services.length == 0) {
            elem.find('ul').append('<li></li>')
            var li = elem.find('li')
            li.append('Sorry, there is currently no real time information for this stop.')
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
    if (data.train_station.metadata.ldb.error) {
        elem.append('<div class="header"><h2>' + data.train_station.title + ' (' + board + ')</h2></div>');
    } else {
        // generatedAt comes from the server in UTC - cast to local time
        var generated = new Date(Date.UTC(parseInt(data.train_station.metadata.ldb.generatedAt.slice(0,4)),
				 parseInt(data.train_station.metadata.ldb.generatedAt.slice(5,7)),
				 parseInt(data.train_station.metadata.ldb.generatedAt.slice(8,10)),
				 parseInt(data.train_station.metadata.ldb.generatedAt.slice(11,13)),
				 parseInt(data.train_station.metadata.ldb.generatedAt.slice(14,16)),
				 parseInt(data.train_station.metadata.ldb.generatedAt.slice(17,19))))
        elem.append('<div class="header"><h2>' + data.train_station.title + ' (' + board + ') - ' + getTimestamp(generated) + '</h2></div>');
    }
    
    if (data.train_station.metadata.ldb.nrccMessages) {
        elem.append('<ul class="content-list no-round-bottom"></ul>')
        ul = elem.find('ul:last')
        for (var i in data.train_station.metadata.ldb.nrccMessages.message) {
            ul.append('<li>' + data.train_station.metadata.ldb.nrccMessages.message[i] + '</li>')
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
    capture_outbound();
}

function setupLDBButtons(){
    $('.ldb-board').click(function(){
        display_loading_screen()
        $.ajax({
            url: $(this).attr('href'),
            data: { format: 'json' },
            dataType: 'json',
            success: function(data){rebuildLDB($('#ldb'), data);clear_loading_screen();},
            error: ajax_failure
        })
        return false;
    })
    $('.ldb-board').addClass('has-ajax-handler')
}

$(function(){
    board = getParameterByName( 'board', window.location.href )
    if (board == '') { board = 'departures'; }
})