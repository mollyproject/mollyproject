touchMapLite.tileSources = {};

touchMapLite.prototype.SQLite.tiles = function(db,map,id, url,regex, mimetype) {
	this.db = db;
	this.map = map;
	this.url = url;
	this.regex = regex;
	this.id = id;
	if(mimetype){this.mimetype = mimetype;} else {this.mimetype = 'image/png';}
	this.init();
	
}


touchMapLite.prototype.SQLite.tiles.prototype = {
	assembleUrl: function(xIndex, yIndex, zoom) {
			url = this.url.replace(/\{Z\}/g, zoom);
			url = url.replace(/\{X\}/g, xIndex);
			url = url.replace(/\{Y\}/g, yIndex);
			return url;
	},


	init: function() {
		if(this.db){
			this.db.transaction(function(tx) {

				tx.executeSql("SELECT COUNT(*) FROM tiles", [], function(tx, result) {
				// count;
				}, function(tx, error) {
				tx.executeSql("CREATE TABLE tiles (provider TEXT, x INT, y INT, z INT, timestamp REAL, data BLOB)", [], function(result) { 
				// count; 
				});
				});
			 });
			this.map.viewerBean.createPrototype = this.createPrototype;
		}

	},

    writeTileToCache: function(tileObject)
    {

		tileObject.timestamp = 0;
        this.db.transaction(function (tx) 
        {
            tx.executeSql("INSERT INTO tiles (provider, x, y, z, timestamp, data) VALUES (?, ?, ?, ?, ?, ?)", [tileObject.provider, tileObject.x, tileObject.y, tileObject.z, tileObject.timestamp, tileObject.data], function(result) { 
            		tileObject = false;
				});
        }); 
        
    },
    populateCache: function(tileObject)
    {
		
// proxy method

/*		getreq('http://proxy/base64/?'+tileObject.src, function(request){
			if (request.readyState != 4){ return; }
			tileObject.data = request.responseText
			tileObject.tiles.writeTileToCache(tileObject);
		});
*/
		// using canvas toDataURL method to generate base64 string
		tileObject.image.src=tileObject.src;
		tileObject.image.onload = function(){
			tileObject.data = tileObject.tiles.getBase64Image(tileObject.image, tileObject.tiles.mimetype);
			tileObject.tiles.writeTileToCache(tileObject);
		}
    },
    // from http://stackoverflow.com/questions/934012/get-image-data-in-javascript
    getBase64Image: function (img,mimetype) {
		canvas = document.createElement("canvas");
		canvas.width = img.width;
		canvas.height = img.height;
		ctx = canvas.getContext("2d");
		ctx.drawImage(img, 0, 0);
		return canvas.toDataURL(mimetype,'quality=20');
		
	},
    
    fetchTileFromCache: function(image,z,x,y,src)
    {

		var tileObject = new Object;
		
		tileObject.image = image;
		tileObject.provider = this.id;
		tileObject.x = x;
		tileObject.y = y;
		tileObject.z = z;
		tileObject.src = src;
		tileObject.tiles = this;

		if(this.db){ //  && document.getElementById('cache') && document.getElementById('cache').checked
	       this.db.transaction(function (tx) 
    	    {
				tx.executeSql("SELECT data FROM tiles WHERE provider = ? AND x = ? AND y = ? AND z = ?", [tileObject.provider, tileObject.x, tileObject.y, tileObject.z], function(tx, result) {
					if(!result.rows.length){
//		    	    	tileObject.image.style.border = 'dotted 1px red';
						tileObject.tiles.populateCache(tileObject);
					} else {
//						tileObject.image.style.border = 'dotted 1px blue';
						tileObject.image.src = result.rows.item(0).data;
					}
				}, function(tx, error) {
//	    	    	tileObject.image.style.border = 'dotted 1px red';
					tileObject.tiles.populateCache(tileObject);
				});

        	}); 
        } else {
	        image.src = src; 
        }
    },
    
	resolveTile: function(image, src) {
  		if(this.regex.test(src)){
			this.regex.exec(src);
	  		this.fetchTileFromCache(image,RegExp.$1,RegExp.$2,RegExp.$3,src);
	  	} else {
	  		image.src = src;
	  	}
	},
	createPrototype: function(src) {
		var img = document.createElement('img');
		if(this.touchMap.viewerBean.tileUrlProvider.resolveTile) {
			this.touchMap.viewerBean.tileUrlProvider.resolveTile(img, src);
		} else {
			touchMap.sqlTiles.resolveTile(img, src);
		}
		img.className = 'tile'; // touchMap.viewerBean.TILE_STYLE_CLASS;
		img.style.width = '256px'; //touchMap.viewerBean.tileSize + 'px';
		img.style.height = '256px'; // touchMap.viewerBean.tileSize + 'px';
		return img;
	}

}

/*
 function createXMLHttpRequest() {
   try { return new XMLHttpRequest(); } catch(e) {}
   try { return new ActiveXObject("Msxml2.XMLHTTP"); } catch (e) {}
   try { return new ActiveXObject("Microsoft.XMLHTTP"); } catch (e) {}
   alert("XMLHttpRequest not supported");
   return null;
 }

function getreq ( url, callback )
{
	var req = createXMLHttpRequest();
	if ( !req ) {
		alert( "Error initializing XMLHttpRequest!" );
		return;
	}
	req.open( "GET", url, true );
	req.onreadystatechange = function () { callback( req ) };
	req.send( null );
}
*/