// http://stackoverflow.com/questions/901115/get-querystring-values-with-jquery
function getParameterByName( name, qs ){
  
    name = name.replace(/[\[]/,"\\\[").replace(/[\]]/,"\\\]");
    var regexS = "[\\?&]"+name+"=([^&#]*)";
    var regex = new RegExp( regexS );
    var results = regex.exec( qs );
    if ( results == null ) {
        return "";
    }
    else {
        return results[1].replace(/\+/g, " ");
    }
}

function handleLibraryAJAX(data){
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
        if (item.author != null) $('#item-list li:last a').append('<br/><small><strong>Author:</strong> ' + item.author + '</small>')
        if (item.publisher != null) $('#item-list li:last a').append('<br/><small><strong>Publisher:</strong> ' + item.publisher + '</small>')
        if (item.edition != null) $('#item-list li:last a').append('<br/><small><strong>Edition:</strong> ' + item.edition + '</small>')
        $('#item-list li:last a').append('<br/><small><strong>Libraries:</strong> ' + item.holding_libraries + '</small>')
        if (i == 0) {
            $('#item-list li:last').addClass('page-break')
        }
    }
    $('.result-number').html($('#item-list li').length)
}

$(document).bind('molly-page-change', function(event, url){
    
    if (url.match(/^\/library\/search\//)) {
        $('a.next').click(function(){
            $.ajax({
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
