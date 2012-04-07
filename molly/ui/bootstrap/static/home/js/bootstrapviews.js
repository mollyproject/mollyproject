function HomeIndexView() {
    this.handle_success = function(response) {
        $('#body').empty();
        var row;
        var visible_apps = response.applications.filter(function(app){
                return app.display_to_user;
            });
        for (var application_index in visible_apps) {
            if (application_index % 6 == 0) {
                row = $('<div/>').addClass('row-fluid');
                $('#body').append(row);
            }
            var app_box = $('<div/>').addClass('app').addClass('span2');
            var app_title = ($('<span/>').addClass('app-title'));
            app_title.text(visible_apps[application_index].title);
            app_box.addClass('app-' + visible_apps[application_index].local_name);
            app_box.append(app_title);
            $(row).append(app_box);
        }
    }
}

$(function(){
   view_renderer.add_handler("home:index", new HomeIndexView()); 
});
