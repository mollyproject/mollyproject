function sendPosition(position, method) {
    $('#location_status').html('Location found; please wait while we put a name to it.');
        
    jQuery.post('/beta/core/ajax/update_location/', {
        longitude: position.coords.longitude,
        latitude: position.coords.latitude,
        accuracy: position.coords.accuracy,
        method: method,
    }, function(data) {
        $('#location_status').html('We think you are somewhere near <strong class="nobr">'+data+'</strong>.');
    });
}

function sendPositionError(error) {
    if (error.code == error.PERMISSION_DENIED) {
        $('#location_status').html(
            'You did not give permission for the site to know your location. '
          + 'You won\'t be asked again unless you initiate an automatic '
          + 'update using the link below.');
        jQuery.post('/core/ajax/update_location/', {
            method: 'denied',
        });
    } else if (error.code == error.POSITION_UNAVAILABLE) {
        $('#location_status').html(
            'We were unable to determine your location at this time. Please '
          + 'try again later, or enter your location manually.'
        );
    } else {
        $('#location_status').html(
            'An error occured while determining your location.'
        );
        jQuery.post('/core/ajax/update_location/', {
            method: 'error',
        });
    }
}

function requestPosition() {
    location_options = {
            enableHighAccuracy: true,
            maximumAge: 30000,
    }
    if (navigator.geolocation) {
        $('#location_status').html('Please wait while we attempt to determine your location...');
        navigator.geolocation.getCurrentPosition(function(position) {sendPosition(position, 'html5');}, sendPositionError, location_options);
    } else if (google.gears) {
        $('#location_status').html('Please wait while we attempt to determine your location...');
        var geo = google.gears.factory.create('beta.geolocation');
        if (geo.getPermission('Oxford Mobile Portal'))
            geo.getCurrentPosition(function(position) {sendPosition(position, 'gears');}, sendPositionError, location_options);
        else {
            sendPositionError({
                PERMISSION_DENIED: geo.PositionError.PERMISSION_DENIED,
                code: geo.PositionError.PERMISSION_DENIED,
            });
        }
    } else
        $('#location_status').html('We have no means of determining your location automatically.');
}

function positionMethodAvailable() {
    return (navigator.geolocation || google.gears)
}

if (require_location)
    jQuery(document).ready(requestPosition);

