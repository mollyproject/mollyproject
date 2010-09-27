var current_slide = 0;

function preview() {
  var popup = window.open(
    '?preview=true',
    'popwin',
    'left=20,top=20,innerwidth=400,innerheight=480,toolbar=1,menubar=0,location=0,status=1,resizable=1,scrollbars=yes'
  );
  popup.window.location.href = "/" + "?preview=true";
}
  
$(function() {
  $('.preview-link').bind('click', function(event) {
    preview();
    return false;
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