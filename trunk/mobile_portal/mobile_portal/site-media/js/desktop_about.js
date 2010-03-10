var pages = ["about", "features", "blog"];
var page = window.location.hash.substring(1).split('-')[0];
var current_slide = 0;

if (page != "{{ page }}") {
  url = "/desktop/";
  for (i in pages) {
    page = pages[i];
    if (window.location.hash.substring(1, page.length+1) != page)
      continue;
    if (page != "about")
      url += page + "/";
    window.location = url + window.location.hash;
  }
}

function preview() {
  var popup = window.open(
    '?preview=true',
    'popwin',
    'left=20,top=20,innerwidth=330,innerheight=480,toolbar=1,menubar=0,location=0,status=1,resizable=1,scrollbars=yes'
  );
  popup.window.location.href = "/" + "?preview=true";
}
  
$(function() {
  $('.preview-link').bind('click', function(event) {
    preview();
    return false;
  });
      
  $('.navigation a').each(function() {
    e = $(this);
    e.bind('click', function() {
      $('#container').html('');
      $('#spinner').show();
      url = $(this).attr('href');
      e = $(this);
      $.ajax({
        url: url,
        data: 'ajax=true',
        success: function(data) {
          $('#spinner').hide();
          $('#container').html(data);
          current_slide = 0;
          initSlides();
          window.location.hash = '#'+e.attr('id').substring(5);
        },
      });
      $('.navigation li').removeClass('selected');
      e.parent().addClass('selected');
      e.blur();
      return false;
    });
  });
        
  initSlides();
  
  setTimeout('nextSlide();', 8000); 
});

function initSlides() {
  slideshow_count = $('.slideshow li').length;
  $('.slideshow ul').css('position', 'relative');
  
  
  $('.slideshow li').each(function(i, e) {
    e = $(e);
    e.css('position', 'absolute').css('top', '0px');
    
    if (i != current_slide) {
      e.hide();
    }
  });
  
  $('.lightbox').lightBox({fixedNavigation:false});
}


function nextSlide() {
  next_slide = (current_slide + 1) % slideshow_count;
  
  current = $('.slideshow li').slice(current_slide, current_slide+1);
  next = $('.slideshow li').slice(next_slide, next_slide+1);
  
  current.fadeOut(2000);
  next.fadeIn(2000);
  
  current_slide = next_slide;
  
  setTimeout('nextSlide();', 10000);
}