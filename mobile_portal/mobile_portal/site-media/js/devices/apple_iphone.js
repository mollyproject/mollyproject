$(document).ready(function () {
    $("#hide_itunesu_link").bind("click", function() {
        $('#itunesu_link_div').slideUp();
        
        if ($('#remember:checked').length)
            jQuery.post('/podcasts/itunesu_redirect/', {
                remember: true,
                cancel: true,
                no_redirect: true,
            }); 
        return false;
    });
});

$(document).ready(function () {
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
                
                new_person.addClass('notbottom');
            }
                
        });
    
        return false;
    });
});

function rotateScreen() {
	switch(window.orientation)
	{
		case 0:
		case 180:
			$('body').toggleClass('portrait', true);
			$('body').toggleClass('landscape', false);
		break;

		case -90:
		case 90:
			$('body').toggleClass('portrait', false);
			$('body').toggleClass('landscape', true);
		break;

	}
	//$('body').toggleClass('landscape', true)

	setTimeout(scrollToTop, 500);
}



jQuery(document).ready(rotateScreen);

function scrollToTop() {
    window.scrollTo(0,1);
    resetDimensions();
}

window.onresize = resetDimensions;
window.onorientationchange = rotateScreen;