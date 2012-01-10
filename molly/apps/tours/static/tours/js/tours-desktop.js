$(function(){

    function reset_selected_bindings(){
        $('#poi-list li a').unbind('click');
        $('#poi-list li a').click(function(e){
            var entity = $(this).attr('class');
            $(this).parent().remove();
            $('.attractions-grouping .' + entity).parent().removeClass('selected');
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
    }
    reset_selected_bindings();

    function add_entity(entity, name){
        for (var i in current_stops) {
            // Don't add stops that already exist
            if (current_stops[i] == entity) {
                return;
            }
        }
        $('#poi-list').append('<li><a href="#" class="' + entity + '">' + name + '</a></li>');
        $('.attractions-grouping .' + entity).parent().addClass('selected');
        reset_selected_bindings();
        entity = entity.replace('-', ':');
        current_stops.push(entity);
    }

    $('.attractions-grouping li a').click(function(e){
        add_entity($(this).attr('class'), $(this).html());
        e.preventDefault();
    });

    $('#poi-submit').submit(function(e){
        $(this).attr('action', '/tours/' + type_slug + '/create/' + current_stops.join('/') + '/save/');
        e.preventDefault();
        $(this).submit();
    });
    
    $('#poi-search').autocomplete({
        minLength: 0,
        source: all_pois,
        focus: function(event, ui) {
            return false;
        },
        select: function(event, ui) {
            add_entity(ui.item.id, ui.item.label)
            return false;
        }
    }).data( "autocomplete" )._renderItem = function( ul, item ) {
        return $( "<li></li>" )
            .data( "item.autocomplete", item )
            .append( "<a>" + item.label + "</a>" )
            .appendTo( ul );
    };
    $('#poi-search').click(function(){
        $('#poi-search').autocomplete("search");
    });

})
