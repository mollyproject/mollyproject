touchMapLite.prototype.TileUrlProviderGMap = function(baseUri, prefix) {
	this.baseUri = baseUri;
	this.prefix = prefix;
}

touchMapLite.prototype.TileUrlProviderGMap.prototype = {
	assembleUrl: function(xIndex, yIndex, zoom) {
		return this.baseUri + '/' +
			this.prefix + 'x=' + xIndex + '&y=' + (yIndex) + '&z=' + zoom;
	}
}