/* Consistent asynchronous page loading */

var current_url = window.location.pathname;

/* This is a work around for the back button being broken in Opera
 * http://www.opera.com/support/kb/view/827/
 */
history.navigationMode = 'compatible';

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

function display_loading_screen(){
    $('body').append('<div id="loading"></div>')
    $('#loading').height($('html').height())
    display_spinner()
}

/* reposition the spinner when the page is scrolled - on iPhone only */
function display_spinner(){
    offset = window.innerHeight / 2
    if (navigator.userAgent.match(/iPhone/i) ||
        navigator.userAgent.match(/iPod/i) ||
        navigator.userAgent.match(/iPad/i)) {
        offset += window.pageYOffset
    }
    $('#loading').css('background-position', '50% ' + offset + 'px')
}

$(window).scroll(display_spinner)

function clear_loading_screen(){
    $('#loading').remove();
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
                clear_loading_screen();
            }, 1200);
        });
}

function async_load(url, query, meth) {
    
    /* Don't attempt AJAX for offsite links */
    if (to_absolute(url).substr(0, base.length) != base) {
        return true;
    }
    
    display_loading_screen()
  
    query['format'] = 'fragment';
    $.ajax({
            'url': to_absolute(url),
            'data': query,
            'type': meth,
            'dataType': 'json',
            'success': function(data, textStatus, xhr) {
                current_url = data.uri;
                // Detect if history API is available - http://diveintohtml5.org/detect.html#history
                if (!!(window.history && history.pushState)) {
                    history.pushState(null, null, to_absolute(current_url))
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

$(window).load(function() {
    function check_hash_change(){
        if (window.location.hash && window.location.hash.substr(1) != current_url) {
            async_load(window.location.hash.substr(1), {}, "GET");
        }
        if (typeof(window.opera)!='undefined'){
            setTimeout(check_hash_change, 100);
        }
    }
    check_hash_change();
    $(document).trigger('molly-page-change', [current_url])
    capture_outbound();
    
    if (!!(window.history && history.pushState)) {
      window.addEventListener('popstate', function(e, state){
        if (current_url != window.location.pathname) {
          async_load(window.location.href, {}, 'GET');
        }
      }, false)
    }
});

