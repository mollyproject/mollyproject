touchMapLite.prototype.getPermaFormUrlParams = function() {
	if(window.location.href.split('?' )[1]){
		var params = window.location.href.split('?')[1].split('&');
		for(index=0; index<params.length; index++) {  
			var keyValue = params[index].split('=');
			if(keyValue[0]=='lon') this.lon=parseFloat(keyValue[1]);
			if(keyValue[0]=='lat') this.lat=parseFloat(keyValue[1]);
			if(keyValue[0]=='zoom') this.zoom=parseInt(keyValue[1]);
			if(keyValue[0]=='map') this.map=keyValue[1];
		}
	}
	if(typeof(this.tileSources[this.map]) == 'undefined') this.map = this.defaultMap;
}

touchMapLite.prototype.permaLinkHandler = function() {
	self = this.viewerBean;
	current = this.currentLonLat(self);
	window.location.href = window.location.href.split('?' )[0]+'?lat='+current.y+'&lon='+current.x+'&zoom='+self.zoomLevel+'&map='+this.map;
	return false;
};