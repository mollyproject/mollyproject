$(document).bind('molly-page-change', function(event, url){
    if (url.match(/^\/tours\/[a-z_\-0-9]+\/create\/(([a-z_\-]+:[^\/]+\/)*)?$/)) {
        
        // Clicking on one in list adds to current stops list
        $('.attractions-grouping li a').click(function(e){
            tours_add_entity(get_tour_entity(this), $(this).html());
            e.preventDefault();
        });
        $('.attractions-grouping li a').addClass('has-ajax-handler');
        $('#tour-submit').addClass('has-ajax-handler');
        tours_reset_selected_bindings();
        
        $('#tour-submit').submit(function(e){
            $(this).attr('action', '/tours/' + type_slug + '/create/' + current_stops.join('/') + '/save/');
            async_form_load();
            return false;
        });
        
    }
});

function get_tour_entity(elem){
    var classes = $(elem).attr('class').split(/\s+/);
    for (var i in classes){
        if (classes[i].substr(0, 4) == 'tour'){
            var entity = classes[i].substr(5);
        }
    }
    return entity;
}

function tours_reset_selected_bindings(){
    $('#tour-poi-list li a').unbind('click');
    $('#tour-poi-list li a').click(function(){
        var entity = get_tour_entity(this);
        $(this).parent().remove();
        $('.attractions-grouping .tour-' + entity).parent().removeClass('selected');
        entity = entity.replace('-', ':');
        new_current_stops = [];
        for (var i in current_stops) {
            if (current_stops[i] != entity) {
                new_current_stops.push(current_stops[i]);
            }
        }
        current_stops = new_current_stops;
        e.preventDefault();
    })
    $('#tour-poi-list li a').addClass('has-ajax-handler');
    capture_outbound();
}

function tours_add_entity(entity, name){
    for (var i in current_stops) {
        // Don't add stops that already exist
        if (current_stops[i] == entity) {
            return;
        }
    }
    $('#tour-poi-list').append('<li><a href="#" class="tour-' + entity + '">' + name + '</a></li>');
    $('.attractions-grouping .tour-' + entity).parent().addClass('selected');
    tours_reset_selected_bindings();
    entity = entity.replace('-', ':');
    current_stops.push(entity);
}
