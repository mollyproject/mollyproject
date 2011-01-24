touchMapLite.prototype.SQLite.ini = function(db, map) {
	if(db) this.db = db;
	this.values = new Object;
	this.map = map;
	this.init();
}

touchMapLite.prototype.SQLite.ini.prototype = {
	init: function() {
		if (this.db){
			var ini = this;
			this.db.transaction(function(tx) {
				tx.executeSql("SELECT * FROM ini", [], function(tx, result) {
					for (var i = 0; i < result.rows.length; ++i) {
						var row = result.rows.item(i);
						ini.set(row.key,row.value);
					 }
					 ini.apply();
				}, function(tx, error) {
					tx.executeSql("CREATE TABLE ini (key TEXT, value TEXT)", [], function(result) { 
				// count; 
				});
				});
			});
		 }
	},
	set: function(key, value)
	{
		this.values[key]=value;
	},
	apply: function()
	{
		if(this.values['lon']) this.map.lon = parseFloat(this.values['lon']);
		if(this.values['lat']) this.map.lat = parseFloat(this.values['lat']);
		if(this.values['zoom']) this.map.viewerBean.zoomLevel = parseInt(this.values['zoom']);
		if(this.values['map']) this.map.switchSource(this.values['map']);
		if(this.map.lon == 0 && this.map.lat == 0){
			this.map.zoom = 1;
		}
		this.map.viewerBean.initialPan = { 'x' : this.map.lon2pan(this.map.lon), 'y' : this.map.lat2pan(this.map.lat)};
		this.map.viewerBean.clear();
		this.map.viewerBean.init();
		this.map.viewerBean.notifyViewerMoved({x:this.map.viewerBean.x, y:this.map.viewerBean.y})

	},
    update: function(key, value)
    {
		var ini = new Object;
		ini.key = key;
		ini.value = value;

        this.db.transaction(function (tx) 
        {
			tx.executeSql("SELECT * FROM ini WHERE key = ?", [ini.key], function(tx,result) {
				if(result.rows.length){
		           tx.executeSql("UPDATE ini SET value = ? WHERE key = ?", [ini.value, ini.key]);
				} else {
		           tx.executeSql("INSERT INTO ini (key, value) VALUES (?, ?)", [ini.key, ini.value]);
				}

			});
        });  
      }
}


