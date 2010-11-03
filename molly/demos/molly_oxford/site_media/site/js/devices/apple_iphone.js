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