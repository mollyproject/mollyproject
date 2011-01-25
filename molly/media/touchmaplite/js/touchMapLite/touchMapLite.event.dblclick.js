PanoJS.doubleClickHandler = function(e) {
	e = e ? e : window.event;
	var self = this.backingBean;
	coords = self.resolveCoordinates(e);
	if (!self.pointExceedsBoundaries(coords)) {
		self.resetSlideMotion();
		self.recenter(coords);
		self.zoom(1);
	}
};
