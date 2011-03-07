function capfirst(s) {
    return s.substr(0,1).toUpperCase() + s.substr(1)
}
    
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
                    '<li><a href="nearby/' + entity_type.slug + '/">' + 
                    capfirst(entity_type.verbose_name_plural) +
                    ' <small>(' + entity_type.entities_found + ' within ' + Math.ceil(entity_type.max_distance/10)*10 + 'm)</small>' +
                    '</a></li>')
            } else {
                $('#poi-category-selector ul:last').append(
                    '<li><a href="category/' + entity_type.slug + '/">' + 
                    capfirst(entity_type.verbose_name_plural) +
                    '</a></li>')
            }
        }
    }
    $('#poi-category-selector ul').addClass('no-round-bottom')
    $('#poi-category-selector ul:last').removeClass('no-round-bottom')
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
            data: { format: 'json' },
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