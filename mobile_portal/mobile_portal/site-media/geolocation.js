function sendPosition(position) {
    alert(jQuery);
    jQuery.post('/ajax/position_update/', {
        longitude: position.coords.longitude,
    })
    alert(position);
)

navigator.geolocation.getCurrentPosition(sendPosition);

