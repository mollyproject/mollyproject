touchMapLite.prototype.SQLite = function(dbname, version, comment, size){
	this.db = false;
	this.dbname = dbname;
	this.version = version;
	this.comment = comment;
	this.size = size;
	this.init();
}


touchMapLite.prototype.SQLite.prototype = {
	init: function(){
		if (window.openDatabase) {
			this.db = window.openDatabase(this.dbname, this.version, this.comment, this.size);
			if (this.db){		 
				this.db.transaction(function(tx) {
//					tx.executeSql("DROP TABLE tiles",[]);
//					tx.executeSql("DROP TABLE locations",[]);
//					tx.executeSql("DROP TABLE ini",[]);
				});
			}
			if (!this.db){
				alert("Failed to open the database.");
			}
		}
	}
}
