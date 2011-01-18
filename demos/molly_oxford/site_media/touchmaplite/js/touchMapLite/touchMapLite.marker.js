/*	markers used under the terms of the Creative Commons Attribution licence
 *	http://www.mapito.net/map-marker-icons.html
 */


touchMapLite.prototype.MARKERS = [];


touchMapLite.prototype.placeMarkerHandler = function(){
	coords = this.currentLonLat(this.viewerBean);
	marker = new this.marker('GPS',coords.y, coords.x,this,true);
}


touchMapLite.prototype.getMarkersFormUrlParams = function(){
		if(window.location.href.split('?' )[1]){
			var params = window.location.href.split('?')[1].split('&');
			for(index=0; index<params.length; index++) {  
				keyValue = params[index].split('=');
				if(keyValue[0]=='markers'){
					markers = keyValue[1].split('|');
					for(markersIndex=0; markersIndex < markers.length; markersIndex++) {  
						markerParams = markers[markersIndex].split(',');
							this.MARKERS[markersIndex] = new this.marker(markerParams[2], parseFloat(markerParams[0]), parseFloat(markerParams[1]),this);
					}
				}
			}
		}
}
		

touchMapLite.prototype.marker = function(title, lat, lon, map, live, radius) {
	if(live){
		this.id = 0;
		found = false;
		if(typeof map.MARKERS == 'undefined') map.MARKERS = [];
		for(var id=0; id<map.MARKERS.length; id++){
			if(map.MARKERS[id].title == title && map.MARKERS[id].element){
				document.getElementById('markers').removeChild(map.MARKERS[id].element);
				map.MARKERS[id] = this;
				this.id = id;
				found = true;
				continue;
			}
		}
		if(!found){
			this.id = map.MARKERS.length;
			map.MARKERS[this.id] = this;
		}
	} else {
		this.id = map.MARKERS.length;
		map.MARKERS[this.id] = this;
	}
	this.lon = lon;
	this.lat = lat;
	this.x = 0;
	this.y = 0;	
	this.radius = radius;
	this.initialized = false;
	this.map = map;
	this.viewer = map.viewerBean;
	var marker = this;	
	this.viewer.addViewerMovedListener(marker);
	this.viewer.addViewerZoomedListener(marker);
	this.title = title;
	this.isVisible = false;
	this.markerSrc = "images/markers/lightblue"+map.MARKERS.length+".png";
	if(title != "GPS"){
		this.createDOMelement();
	} else {
		this.createGPSelement(radius);	
	}
	this.placeMarker();
	this.updateMarker(this.viewer);

}

touchMapLite.prototype.marker.prototype = {
	
	placeMarker: function(){
		fullSize = this.viewer.tileSize * Math.pow(2, this.viewer.zoomLevel);
		this.x = Math.floor(this.map.lon2pan(this.lon)*fullSize);
		this.y = Math.floor(this.map.lat2pan(this.lat)*fullSize);

	},
	createGPSelement: function(accuracy){
	    radius = Math.floor((accuracy/metersPerPixel[this.viewer.zoomLevel])/2);
		this.element = document.createElement("div");
		this.element.setAttribute("class","marker");
		if(accuracy = document.getElementById("accuracy")){
			this.element.removeChild(accuracy);
		}
		var circle = document.createElement('CANVAS');
		circle.setAttribute("id","accuracy");
		circle.setAttribute("width",(radius+3)*2);
		circle.setAttribute("height",(radius+3)*2);
		circle.style.position = "absolute";
		circle.style.top = -(radius+3)+"px";
		circle.style.left = -(radius+3)+"px";
		var ctx = circle.getContext("2d");
		ctx.beginPath();
		ctx.fillStyle = 'rgba(4,90,252,0.1)';
		ctx.strokeStyle = 'rgba(4,90,252,0.8)';
		ctx.lineWidth = 1;
		ctx.arc((radius+1), (radius+1), radius, 0, Math.PI*2, true);
		ctx.closePath();
		ctx.fill();
		ctx.stroke();
		this.element.appendChild(circle);
		var image = document.createElement("img");
		image.src=this.markerSrc;
		this.element.appendChild(image)
		document.getElementById('markers').appendChild(this.element);
		this.element.marker = this;
		this.element.onclick = function(event){
			accuracy = document.getElementById("accuracy");
			if(accuracy){
				accuracy.style.display="none";
			};
		}
		setTimeout('document.getElementById("accuracy").style.display="none";',1500);
	},	
	createDOMelement: function(){
		this.element = document.createElement("div");
		this.element.setAttribute("class","marker");
		var image = document.createElement("img");
		image.src=this.markerSrc;
		document.getElementById('markers').appendChild(this.element)
		this.element.appendChild(image)
	
		this.element.marker = this;
		this.element.onclick = function(event){
			this.marker.hideBubbles();
			var bubble = document.createElement("div");
			this.appendChild(bubble);

			bubble.innerHTML = "#"+this.marker.id+": "+this.marker.title+"<br />"+this.marker.lat+",<br />"+this.marker.lon;
			bubble.setAttribute("class","bubble");
			bubble.onmouseup = function(e){
				this.parentNode.marker.hideBubbles();
				return false;
			}
			return false;
		}
	},
	updateMarker: function(e){	
	if(this.element){
		top = (e.y+this.y);
		left = (e.x+this.x);
		if(top>=0 && top<this.viewer.height && left>=0 && left<this.viewer.width){
			this.element.style.top = top+"px";
			this.element.style.left = left+"px";
			if(!this.isVisible){
				this.isVisible = true;
				this.element.style.display = 'block';
			}
		} else {
			if(this.isVisible){
				this.isVisible = false;
				this.element.style.display = 'none';
			}		
		}
	}
	},

	viewerMoved: function(e){
		this.updateMarker(e);

	},

	viewerZoomed: function(e){
		this.placeMarker();
		this.updateMarker(e);
		this.hideBubbles();
		if(this.title == "GPS"){
			accuracy = document.getElementById("accuracy");
			if(accuracy){
				accuracy.style.display="none";
			};
		}

	},

	
	hideBubbles: function(){
		for (var mm = document.getElementById('markers').firstChild; mm; mm = mm.nextSibling) {
			if (mm.className == 'marker'){
				for (var bb = mm.firstChild; bb; bb = bb.nextSibling) {
					if (bb.className == 'bubble'){
						mm.removeChild(bb);
					}
				}
			}
		}	
	}

}
