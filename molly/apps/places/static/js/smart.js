function capfirst(s) {
    return s.substr(0,1).toUpperCase() + s.substr(1)
}

$(function(){
    
    function parse_results(data, nearby){
        $('.category-list').remove()
        for (category in data.entity_types) {
            $('#poi-category-selector').append(
                '<div class="header"><h2>' + category + '</h2></div>' +
                '<ul class="link-list"></ul>')
            for (j in data.entity_types[category]) {
                entity_type = data.entity_types[category][j]
                if (nearby) {
                    $('#poi-category-selector ul:last').append(
                        '<li><a href="nearby/' + entity_type.slug + '/">' + 
                        capfirst(entity_type.verbose_name_plural) +
                        ' <small>(' + entity_type.entities_found + ' within ' + Math.ceil(entity_type.max_distance/10)*10 + 'm)</small>' +
                        '</a></li>')
                } else {
                    $('#poi-category-selector ul:last').append(
                        '<li><a href="category/' + entity_type.slug + '/">' + 
                        capfirst(entity_type.verbose_name_plural) +
                        '</a></li>')
                }
            }
        }
        $('#poi-category-selector ul').addClass('no-round-bottom')
        $('#poi-category-selector ul:last').removeClass('no-round-bottom')
    }
    
    $('.nearby a').click(function(){
        $.ajax({
            url: $(this).attr('href'),
            data: { format: 'json' },
            dataType: 'json',
            success: function(data){parse_results(data, true)}
        })
        return false;
    })
    
    $('.categories a').click(function(){
        $.ajax({
            url: $(this).attr('href'),
            data: { format: 'json' },
            dataType: 'json',
            success: function(data){parse_results(data, false)}
        })
        return false;
    })
    
})