touchMapLite.prototype.SQLite.markers = function(db, map) {
	this.db = db;
	this.map = map;
	this.init();
}

touchMapLite.prototype.SQLite.markers.prototype = {
	init: function() {
		if (this.db){
			var map = this.map;
			this.db.transaction(function(tx) {
				tx.executeSql("SELECT * FROM locations", [], function(tx, result) {
					for (var i = 0; i < result.rows.length; ++i) {
						var row = result.rows.item(i);
						marker = new map.marker(row.title,row.lat,row.lon,map,true);

					 }
				}, function(tx, error) {
				tx.executeSql("CREATE TABLE locations (id INT, lon FLOAT, lat FLOAT, timestamp REAL, title TEXT)", [], function(result) { 
				// count; 
				});
				});
			});
		 }



	},
    updateMarker: function(id,lat,lon,title)
    {
		var marker = new Object;
		var now = new Date();
		marker.id = id;
		marker.lat = lat;
		marker.lon = lon;
		marker.title = title;
		marker.timestamp = now.getTime();

        this.db.transaction(function (tx) 
        {
			tx.executeSql("SELECT * FROM locations WHERE id = ?", [marker.id], function(tx,result) {
				if(result.rows.length){
		           tx.executeSql("UPDATE locations SET lon = ?, lat = ?, timestamp = ?, title = ?  WHERE id = ?", [marker.lon, marker.lat, marker.timestamp, marker.title,marker.id]);
				} else {
		           tx.executeSql("INSERT INTO locations (id, lon, lat, timestamp, title) VALUES (?, ?, ?, ?, ?)", [marker.id, marker.lon, marker.lat, marker.timestamp, marker.title]);				
				}

			});
        });  
      }
}


