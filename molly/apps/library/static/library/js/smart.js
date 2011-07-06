function handleLibraryAJAX(data){
    library_ajax = null;
    $('.current-page').html(data.page.number)
    qs = '?title=' + getParameterByName('title', $('a.next').attr('href')) + '&amp;' +
         'author=' + getParameterByName('author', $('a.next').attr('href')) + '&amp;' +
         'isbn=' + getParameterByName('isbn', $('a.next').attr('href')) + '&amp;'
    
    if (data.page.has_next) {
        $('a.next').attr('href', qs + 'page=' + (data.page.number + 1).toString(10))
    } else {
        $('a.next').remove()
    }
    for (i in data.page.objects) {
        var item = data.page.objects[i]
        $('#item-list').append('<li><a href="/library/item:' + item.control_number + '/">' +
                               item.title + 
                               '</a></li>')
        if (item.author != null) $('#item-list li:last a').append('<br/><small><strong>' + gettext('Author') + ':</strong> ' + item.author + '</small>')
        if (item.publisher != null) $('#item-list li:last a').append('<br/><small><strong>' + gettext('Publisher') + ':</strong> ' + item.publisher + '</small>')
        if (item.edition != null) $('#item-list li:last a').append('<br/><small><strong>' + gettext('Edition') + ':</strong> ' + item.edition + '</small>')
        $('#item-list li:last a').append('<br/><small><strong>' + gettext('Libraries') + ':</strong> ' + item.holding_libraries + '</small>')
        if (i == 0) {
            $('#item-list li:last').addClass('page-break')
        }
    }
    $('.result-number').html($('#item-list li').length)
}

library_ajax = null;

$(document).bind('molly-page-change', function(event, url){
    
    if (library_ajax != null) {
        library_ajax.abort();
    }
    
    if (url.match(/^\/library\/search\//)) {
        $('a.next').click(function(){
            library_ajax = $.ajax({
                url: $(this).attr('href'),
                data: { format: 'json' },
                dataType: 'json',
                success: handleLibraryAJAX,
                error: ajax_failure
            })
            return false;
        })
        $('a.next').addClass('has-ajax-handler')
    }
    
});
