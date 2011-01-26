/*
 *	code fragments from http://rossboucher.com/2008/08/19/iphone-touch-events-in-javascript/
 */

touchHandler = function(event)
{
//	event.preventDefault()
    var self = touchMap.viewerBean;
    var touches = event.changedTouches,
        first = touches[0],
        type = '';
    if(touches.length==1){

		switch(event.type)
		{
			case 'touchstart': type = 'mousedown'; break;
			case 'touchmove':  type='mousemove'; break;        
			case 'touchend':   type='mouseup'; break;
			default: return;
		}
		
		
		if(event.type == 'touchend' && lastTouchEventBeforeLast.type == 'touchend' &&
			event.x == lastTouchEventBeforeLast.x &&
			event.y == lastTouchEventBeforeLast.y){
			if(lastTouchEventBeforeLast.date){
				event.date = new Date();
				diff = event.date.getSeconds()*1000+event.date.getMilliseconds()-
				(lastTouchEventBeforeLast.date.getSeconds()*1000+lastTouchEventBeforeLast.date.getMilliseconds());
				if(diff<500){
					lastTouchEventBeforeLast.date = false;
					lastTouchEvent.date = false;
					type='dblclick';
				}
			}
		}

		var simulatedEvent = document.createEvent('MouseEvent');
		simulatedEvent.initMouseEvent(type, true, true, window, 1, 
								  first.screenX, first.screenY, 
								  first.clientX, first.clientY, false, 
								  false, false, false, 0/*left*/, null);
																				
		first.target.dispatchEvent(simulatedEvent);

		lastTouchEventBeforeLast = lastTouchEvent;
		lastTouchEvent = event;
		lastTouchEvent.date = new Date();
    }
    if(event.type == 'touchend') { 
        if(typeof(lastKnownScale) != "undefined" && lastKnownScale!=false){    
            document.getElementById('well').setAttribute('style','-webkit-transform: scale(1);');
            pinchStartScale = false;
//            var faktor=1; // lastKnownScale;
//            if( self.tileSize*lastKnownScale < PanoJS.TILE_SIZE*0.7) faktor=PanoJS.TILE_SIZE/self.tileSize;
//            if( self.tileSize*lastKnownScale > PanoJS.TILE_SIZE*1.7) faktor=PanoJS.TILE_SIZE/self.tileSize;

//        	self.blank();
//    		var coords = { 'x' : Math.floor(self.width / 2), 'y' : Math.floor(self.height / 2) };
//    		var before = {
//    			'x' : (coords.x - self.x),
//    			'y' : (coords.y - self.y)
//    		};
//    		var after = {
//    			'x' : Math.floor(before.x * faktor),
//    			'y' : Math.floor(before.y * faktor)
//    		};
//    		self.x = coords.x - after.x;
//    		self.y = coords.y - after.y;

            self.x = pinchStartCoords.x;
            self.y = pinchStartCoords.y;

            if( self.tileSize*lastKnownScale < PanoJS.TILE_SIZE*0.7) {
                self.tileSize=PanoJS.TILE_SIZE;
        		self.positionTiles();
                touchMap.viewerBean.zoom(-1);
            } else if( self.tileSize*lastKnownScale > PanoJS.TILE_SIZE*1.7) {
                self.tileSize=PanoJS.TILE_SIZE;
        		self.positionTiles();
                touchMap.viewerBean.zoom(1);
            } else {       		
                //self.tileSize=self.tileSize*faktor;
                self.tileSize=PanoJS.TILE_SIZE;
        		self.positionTiles();
        		//touchMap.viewerBean.notifyViewerZoomed();
    		}
            lastKnownScale=false;
            pinchStartCoords=false;
        }
	}
    if (event.preventDefault) event.preventDefault();
}

function gestureHandler(event){
    var touches = event.changedTouches;
    if (pinchStartScale==false) {
        pinchStartScale = touchMap.viewerBean.zoomLevel;
        pinchStartCoords={ 'x' : (touchMap.viewerBean.x), 'y' : (touchMap.viewerBean.y) };
    } 
    if(pinchStartScale && event.scale){
        document.getElementById('well').setAttribute('style','-webkit-transform: scale('+event.scale+');');
        lastKnownScale=event.scale;
    }
    if (event.preventDefault) event.preventDefault();
} 



var touchArea = document.getElementById('touchArea');
var lastTouchEvent = false;
var lastTouchEventBeforeLast = false;
var touchDate = false;
var pinchStartScale = false;
var pinchStartCoords = false;
var lastKnownScale = false;

if(touchArea){
	EventUtils.addEventListener(touchArea, 'touchstart', touchHandler, true);
	EventUtils.addEventListener(touchArea, 'touchmove', touchHandler, true);
	EventUtils.addEventListener(touchArea, 'touchend', touchHandler, true);
	EventUtils.addEventListener(touchArea, 'touchcancel', touchHandler, true);
    EventUtils.addEventListener(touchArea, 'gesturestart', gestureHandler, false);
    EventUtils.addEventListener(touchArea, 'gesturechange', gestureHandler, false);
    EventUtils.addEventListener(touchArea, 'gestureend', gestureHandler, false);
}
