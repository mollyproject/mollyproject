function refreshTransport(data){
    window.location.reload()
}

function ajaxTransportUpdate(){
    $.ajax({
        url: window.location.href,
        data: { format: 'json' },
        dataType: 'json',
        success: refreshTransport
    })
}