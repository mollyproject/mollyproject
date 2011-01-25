try {window.gears = !!(typeof GearsFactory != 'undefined' || navigator.mimeTypes['application/x-googlegears'] || new ActiveXObject('Gears.Factory'));}catch(e){}

if(typeof(navigator.geolocation) != "undefined"){

	touchMapLite.prototype.findLocationHandler = function(e) {
		if(findOnMap != null){
			  navigator.geolocation.getCurrentPosition(this.recenterLonLat, this.nolocationFound);
		}
		return false;
	};

} else if(typeof window.gears != "undefined"){
// android

	var geo = google.gears.factory.create('beta.geolocation');
	
	touchMapLite.prototype.findLocationHandler = function(e) {
		if(typeof(geo) != "undefined" && findOnMap != null){
			 geo.getCurrentPosition(this.recenterLonLat, this.nolocationFound);
		} else {
			alert('no geolocation service (gears)')
		}
		return false;
	}
} else if(typeof blackberry != "undefined" && typeof blackberry.location != "undefined"){
// blackberry
	touchMapLite.prototype.findLocationHandler = function(e) {
		if(blackberry.location.GPSSupported && findOnMap != null){
			 if(typeof blackberry.location.longitude  != "undefined"){
				 position = {coords:{longitude:blackberry.location.longitude, latitude:blackberry.location.latitude}};
				 this.prototype.recenterLonLat(position);
			 } else {
				 this.nolocationFound();
			 }
		} else {
			alert('no geolocation service (backberry)')
		}
		return false;
	}
} else {
// dummy

	touchMapLite.prototype.findLocationHandler = function(e) {
		alert('no geolocation services found')
		return false;
	};

}


touchMapLite.prototype.watchLocationHandler = function(e) {
	if(typeof(navigator.geolocation) != "undefined"){
		if(!watchId && findOnMap != null){
			watchId = navigator.geolocation.watchPosition(this.recenterLonLat);
			return true;
		} else {
			navigator.geolocation.clearWatch(watchId);
			watchId = false;
		}
	} else {
		alert('no geolocation service')
	}
	return false;
};

touchMapLite.prototype.nolocationFound = function(error){
	if(error.code!=0){
		alert('cannot determin current location ['+error.code+']');
	} else {
		return false;
	}
}

touchMapLite.prototype.recenterLonLat = function(position){
    var wasZoomed=false;

	lon = position.coords.longitude;
	lat = position.coords.latitude;

	findOnMap.lon = lon;
	findOnMap.lat = lat;
	
	if(!watchId && position.coords.accuracy){	
		for(zoomLevel=0; zoomLevel<17 && metersPerPixel[zoomLevel]*256>position.coords.accuracy; zoomLevel++){}
		if(zoomLevel!=findOnMap.viewerBean.zoomLevel) wasZoomed=true;
//		if(zoomLevel>findOnMap.viewerBean.zoomLevel) {
            findOnMap.viewerBean.zoomLevel = zoomLevel; 
//        }
	}
	if(wasZoomed==true) findOnMap.viewerBean.notifyViewerZoomed();
	if(typeof findOnMap.marker != 'undefined'){
		var home = new findOnMap.marker('GPS',lat, lon,findOnMap,true, position.coords.accuracy);
	}
	fullSize = findOnMap.viewerBean.tileSize * Math.pow(2, findOnMap.viewerBean.zoomLevel);
	x = Math.floor(findOnMap.lon2pan(lon)*fullSize);
	y = Math.floor(findOnMap.lat2pan(lat)*fullSize);
	findOnMap.viewerBean.recenter({'x':x, 'y':y}, true);
	return false;
}

var findOnMap = null;
var watchId = false;
var metersPerPixel = [156412,78206,39103,19551,9776,4888,2444,1222 ,611,305,153,76,38,19,10,5,2,1,0.6];
