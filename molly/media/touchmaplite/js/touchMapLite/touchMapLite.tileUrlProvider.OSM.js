touchMapLite.prototype.TileUrlProviderOSM = function(baseUri, prefix, extension) {
	this.baseUri = baseUri;
	this.prefix = prefix;
	this.extension = extension;
}

touchMapLite.prototype.TileUrlProviderOSM.prototype = {
	assembleUrl: function(xIndex, yIndex, zoom) {
		return this.baseUri + '/' +
			this.prefix + zoom + '/' + xIndex + '/' + yIndex + '.' + this.extension;
	}
}