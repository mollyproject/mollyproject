function ViewRenderer() {
    
    this.views = {};
    
    this.add_handler = function(view_name, view) {
        this.views[view_name] = view;
    }
    
    this.dispatch_request = function(url) {
        return $.ajax({
            'url': url,
            'dataType': 'json',
            'success': $.proxy(this.dispatch_response, this)
        });
    }
    
    this.dispatch_response = function(response) {
        var handler = this.views[response.view_name];
        if (handler !== undefined) {
            handler.handle_success(response);
        }
    }
    
    this.enter = function() {
        $('#body').empty();
        var spinner = new Spinner({
          lines: 11, // The number of lines to draw
          length: 27, // The length of each line
          width: 14, // The line thickness
          radius: 40, // The radius of the inner circle
          rotate: 0, // The rotation offset
          color: '#000', // #rgb or #rrggbb
          speed: 1.2, // Rounds per second
          trail: 100, // Afterglow percentage
          shadow: false, // Whether to render a shadow
          hwaccel: false, // Whether to use hardware acceleration
          className: 'spinner', // The CSS class to assign to the spinner
          zIndex: 2e9, // The z-index (defaults to 2000000000)
          top: 'auto', // Top position relative to parent in px
          left: 'auto' // Left position relative to parent in px
        }).spin(document.getElementById('body'));
        this.dispatch_request(window.location);
    }
}

view_renderer = new ViewRenderer();
$(function(){
    view_renderer.enter();
})
