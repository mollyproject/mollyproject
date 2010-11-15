// Copyright 2007, Google Inc.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//
//  1. Redistributions of source code must retain the above copyright notice,
//     this list of conditions and the following disclaimer.
//  2. Redistributions in binary form must reproduce the above copyright notice,
//     this list of conditions and the following disclaimer in the documentation
//     and/or other materials provided with the distribution.
//  3. Neither the name of Google Inc. nor the names of its contributors may be
//     used to endorse or promote products derived from this software without
//     specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR IMPLIED
// WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
// MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
// EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
// SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
// PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
// OR BUSINESS INTERRUPTION) HOWEVER CAUgeolocation/update/SED AND ON ANY THEORY OF LIABILITY,
// WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
// OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
// ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
// Sets up google.gears.*, which is *the only* supported way to access Gears.
//
// Circumvent this file at your own risk!
//
// In the future, Gears may automatically define google.gears.* without this
// file. Gears may use these objects to transparently fix bugs and compatibility
// issues. Applications that use the code below will continue to work seamlessly
// when that happens.

(function() {
  // We are already defined. Hooray!
  if (window.google && google.gears) {
    return;
  }

  var factory = null;

  // Firefox
  if (typeof GearsFactory != 'undefined') {
    factory = new GearsFactory();
  } else {
    // IE
    try {
      factory = new ActiveXObject('Gears.Factory');
      // privateSetGlobalObject is only required and supported on IE Mobile on
      // WinCE.
      if (factory.getBuildInfo().indexOf('ie_mobile') != -1) {
        factory.privateSetGlobalObject(this);
      }
    } catch (e) {
      // Safari
      if ((typeof navigator.mimeTypes != 'undefined')
           && navigator.mimeTypes["application/x-googlegears"]) {
        factory = document.createElement("object");
        factory.style.display = "none";
        factory.width = 0;
        factory.height = 0;
        factory.type = "application/x-googlegears";
        document.documentElement.appendChild(factory);
      }
    }
  }

  // *Do not* define any objects if Gears is not installed. This mimics the
  // behavior of Gears defining the objects in the future.
  if (!factory) {
    return;
  }

  // Now set up the objects, being careful not to overwrite anything.
  //
  // Note: In Internet Explorer for Windows Mobile, you can't add properties to
  // the window object. However, global objects are automatically added as
  // properties of the window object in all browsers.
  if (!window.google) {
    google = {};
  }

  if (!google.gears) {
    google.gears = {factory: factory};
  }
})();



/************************************
 *        The following is          *
 * (C) University of Oxford 2009    *
 * E-mail: erewhon AT oucs.ox.ac.uk *
 ************************************/

/************************************
 *           Geolocation            *
 ************************************/

var positionRequestCount = 0;
var positionWatchId = null;
var positionInterface = null;
var positionMethod = null;
var positionGeo = null;
var manualUpdateLocation = null;



function sendPosition(position, final) {
    if (positionRequestCount == 1)
        $('.location-status').html('Location found; please wait while we put a name to it.');
    jQuery.post(base+'geolocation/', {
        longitude: position.coords.longitude,
        latitude: position.coords.latitude,
        accuracy: position.coords.accuracy,
        method: positionMethod,
        format: 'json',
        return_url: $('#return_url').val(),
        force: 'True',
    }, function(data) {
        oldPositionName = positionName;
        positionName = data.name;
        $('.location').html(data.name);
        $('.location-status').html('We think you are somewhere near <span class="location">'+data.name+'</span>.');
        if (oldPositionName == null && data.redirect)
            window.location.pathname = data.redirect;
    }, 'json');
}

