function refreshTransport(data){
    $('#park_and_rides .section-content').empty()
    for (var i in data.park_and_rides) {
        var entity = data.park_and_rides[i]
        $('#park_and_rides .section-content').append('<div class="park-and-ride"><h3><a href="' + entity._url + '">' + entity.title + '</a></h3></div>')
        if (entity.metadata.park_and_ride) {
            if (entity.metadata.park_and_ride.unavailable) {
                spaces = '?'
                $('.park-and-ride:last').append('<p><em>Space information currently unavailable</em></p>')
            } else {
                $('.park-and-ride:last').append('<div class="capacity-bar"><div style="width: ' + entity.metadata.park_and_ride.percentage.toString() + '%; height:7px;background-color: #960300;">&nbsp;</div></div>')
                spaces = entity.metadata.park_and_ride.spaces.toString()
            }
            $('.park-and-ride:last').append('<p>Spaces: ' + spaces + ' / ' + entity.metadata.park_and_ride.capacity + '</p>')
        }
        if (i < data.park_and_rides.length - 1 || i%2 == 0) {
            $('.park-and-ride:last').css('float', 'left')
        }
        if (i%2 == 0) {
            $('.park-and-ride:last').css('clear', 'left')
        }
    }
}

function ajaxTransportUpdate(){
    $.ajax({
        url: window.location.href,
        data: { format: 'json' },
        dataType: 'json',
        success: refreshTransport
    })
}