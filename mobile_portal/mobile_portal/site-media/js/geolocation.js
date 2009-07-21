function sendPosition(position) {
    jQuery.post('/beta/core/ajax/update_location/', {
        longitude: position.coords.longitude,
        latitude: position.coords.latitude,
    }, function(data) {
        $('#location_status').html('We think you are somewhere near <strong class="nobr">'+data+'</strong>.');
    });
}

function sendPositionError(error) {
    $('#location_status').css('display', 'none');
}

function requestPosition() {
    navigator.geolocation.getCurrentPosition(sendPosition, sendPositionError);
}


if (require_location)
    jQuery(document).ready(requestPosition);

