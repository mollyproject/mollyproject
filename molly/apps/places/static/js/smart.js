function capfirst(s) {
    return s.substr(0,1).toUpperCase() + s.substr(1)
}

$(function(){
    
    function parse_results(data, nearby){
        $('.category-list').remove()
        for (i in data.entity_types) {
            if (i < data.entity_types.length - 1) {
                classes = 'link-list no-round-bottom'
            } else {
                classes = 'link-list'
            }
            $('#poi-category-selector').append(
                '<div class="header"><h2>' + data.entity_types[i][0] + '</h2></div>' +
                '<ul class="' + classes + '"></ul>')
            for (j in data.entity_types[i][1]) {
                entity_type = data.entity_types[i][1][j]
                if (nearby) {
                    $('#poi-category-selector ul:last').append(
                        '<li><a href="nearby/' + data.entity_types[i][1][j].slug + '/">' + 
                        capfirst(entity_type.verbose_name_plural) +
                        ' <small>(' + entity_type.entities_found + ' within ' + Math.ceil(entity_type.max_distance/10)*10 + 'm)</small>' +
                        '</a></li>')
                } else {
                    $('#poi-category-selector ul:last').append(
                        '<li><a href="category/' + data.entity_types[i][1][j].slug + '/">' + 
                        capfirst(entity_type.verbose_name_plural) +
                        '</a></li>')
                }
            }
        }
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
            success: function(data){parse_results(data, true)}
        })
        return false;
    })
    
})