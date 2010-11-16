var map = null;
var markers = null;

function setMap(e) {
  loc = entities[e.data].location;
  map.setCenter(new OpenLayers.LonLat(loc[0], loc[1]).transform(map.displayProjection, map.projection), 16);
  highlightRow(e.data);
  return false;
}

var currentRow = null;
var currentId = null;
function highlightRow(id) {
  if (currentRow)
    currentRow.removeClass('highlighted');
  $('#row-'+id).addClass('highlighted');

  currentRow = $('#row-'+id);
  currentId = id;

  $('#tags-div').css('visibility','visible');

  tags_tbody = $('#tags tbody');
  tags_tbody.empty();

  tags = [];
  for (var tag in entities[id].new_tags)
    tags.push(tag);
  tags.sort();

  for each (var tag in tags) {
    addTag(tags_tbody, tag, entities[id].new_tags[tag]);
  }
}

function updateTag(id, key, value) {
  if (value == '') {
    value = undefined;
    delete entities[id].new_tags[key];
  } else
    entities[id].new_tags[key] = value;

  cell = $('#cell-'+id+'-'+key);

  cell.text(value || '');
  if (entities[id].tags[key] == entities[id].new_tags[key]) {
    cell.removeClass('modified');
    cell.attr('title', '');
  } else {
    cell.addClass('modified');
    cell.attr('title', "Originally '" + entities[id].tags[key] + "'");
  }
}

function addTag(tags_tbody, key, value) {
  row = $('<tr><td><input class="key"/></td><td><input class="value"/></td><td><button class="remove">Remove</button></td></tr>');
  tags_tbody.append(row);
  row.find('.key').val(key);
  row.find('.value').val(value);
  row.find('.remove').bind('click', row, function(e) {
    e.data.remove();
  });
}

$(function () {
  map = create_map('map', 51.7522, -1.2582, null);

  var size = new OpenLayers.Size(21,25);
  var offset = new OpenLayers.Pixel(-(size.w/2), -size.h);
  var icon = new OpenLayers.Icon('/site-media/openlayers/img/marker-blue.png',size,offset);

  $('.tag-key').each(function() {
    star = $('<a href="#">*</a>').bind('click', $(this).text(), function(e) {
      green_icon = '/site-media/openlayers/img/marker-green.png';
      red_icon = '/site-media/openlayers/img/marker.png';
      for (var id in entities)
        $(entities[id].marker.icon.imageDiv).find('img').attr('src', (entities[id].new_tags[e.data] ? green_icon : red_icon));
      return false;
    });
    $(this).append(star);
  });

  $('#entities > tbody > tr').each(function() {
    e = $(this).children(":first");
    var id = e.html();
    e.html('<a href="#">'+id+'</'+'a>').bind('click', id, setMap);
    loc = entities[id].location;
    marker = new OpenLayers.Marker(new OpenLayers.LonLat(loc[0], loc[1]).transform(map.displayProjection, map.projection), icon.clone());
    marker.events.register('click', marker, function(e) {
      mp = $('#main-pane');
      mp.scrollTop(mp.scrollTop() - mp.height()/2 + $('#row-'+id).offset().top);
      highlightRow(id);
    });
    markers.addMarker(marker);

    entities[id].new_tags = {};
    entities[id].marker = marker;
    for (var tag in entities[id].tags) {
      entities[id].new_tags[tag] = entities[id].tags[tag];
    }

  });

  $('#entities > tbody td').bind('click', function() {
    cell = $(this);
    if (cell.find('input').length > 0)
      return;

    value = cell.text();
    cell.html('<input/>');
    cell.find('input').val(value).width(cell.width()-10).focus().bind('blur', function() {
      input = $(this);
      cell = input.parent();
      cell.text(input.val());
      id_ptype = cell.attr('id').split('-', 3);
      updateTag(id_ptype[1], id_ptype[2], cell.text());
    });
  });

  $('#send_update').bind('click', function() {
    comment = $('#comment').val();
    if (!comment) {
      $('#status').html('You must provide a changeset comment');
      return;
    }

    var changes = {};
    for (var id in entities) {
      has_changed = false;
      for (var tag in entities[id].new_tags)
        if (entities[id].tags[tag] != entities[id].new_tags[tag])
          has_changed = true;
      for (var tag in entities[id].tags)
        if (entities[id].tags[tag] != entities[id].new_tags[tag])
          has_changed = true;

      if (!has_changed)
        continue;

      changes[id] = {
        version: entities[id].version,
        location: entities[id].location,
        tags: entities[id].new_tags,
      };
    }

    $.post('.', $.toJSON({
      comment: comment,
      username: $('#username').val(),
      password: $('#password').val(),
      changes: changes,
    }), function(data, status) {
      $('#status').html(data.status);
      for (var id in data.changes) {
        entites[id] = data.changes[id];
        for (var tag in data.changes[id].tags) {
          cell = $('#cell-'+id+'-'+tag);
          if (cell.length == 0)
            continue;
          cell.removeClass('modified');
          cell.text(data.changes[id].tags[tag]);
        }
      }
    }, 'json');
  });

  $('#save-tags').bind('click', function() {
    tags = entities[currentId].new_tags = {}
    $('#tags tbody tr').each(function () {
      row = $(this);
      key = row.find('.key').val();
      value = row.find('.value').val();

      updateTag(currentId, key, value);
    });
  });

  $('#new-tag').bind('click', function() {
    tags_tbody = $('#tags tbody');
    addTag(tags_tbody, '', '');
  });
});
