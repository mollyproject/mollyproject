// Handle auto-updating of the webcam

webcamRefreshTimer = null;
webcamXHR = null;

$(document).bind('molly-page-change', function(event, url){
    
    if (url.match(/^\/webcams\/[a-zA-Z0-9\-]+\/$/)) {
        
        // Refresh every 60 seconds
        webcamRefreshTimer = setTimeout(webcamRequestData, 60000);
        
    } else {
        clearTimeout(webcamRefreshTimer);
        if (webcamXHR != null) {
            webcamXHR.abort();
        }
    }
});

function webcamRequestData(){
        webcamXHR = $.ajax({
            url: current_url,
            data: { format: 'json' },
            dataType: 'json',
            success: webcamRefresh
        })
}

function webcamRefresh(data){
    
    webcamXHR = null;
    
    // Update image (which is a background to a div in smartphones)
    $('.webcam-image').css('background-image', "url('" + data.eis._url + "')")
    
    // Also upadte last updated timestamp
    var now = new Date();
    $('.webcam-last-updated').html(pad2(now.getHours()) + ':' + pad2(now.getMinutes()));
    function pad2(number) {
        return (number < 10 ? '0' : '') + number
    }
    webcamRefreshTimer = setTimeout(webcamRequestData, 60000);
}
