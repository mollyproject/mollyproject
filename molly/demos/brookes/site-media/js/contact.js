$(document).ready(function () {
    if (!window.query)
        return;
    
    if (page == page_count) {
        $('#more_contact_results').remove();
        $('#people').children().slice(-1).removeClass('round-bottom');
        return;
    }
    
    html  = '<input type="hidden" id="h_current_page" value="'+page+'"/>';
    html += '<input type="hidden" id="h_query" value="'+query+'"/>';
    html += '<input type="hidden" id="h_method" value="'+method+'"/>';
    html += '<a id="contacts_more" href="?page='+(page+1)+'&amp;method='+method+'&amp;q='+query_enc+'">More&hellip;</a>';
    html += '<img src="'+site_media+'gif/wait24trans.gif" width="24px" height="24px" style="display:none" id="wait_spinner"/>';

    $('#more_contact_results').html(html);
    
    $("#contacts_more").bind("click", function () {
        $("#contacts_more").hide();
        $("#wait_spinner").show();
        
        current_page = Number($('#h_current_page').val());
        query = $('#h_query').val();
        method = $('#h_method').val();
        
        jQuery.getJSON(base+'contact/', {
            q: query,
            method: method,
            page: current_page+1,
            format: 'json'
        }, function(data) {
            people = $('#people');
            method = data['method'];
            
            for (i in data['people']) {
                person = data['people'][i];
                
                if (method == 'email')
                    uri = 'mailto:'+person['email'];
                else
                    uri = 'tel:+44' + person['phone'][1].replace(' ', '').slice(1);
                name = person['name'];
                unit = person['unit'];
                
                html  = '<li>';
                html += '  <a class="'+method+'" href="'+uri+'">';
                html += '    <span class="name">'+name+'</span><br/>';
                html += '    <small><span class="unit">'+unit+'</span></small>';
                html += '  </a>';
                html += '</li>';
                
                new_person = $(html);
                new_person.appendTo(people);
                
            }
            
            if (data['page'] == data['page_count']) {
                $('.list-footer').hide();
            } else {
                $("#contacts_more").show();
                $("#wait_spinner").hide();
                current_page = Number($('#h_current_page').val());
                $('#h_current_page').val(current_page+1);
                
                new_person.addClass('round-bottom');
            }
                
        });
    
        return false;
    });
});