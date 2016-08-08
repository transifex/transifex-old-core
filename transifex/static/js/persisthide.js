(function($){
  $.fn.extend({ 
    persisthide: function() {
      return this.each(function() {

        phobj = $(this);
        phid = $(this).attr("id")+"-ph";

        if (amplify.store(phid) == 'expanded') {
          phobj.addClass("expanded").children(".ph-content").show();
        }

        phobj.children(".ph-trigger").click(function(){
          if(phobj.hasClass("expanded")){
        		   phobj.removeClass("expanded")
        		        .children(".ph-content").hide();
            amplify.store(phid, 'contracted');
          }
          else{
               phobj.addClass("expanded")
                    .children(".ph-content").show();
            amplify.store(phid, 'expanded');
          }
        });
      });
    }
  });
})(jQuery);