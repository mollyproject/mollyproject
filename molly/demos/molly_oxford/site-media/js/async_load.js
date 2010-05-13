/* Consistent asynchronous page loading */

var current_url = "";

function to_absolute(url) {
    if (url.match(/http\:\/\//)) {
        // console.log("http://");
        return url;
    } else if (url.substr(0, 1) == "/") {
        // console.log("abs");
        return base + url.substr(1);
    } else if (url.indexOf('?') != -1) {
        // console.log("qs");
        if (current_url.lastIndexOf('?') != -1) {
            return current_url.substring(0, current_url.lastIndexOf('?')) + url;
        }
        return current_url + url;
    } else {
        // console.log("rel, with current " + current_url);
        return current_url + url;
    }
}

// Callback method that swaps in the asynchronously loaded bits to the page, and fades it in
function async_load_callback(data, textStatus, xhr) {
    jQuery('body').html(data.body);
    jQuery('#loading-bg').css({'opacity': 0.75}).show();
    jQuery('title').html(data.title);
    jQuery('.content').html(data.content);
    capture_outbound();
    jQuery('#loading-bg').fadeTo('fast', 0, function() {
        jQuery('#loading-bg').hide();
        jQuery('html, body').animate({'scrollTop': 0}, 100);
    });
}

function async_load(url, query, meth) {
    query['format'] = 'fragment';
    /* console.log("Async loading " + url);
    console.log("    aka " + to_absolute(url));
    console.log("    with " + query);
    console.log("    meth " + meth); */
    var settings = {'url': to_absolute(url), 'data': query, 'type': meth, 'dataType': 'json'};

    settings['success'] = function(data, textStatus, xhr) {
        var abs_url = to_absolute(url);
        current_url = abs_url;
        console.log("Current URL now " + current_url)
        window.location.hash = current_url;
        return async_load_callback(data, textStatus, xhr);
    };
    settings['error'] = function(xhr, textStatus, errorThrown) {
        jQuery('#loading-bg')
            .html('<p style="position:fixed; top: 10%; width:100%; margin:0 auto; text-align:center;">Error loading page - please try again.</p>')
            .css({'font-size': '20px', 'font-weight': 'bold'})
            .fadeTo('fast', 0.9, function() {
                setTimeout(function() {
                    jQuery('#loading-bg').fadeTo('fast', 0, function () {
                        jQuery('#loading-bg').hide();
                    });
                }, 1200);
            });
    };

    jQuery.ajax(settings);
    jQuery('#loading-bg').show().fadeTo('fast', 0.75)
    return false;
}

function capture_outbound()  {
    // Intercept all forms
    jQuery('form').submit(function(evt) {
            var serial = jQuery(this).serializeArray();
            var datamap = {}
            var i = 0;
            for (i = 0; i < serial.length; i++) {
                datamap[serial[i].name] = serial[i].value;
            }
            return async_load(jQuery(this).attr('action'), datamap, jQuery(this).attr('method'));
        });
    console.log("Captured outbound forms");
    // Intercept all links with an href
    jQuery('a[href]').click(function(evt) {
            return async_load(jQuery(this).attr('href'), {}, 'GET');
        });
    console.log("Captured outbound links");
}

jQuery(document).ready(function() {
    if (window.location.hash != current_url) {
        console.log("Hash mismatch! " + window.location.hash + " != " + current_url + "! Reloading...");
        async_load(window.location.hash.substr(1), {}, "GET");
    }
    capture_outbound();
});

