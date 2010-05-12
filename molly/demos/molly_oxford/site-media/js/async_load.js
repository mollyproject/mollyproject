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
function load_callback(data, textStatus, xhr) {
    $('body').html(data.body);
    $('title').html(data.title);
    $('.content').html(data.content);
    $('#loading').hide()
    capture_outbound();
    $('body').fadeTo('fast', 1);
}

function ajax_load(url, query, meth) {
    query['format'] = 'fragment';
    console.log("Async loading " + url);
    console.log("    aka " + to_absolute(url));
    console.log("    with " + query);
    console.log("    meth " + meth);
    var settings = {'url': to_absolute(url), 'data': query, 'type': meth, 'dataType': 'json'};
    settings['success'] = function(data, textStatus, xhr) {
        var abs_url = to_absolute(url);
        current_url = abs_url;
        console.log("Current URL now " + current_url)
        window.location.hash = current_url;
        return load_callback(data, textStatus, xhr);
    };
    $.ajax(settings);
    $('body').fadeTo('fast', 0.1);
    $('#loading').css({'position': 'fixed', 'top': '30%', 'left': '50%', 'opacity': '0.8'}).show()
    $('#loading').fadeIn('fast');
    return false;
}

function capture_outbound()  {
    // Intercept all forms
    $('form').submit(function(evt) {
            var serial = $(this).serializeArray();
            var datamap = {}
            var i = 0;
            for (i = 0; i < serial.length; i++) {
                datamap[serial[i].name] = serial[i].value;
            }
            return ajax_load($(this).attr('action'), datamap, $(this).attr('method'));
        });
    // Intercept all links with an href
    $('a[href]').click(function(evt) {
            return ajax_load($(this).attr('href'), {}, 'GET');
        });
}

$(document).ready(function() {
    if (window.location.hash != current_url) {
        console.log("Hash mismatch! " + window.location.hash + " != " + current_url + "! Reloading...");
        ajax_load(window.location.hash.substr(1), {}, "GET");
    }
    capture_outbound();
});

