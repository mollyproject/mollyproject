/************************************
 * (C) University of Oxford 2009    *
 * E-mail: erewhon AT oucs.ox.ac.uk *
 ************************************/

var positionRequestCount = 0;
var positionWatchId = null;
var positionInterface = null;
var positionMethod = null;
var positionGeo = null;

function sendPosition(position, final) {
    if (positionRequestCount == 1)
        $('#location_status').html('Location found; please wait while we put a name to it.');
        
    jQuery.post(base+'ajax/update_location/', {
        longitude: position.coords.longitude,
        latitude: position.coords.latitude,
        accuracy: position.coords.accuracy,
        method: positionMethod,
    }, function(data) {
        accuracy = Math.round(position.coords.accuracy);
        $('#location_status').html('We think you are somewhere near <strong class="nobr">'+data+'</strong> (to approximately <strong>'+accuracy+'</strong> metres).');
        
        $('.location_name').html(data);
    });
}

function sendPositionError(error) {
    if (error.code == error.PERMISSION_DENIED) {
        $('#location_status').html(
            'You did not give permission for the site to know your location. '
          + 'You won\'t be asked again unless you initiate an automatic '
          + 'update using the link below.');
        jQuery.post(base+'ajax/update_location/', {
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
        jQuery.post(base+'ajax/update_location/', {
            method: 'error',
        });
    }
}

function getGearsPositionInterface(name) {
    if (positionGeo == null)
        positionGeo = google.gears.factory.create('beta.geolocation');
    geo = positionGeo;
    
    function wrapWithPermission(fname) {
        return function(successCallback, errorCallback, options) {
            if (geo.getPermission(name)) {
                if (fname == 'gcp')
                    return geo.getCurrentPosition(successCallback, errorCallback, options);
                else
                    return geo.watchPosition(successCallback, errorCallback, options);
            } else
                errorCallback({
                    PERMISSION_DENIED: geo.PositionEror.PERMISSION_DENIED,
                    code: geo.PositionError.PERMISSION_DENIED,
                });
        };
    }
    
    return {
        getCurrentPosition: wrapWithPermission('getCurrentPosition'),
        watchPosition: wrapWithPermission('watchPosition'),
        clearWatch: function(id) {
            geo.clearWatch(id);
        },
    }
}

function positionWatcher(position) {
    positionRequestCount += 1;
    if (positionRequestCount > 10 || position.coords.accuracy <= 150 || position.coords.accuracy == 18000) {
        positionInterface.clearWatch(positionWatchId);
        positionWatchId = null;
    }
    
    sendPosition(position, positionWatchId != null);
}

function requestPosition() {
    if (positionWatchId != null)
        return; 
        
    location_options = {
            enableHighAccuracy: true,
            maximumAge: 30000,
    }
    if (window.google && google.gears) {
        positionInterface = getGearsPositionInterface('Oxford Mobile Portal');
        positionMethod = 'gears';
    } else if (window.navigator && navigator.geolocation) {
        positionInterface = navigator.geolocation;
        positionMethod = 'html5';
    }
    
    $('#location_status').css('display', 'block');
    if (positionInterface) {
        $('#location_status').html('Please wait while we attempt to determine your location...');
        positionWatchId = positionInterface.watchPosition(positionWatcher, sendPositionError, location_options);
    } else
        $('#location_status').html('We have no means of determining your location automatically.');
}

function positionMethodAvailable() {
    return ((window.navigator && navigator.geolocation) || (window.google && google.gears))
}

if (require_location)
    jQuery(document).ready(requestPosition);

function resetDimensions() {
    return;
    
    h = window.innerHeight - $('.content').offset().top;
    //$('#page_title').html(window.innerWidth + ' ' + ($('body').hasClass('landscape') ? 'land' : 'port') + ' ' + $('.map_pane').width() + ' ' + $('.content').height());
    
    if (window.orientation == 0 || window.orientation == 180)
        $('.map_pane').css('height', 200);
    else
        $('.map_pane').css('height', h);
        
    //$('.details_pane').css('width', $('.map_pane').width()-4);
}


function do_location_update() {
    $(document.body).append('<div id="location_update_background" style="position:absolute; left:0; top:0; width:100%; height:'+$(document).attr('height')+'px; background-color:#fff; opacity:0.75"> </div>');

    width = Math.min(window.innerWidth - 15, 300);
    height = Math.min(window.innerHeight, 300);
    top = Math.min((window.innerHeight - height) / 2, 50);
    left = (window.innerWidth - width) / 2;
    

    $(document.body).append(
        '<div id="location_update_container" style="position:fixed; width:'+width+'px; left:'+left+'px; top:'+top+'px; border-radius:10px; -moz-border-radius:10px; -webkit-border-radius:10px; border:solid 0px #fff;">'
      + '  <ul class="popup-tabs">'
      + '    <li><a href="#" onclick="javascript:show_tab(\'auto\');">Auto</a></li>'
      + '    <li><a href="#" onclick="javascript:show_tab(\'manual\');">Manual</a></li>'
//      + '    <li><a href="#" onclick="javascript:show_tab(\'map\');">Map</a></li>'
      + '    <li class="not-tab"><a href="#" onclick="javascript:close_location_update();">Close</a></li>'
      + '  </ul>'
      + '  <div id="location_update_box">'
      + '    <div class="wait-tab"> </div>' 
      + '  </div>'
      + '</div>');
    
    $.get(base+'update_location/', {
        ajax: true,
    }, function(data) {
        $('#location_update_box').html(data);
        $('#manual_location_form').bind('submit', manual_location_submit);
        show_tab('auto');
    });
    
    return false;
};

function show_tab(name) {
    $('.tab').hide();
    $('#tab-'+name).show();
}

function manual_location_submit() {
    $.get(base+'update_location/', {
        ajax: true,
        location: $('#location').val(),
    }, function(data) {
        $('#tab-manual').html(data);
        $('.submit-location-form').bind('submit', manual_location_confirm);
    });
    $('#tab-manual').html('<div class="wait-tab"> </div>');
    return false;
}

function manual_location_confirm() {
    form = $(this);
    $.post(base+'update_location/', {
        ajax: 'true',
        title: form.find("[name='title']").val(),
        latitude: form.find("[name='latitude']").val(),
        longitude: form.find("[name='longitude']").val(),
        accuracy: form.find("[name='accuracy']").val(),
        no_redirect: 'true',
    }, function(data) {
        $('#tab-manual').html('<h2 class="section-header">Update manually</h2><div class="section-content">Your location has been updated successfully.</div></div>');
        $('.location_name').html(form.find("[name='title']").val());
    });
    $('#tab-manual').html('<div class="wait-tab"> </div>');
    return false;
}
        

function close_location_update() {
    $('#location_update_container').remove();
    $('#location_update_background').remove();
}

$(document).ready(function () {
    $('a.location_update_link').bind('click', do_location_update);
    $('#manual_location_form').bind('submit', manual_location_submit);
    $('.submit-location-form').bind('submit', manual_location_confirm);
});