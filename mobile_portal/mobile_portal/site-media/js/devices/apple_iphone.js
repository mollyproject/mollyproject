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