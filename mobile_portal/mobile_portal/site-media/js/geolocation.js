/************************************
 * (C) University of Oxford 2009    *
 * E-mail: erewhon AT oucs.ox.ac.uk *
 ************************************/

var positionRequestCount = 0;
var positionWatchId = null;
var positionInterface = null;
var positionMethod = null;

function sendPosition(position) {
    $('#location_status').html('Location found; please wait while we put a name to it.');
        
    jQuery.post(base+'core/ajax/update_location/', {
        longitude: position.coords.longitude,
        latitude: position.coords.latitude,
        accuracy: position.coords.accuracy,
        method: positionMethod,
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

function getGearsPositionInterface(name) {
    var geo = google.gears.factory.create('beta.geolocation');
    
    function wrapWithPermission(f) {
        return function(successCallback, errorCallback, options) {
            if (geo.getPermission(name))
                    return f(successCallback, errorCallback, options);
                else
                    errorCallback({
                        PERMISSION_DENIED: geo.PositionEror.PERMISSION_DENIED,
                        code: geo.PositionError.PERMISSION_DENIED,
                    });
        };
    }
    
    return {
        getCurrentPosition: wrapWithPermission(geo.getCurrentPosition),
        watchPosition: wrapWithPermission(geo.watchPosition),
        clearWatch: geo.clearWatch,
    }
}

function positionWatcher(position) {
    if (positionRequestCount > 10 || position.coords.accuracy <= 150 || position.coords.accuracy == 18000)
        positionInterface.clearWatch(positionWatchId);
    positionRequestCount += 1;
    
    sendPosition(position);
}

function requestPosition() {
    location_options = {
            enableHighAccuracy: true,
            maximumAge: 30000,
    }
    if (navigator.geolocation) {
        positionInterface = navigator.geolocation;
        positionMethod = 'html5';
    } else if (google.gears) {
        positionInterface = getGearsPositionInterface('Oxford Mobile Portal');
        positionMethod = 'gears';
    }
    
    if (positionInterface) {
        $('#location_status').html('Please wait while we attempt to determine your location...');
        positionWatchId = positionInterface.watchPosition(positionWatcher, sendPositionError, location_options);
    } else
        $('#location_status').html('We have no means of determining your location automatically.');
}

function positionMethodAvailable() {
    return (navigator.geolocation || google.gears)
}

if (require_location)
    jQuery(document).ready(requestPosition);

function resetDimensions() {
    
    h = window.innerHeight - $('.content').offset().top;
    //$('#page_title').html(window.innerWidth + ' ' + ($('body').hasClass('landscape') ? 'land' : 'port') + ' ' + $('.map_pane').width() + ' ' + $('.content').height());
    
    if (window.orientation == 0 || window.orientation == 180)
        $('.map_pane').css('height', 200);
    else
        $('.map_pane').css('height', h);
        
    //$('.details_pane').css('width', $('.map_pane').width()-4);
}

