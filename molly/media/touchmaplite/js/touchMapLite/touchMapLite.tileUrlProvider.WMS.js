touchMapLite.prototype.TileUrlProviderWMS = function(baseUri, layers, styles, format, lowercase) {
	this.myBaseURL = baseUri;
	this.myLayers = layers;
	this.myStyles = styles;
	this.myFormat = format;
	this.lowercase = lowercase;
}

touchMapLite.prototype.TileUrlProviderWMS.prototype = {

	tile2long:function(x,z) {
  		return (x/Math.pow(2,z)*360-180);
	 },

	tile2lat: function(y,z) {
		var n=Math.PI-2*Math.PI*y/Math.pow(2,z);
		return (180/Math.PI*Math.atan(0.5*(Math.exp(n)-Math.exp(-n))));
 	},

	assembleUrl:function(xIndex, yIndex, zoom) {

		var lSRS="EPSG:4326";
	
		var lLongLeft = this.tile2long(xIndex,zoom);
		var lLongRight = this.tile2long(xIndex+1,zoom);
		var lLatTop = this.tile2lat(yIndex,zoom);
		var lLatBottom =this.tile2lat(yIndex+1,zoom);
	
		var lBbox=lLongLeft+","+lLatBottom+","+lLongRight+","+lLatTop;

	
		var lURL=this.myBaseURL;
		if(!this.lowercase){
			lURL+="&REQUEST=GetMap";
			lURL+="&SERVICE=WMS";
			lURL+="&VERSION=1.1.1";
			lURL+="&LAYERS="+this.myLayers;
			lURL+="&STYLES="+this.myStyles;
			lURL+="&FORMAT="+this.myFormat;
			lURL+="&BGCOLOR=0xFFFFFF";
			lURL+="&TRANSPARENT=FALSE";
			lURL+="&SRS="+lSRS;
			lURL+="&BBOX="+lBbox;
			lURL+="&WIDTH=256";
			lURL+="&HEIGHT=256";
			lURL+="&REASPECT=false";
		} else {
			lURL+="request=GetMap";
			lURL+="&service=WMS";
			lURL+="&version=1.1.1";
			lURL+="&srs="+lSRS;
			lURL+="&format="+this.myFormat;
			lURL+="&styles="+this.myStyles;
			lURL+="&bgcolor=0xFFFFFF";
			lURL+="&transparent=FALSE";
			lURL+="&bbox="+lBbox;
			lURL+="&width=512";
			lURL+="&height=512";
			lURL+="&layers="+this.myLayers;
			lURL+="&reaspect=false";
		}
		return lURL;
		}
}
