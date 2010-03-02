
$(document).ready(function() {

    $('input[type!=submit]').css('display', 'none');

    $('.front_page_links tbody td.displayed').map(function (i, e) {
        set = $(e).children()[0].checked ? 'on' : 'off';
        displayedClass = set=='on' ? ' class="is_displayed"' : '';
        $(e).append('<img id="displayed-'+i+'"'+displayedClass+' src="'+site_media+'/gif/check-'+set+'.gif" onclick="javascript:toggleDisplayed('+i+');"/>');
    });

    $('.front_page_links tbody td.order').map(function (i, e) {
        $(e).append('<img src="'+site_media+'/gif/up.gif" onclick="javascript:moveUp('+i+');"/>'
                + '<img src="'+site_media+'/gif/down.gif" onclick="javascript:moveDown('+i+');"/>');
    });

});

function toggleDisplayed(i) {
    e = $('#displayed-'+i);
    
    e.toggleClass('is_displayed');
    set = e.hasClass('is_displayed');

    e.attr('src', site_media+'/gif/check-' + (set ? 'on' : 'off') + '.gif');
    
    // Set or unset the relevant checkbox
    $('#id_'+i+'-displayed').attr('checked', set);
}

function moveUp(i) {
    tr = $('#displayed-'+i).parent().parent();
    cur_val = tr.find('input[type=text]').attr('value');
    if (cur_val == '1') return;
    next_val = tr.prev().find('input[type=text]').attr('value');
    tr.find('#id_'+i+'-order').attr('value', function() {return this.value-1;});
    tr.prev().insertAfter(tr).find('input[type=text]').attr('value', function() {return parseFloat(this.value)+1;});
}

function moveDown(i) {
    tr = $('#displayed-'+i).parent().parent();
    cur_val = tr.find('input[type=text]').attr('value');
    next_val = tr.next().find('input[type=text]').attr('value');
    tr.find('#id_'+i+'-order').attr('value', next_val);
    tr.next().insertBefore(tr).find('input[type=text]').attr('value', cur_val);
}