function sendPositionError(error) {
    if (error.code == error.PERMISSION_DENIED) {
        $('.location-status').html(
            'You did not give permission for the site to know your location. '
          + 'You won\'t be asked again unless you initiate an automatic '
          + 'update using the link below.');
        jQuery.post(base+'geolocation/', {
            method: 'denied',
        });
    } else if (error.code == error.POSITION_UNAVAILABLE) {
        $('.location-status').html(
            'We were unable to determine your location at this time. Please '
          + 'try again later, or enter your location manually.'
        );
    } else {
        $('.location-status').html(
            'An error occured while determining your location.'
        );
        jQuery.post(base+'geolocation/', {
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
        $('.location-action').html(
            ' <a class="update-location-toggle" href="#" onclick="javascript:toggleUpdateLocation(); return false;">Update</a>');
    }
    
    sendPosition(position, positionWatchId != null);
}

function requestPosition() {
    $('.update-location').slideUp();
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
    
    positionRequestCount = 0;
    
    if (positionInterface) {
        $('.location-status').html('Please wait while we attempt to determine your location...');
        $('.location-action').html(
            ' <a class="update-location-cancel" href="#" onclick="javascript:cancelUpdateLocation(); return false;">Cancel</a>');
        positionWatchId = positionInterface.watchPosition(positionWatcher, sendPositionError, location_options);
    } else
        $('.location-status').html('We have no means of determining your location automatically.');
}

function positionMethodAvailable() {
    return ((window.navigator && navigator.geolocation) || (window.google && google.gears))
}

function toggleUpdateLocation(event) {
    updateLocationToggle = $('.update-location-toggle');
    
    if (updateLocationToggle.html() == 'Update') {
        $('.update-location').slideDown();
        updateLocationToggle.html('Cancel');
    } else {
        $('.update-location').slideUp();
        updateLocationToggle.html('Update');
    }
    return false;
}

function cancelUpdateLocation() {
    positionRequestCount = 11;
    if (positionName)
        $('.location-status').html('We think you are somewhere near <span class="location">'+positionName+'</span>.');
    else
        $('.location-status').html('We do not know where you are.');
    $('.location-action').html(
        ' <a class="update-location-toggle" href="#" onclick="javascript:toggleUpdateLocation(); return false;">Update</a>');

}

function cancelManualUpdateLocation() {
    positionRequestCount = 11;
    if (positionName)
        $('.location-status').html('We think you are somewhere near <span class="location">'+positionName+'</span>.');
    else
        $('.location-status').html('We do not know where you are.');
    $('.location-action').html(
        ' <a class="update-location-toggle" href="#" onclick="javascript:toggleUpdateLocation(); return false;">Update</a>');

    $('.update-location').slideUp('normal', function() {
        $('.manual-update-location').replaceWith(manualUpdateLocation);
    });
        
}

function manualLocationSubmit(event) {
    $('.manual-update-location-submit').css('display', 'none');
    
    $('.location-action').html(
            ' <a class="update-location-cancel" href="#" onclick="javascript:cancelManualUpdateLocation(); return false;">Cancel</a>');
    manualUpdateLocation = $('.manual-update-location').clone(true);
        
    $.post(base+'geolocation/', {
        method: 'geocoded',
        name: $('#location-name').val(),
        format: 'embed',
        return_url: $('#return_url').val(),
    }, function(data, textStatus, xhr) {
        if (xhr.getResponseHeader('X-Embed-Redirect') != null) {
            if (positionName == null)
                window.location.pathname = xhr.getResponseHeader('X-Embed-Redirect');
            positionName = xhr.getResponseHeader('X-Embed-Location-Name');
            $('.location').html(positionName);
            cancelManualUpdateLocation();
            return;
        }
        
        $('.manual-update-location').html(data);
        $('.submit-location-form').each(function () {
            button = $(this).find(".submit-location-form-button");
            link = $('<a href="#">'+button.html()+'</a>');
            link.css('color', '#ffffff').bind('click', {form:this}, function(event) {
                form = $(event.data.form);
                $.post(base+'geolocation/', {
                    longitude: form.find('[name=longitude]').val(),
                    latitude: form.find('[name=latitude]').val(),
                    accuracy: form.find('[name=accuracy]').val(),
                    name: form.find('[name=name]').val(),
                    return_url: form.find('[name=return_url]').val(),
                    method: 'geocoded',
                    format: 'json',
                    force: 'True'
                }, function(data) {
                    oldPositionName = positionName;
                    positionName = form.find('[name=name]').val();
                    $('.location').html(positionName);
                    cancelManualUpdateLocation();
                    if (oldPositionName == null && data.redirect)
                        window.location.pathname = data.redirect;
                }, 'json');
                return false;
            });
            button.replaceWith(link);
        });
    });

    return false;
}
    
if (require_location)
    jQuery(document).ready(requestPosition);


$(document).ready(function() {
    $('.update-location').css('display', 'none');
    $('.location-action').html(
        ' <a class="update-location-toggle" href="#" onclick="javascript:toggleUpdateLocation(); return false;">Update</a>');
      
    if (positionMethodAvailable()) {
        $('#geolocate-js').html(
            '<a href="#" onclick="javascript:requestPosition(); return false;">Determine location automaticaly</a>');
    }
    
    $('.manual-update-form').bind('submit', manualLocationSubmit);
    $('.manual-update-form').bind('submit', function(){ return false; });
    
    if (require_location && positionMethodAvailable())
        $('#location_status').html('We do not yet have a location for you; please wait while we attempt to determine one.');
    else if (positionMethodAvailable())
        $('#location_status').css('display', 'none');
   
});