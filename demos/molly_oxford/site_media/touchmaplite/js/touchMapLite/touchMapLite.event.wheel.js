/*	
 *	code found at http://adomas.org/javascript-mouse-wheel/
 */


function wheelHandler(event){
	var delta = 0;

	if (!event) event = window.event;
	if (event.wheelDelta) {
		delta = event.wheelDelta/120;
		if (window.opera) delta = -delta;
	} else if (event.detail) {
		delta = -event.detail/3;
	}
 
	if (delta)
	var self = touchMap.viewerBean;
	if(delta>0){
		self.zoom(1);
	} else {
		self.zoom(-1);                	
	};
	coords = self.resolveCoordinates(event);
	if (!self.pointExceedsBoundaries(coords)) {
		self.resetSlideMotion();
		self.recenter(coords);
	}
	if (event.preventDefault) event.preventDefault();
	event.returnValue = false;
}

		
EventUtils.addEventListener(window, 'DOMMouseScroll', wheelHandler, false);
EventUtils.addEventListener(window, 'mousewheel', wheelHandler, false);
