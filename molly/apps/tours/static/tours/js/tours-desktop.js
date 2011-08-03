$(function(){

    function reset_selected_bindings(){
        $('#poi-list li a').unbind('click');
        $('#poi-list li a').click(function(e){
            var entity = $(this).attr('class');
            $(this).parent().remove();
            $('.attractions-grouping .' + entity).parent().removeClass('selected');
            entity = entity.replace('-', ':');
            new_current_stops = [];
            for (i in current_stops) {
                if (current_stops[i] != entity) {
                    new_current_stops.push(current_stops[i]);
                }
            }
            current_stops = new_current_stops;
            e.preventDefault();
        })
    }
    reset_selected_bindings();

    $('.attractions-grouping li a').click(function(e){
        var entity = $(this).attr('class');
        $('#poi-list').append('<li><a href="#" class="' + entity + '">' + $(this).html() + '</a></li>');
        $('.attractions-grouping .' + entity).parent().addClass('selected');
        reset_selected_bindings();
        entity = entity.replace('-', ':');
        current_stops.push(entity);
        e.preventDefault();
    })

    $('#poi-submit').submit(function(){
        $(this).attr('action', '/tours/create/' + current_stops.join('/') + '/save/');
        e.preventDefault();
        $(this).submit();
    })

})
