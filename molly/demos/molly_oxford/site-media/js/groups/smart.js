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

function sendPosition(position, final, statusTarget) {
    if (positionRequestCount == 1)
        statusTarget.html('Location found; please wait while we put a name to it.');
    jQuery.post(base+'geolocation/', {
        longitude: position.coords.longitude,
        latitude: position.coords.latitude,
        accuracy: position.coords.accuracy,
        method: positionMethod,
        format: 'json',
        return_url: $('#return_url').val(),
        force: 'True',
    }, function(data) {
        oldLocationName = locationName;
        locationName = data.name;
        $('.location').html(data.name);
        if (oldLocationName == null && data.redirect)
            window.location.pathname = data.redirect;
    }, 'json');
}

function sendPositionError(error, statusTarget) {
    if (error.code == error.PERMISSION_DENIED) {
        statusTarget.html(
            'You did not give permission for the site to know your location. '
          + 'You won\'t be asked again unless you initiate an '
          + 'update using the icon to the right.');
        jQuery.post(base+'geolocation/', {
            method: 'denied',
        });
    } else if (error.code == error.POSITION_UNAVAILABLE) {
        statusTarget.html(
            'We were unable to determine your location at this time. Please '
          + 'try again later, or enter your location manually.'
        );
    } else {
        statusTarget.html(
            'An error occured while determining your location.'
        );
        jQuery.post(base+'geolocation/', {
            method: 'error',
        });
    }
    window.setTimeout(function() {
        p.find('.location').text(locationName);
    }, 5000);
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

function positionWatcher(position, statusTarget) {
    positionRequestCount += 1;
    if (positionRequestCount > 10 || position.coords.accuracy <= 150 || position.coords.accuracy == 18000) {
        positionInterface.clearWatch(positionWatchId);
        positionWatchId = null;
    }

    sendPosition(position, positionWatchId != null, statusTarget);
}

function positionMethodAvailable() {
    return ((window.navigator && navigator.geolocation) || (window.google && google.gears))
}

$.fn.selectAll = function() {
  return this.each(function() {
    start = 0; end = this.value.length;
    if(this.setSelectionRange) {
      this.focus();
      this.setSelectionRange(start, end);
    } else if(this.createTextRange) {
      var range = this.createTextRange();
      range.collapse(true);
      range.moveEnd('character', end);
      range.moveStart('character', start);
      range.select();
    }
  });
};

function positionMethodAvailable() {
  return ((window.navigator && navigator.geolocation) || (window.google && google.gears))
}

function wrapWithArg(f, new_arg) {
  function g(arg) {
    return f(arg, new_arg);
  }
  return g;
}

function geolocate() {
    p = $(this).closest('div');
    l = p.find('.location');
    if (positionWatchId != null)
        return;

    location_options = {
            enableHighAccuracy: true,
            maximumAge: 30000,
    }
    if (window.google && google.gears) {
        positionInterface = getGearsPositionInterface('Mobile Oxford');
        positionMethod = 'gears';
    } else if (window.navigator && navigator.geolocation) {
        positionInterface = navigator.geolocation;
        positionMethod = 'html5';
    }

    l.css('display', 'block');
    p.find('.location-form').css('display', 'none');
    if (positionInterface) {
        l.html('Please wait while we attempt to determine your location&hellip;');
        positionInterface.statusTarget = l;
        positionWatchId = positionInterface.watchPosition(wrapWithArg(positionWatcher, l), wrapWithArg(sendPositionError, l), location_options);
    } else
        l.html('We have no means of determining your location automatically.');
}

function cancelGeolocate() {
    if (positionWatchId == null)
        return;
    positionInterface.clearWatch(positionWatchId);
    positionWatchId = null;
    positionInterface = null;
    $('.location').html((locationName != null) ? locationName : "No location set.");
}
    
function manualLocation(e) {
  cancelGeolocate();
  p = $(this).closest('div');
  if (p.find('.location').css('display') == 'block')
    return false;
  p.find('.location-form').css('display', 'none');
  p.find('.location').css('display', 'block')

  newLocationName = p.find('.location-name').val() || null;
  if (locationName != newLocationName) {
    p.find('.location').html('<i>Updating&hellip;</i>');
    $.post(base+'geolocation/', {
      format: 'json',
      name: newLocationName,
      method: 'geocoded',
    }, function(data) {
      if (data.name) {
        locationName = data.name;
        $('.location').text(data.name);
      } else {
        p.find('.location').html("<i>"+data.error+"</i>"); 
        window.setTimeout(function() {
          p.find('.location').text(locationName);
        }, 5000);
      }
    });
  }
  return false;
}

$(function() {
  $('.location-form').css('display', 'none').submit(manualLocation);
  $('.location-submit').css('display', 'none');
  $('.location-name').css('width', '100%');

  $('.location-box').each(function() {
    var p = $(this);
    if (positionMethodAvailable()) {
      p.append($('<span style="position:absolute; right:10px; top:4px; font-size:30px; color:#0000ff; cursor:pointer;">↻</span>').click(geolocate));
    }
    p.find('.location').append(" <small>Select to edit</small>").click(function() {
      $(this).css('display', 'none');
      p.find('.location-form').css('display', 'block');
      p.find('.location-name').focus().blur(manualLocation).val(locationName).selectAll();
    }).css('display', 'block').css('cursor', 'pointer');
  });
  if (locationRequired && positionMethodAvailable())
    geolocate();
});
