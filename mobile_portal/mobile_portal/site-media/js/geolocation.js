function sendPosition(position, method) {
    $('#location_status').html('Location found; please wait while we put a name to it.');
    
    if (position.coords) {
        position = position.coords;
    }
        
    jQuery.post('/core/ajax/update_location/', {
        longitude: position.longitude,
        latitude: position.latitude,
        method: method,
    }, function(data) {
        $('#location_status').html('We think you are somewhere near <strong class="nobr">'+data+'</strong>.');
    });
}

function sendPositionError(error) {
    $('#location_status').css('display', 'none');
}

function requestPosition() {
    if (navigator.geolocation) {
        $('#location_status').html('Please wait while we attempt to determine your location...');
        location_options = {
            enableHighAccuracy: true,
            maximumAge: 30000,
        }
        navigator.geolocation.getCurrentPosition(function(position) {sendPosition(position, 'html5');}, sendPositionError, location_options);
    } else if (google.gears) {
        $('#location_status').html('Please wait while we attempt to determine your location...');
        var geo = google.gears.factory.create('beta.geolocation');
        geo.getCurrentPosition(function(position) {sendPosition(position, 'gears');}, sendPositionError);
    } else
        $('#location_status').html('We have no means of determining your location automatically.');
}

function positionMethodAvailable() {
    return (navigator.geolocation || google.gears)
}

if (require_location)
    jQuery(document).ready(requestPosition);

