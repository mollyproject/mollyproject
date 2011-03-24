/* Consistent asynchronous page loading */

var current_url = window.location.pathname;

function to_absolute(url) {
    if (url.match(/https?\:\/\//)) {
        return url;
    } else if (url.substr(0, 1) == "/") {
        return window.location.protocol + '//' + window.location.host + url;
    } else if (url.indexOf('?') != -1) {
        if (current_url.lastIndexOf('?') != -1) {
            return current_url.substring(0, current_url.lastIndexOf('?')) + url;
        }
        return current_url + url;
    } else {
        return current_url + url;
    }
}

// Callback method that swaps in the asynchronously loaded bits to the page, and fades it in
function async_load_callback(data, textStatus, xhr) {
    $('body').html(data.body);
    $('title').html(data.title);
    $(document).trigger('molly-page-change', [current_url])
    capture_outbound();
}

function ajax_failure() {
    $('#loading')
        .html('<p style="position:fixed; top: 10%; width:100%; margin:0 auto; text-align:center;">Error loading page - please try again.</p>')
        .css({'font-size': '20px', 'font-weight': 'bold'})
        .fadeTo('fast', 0.9, function() {
            setTimeout(function() {
                $('#loading').fadeTo('fast', 0, function () {
                    $('#loading').remove();
                });
            }, 1200);
    });
}

function async_load(url, query, meth) {
    
    /* Don't attempt AJAX for offsite links */
    if (to_absolute(url).substr(0, base.length) != base) {
        return true;
    }
    
    $('body').append('<div id="loading"></div>')
  
    query['format'] = 'fragment';
    $.ajax({
            'url': to_absolute(url),
            'data': query,
            'type': meth,
            'dataType': 'json',
            'success': function(data, textStatus, xhr) {
                var abs_url = to_absolute(url);
                current_url = abs_url.substr(base.length - 1);
                // Detect if history API is available - http://diveintohtml5.org/detect.html#history
                if (!!(window.history && history.pushState)) {
                    history.pushState(null, null, abs_url)
                } else {
                    window.location.hash = current_url;
                }
                return async_load_callback(data, textStatus, xhr);
            },
            'error': ajax_failure
        });
    return false;
}

function capture_outbound()  {
    // Intercept all forms
    $('form:not(.has-ajax-handler)').unbind('submit')
    $('form:not(.has-ajax-handler)').submit(function(evt) {
            var serial = $(this).serializeArray();
            var datamap = {}
            var i = 0;
            for (i = 0; i < serial.length; i++) {
                datamap[serial[i].name] = serial[i].value;
            }
            return async_load($(this).attr('action'), datamap, $(this).attr('method'));
        });
    
    // Intercept all links with an href
    $('a[href]:not(.has-ajax-handler)').unbind('click')
    $('a[href]:not(.has-ajax-handler)').click(function(evt) {
            return async_load($(this).attr('href'), {}, 'GET');
        });
}

$(function() {
    if (window.location.hash && window.location.hash != current_url) {
        async_load(window.location.hash.substr(1), {}, "GET");
    }
    $(document).trigger('molly-page-change', [current_url])
    capture_outbound();
    
    if (!!(window.history && history.pushState)) {
      window.addEventListener('popstate', function(e){
        if (current_url != window.location.pathname) {
          async_load(window.location.href, {}, 'GET');
        }
      })
    }
});

