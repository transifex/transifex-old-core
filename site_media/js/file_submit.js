$(document).ready(function() {
  $('span.submit_button').click(function() {
    if ( $(this).next("form.submit_form").is(':hidden') ) { 
      $("form.submit_form").hide("slide");
    }
    // Temporary "if" for warning users about locked files
    if ( $(this).prev().attr("nodeName") == "SPAN" && $(this).prev().text() != "(you)" ) {
        lastChild = $(this).next("form.submit_form").children().attr('lastChild');
        if (lastChild["nodeName"] != "P")
            $(this).next("form.submit_form").children().append("<p style=\"margin: 0px; color: red;\">This file is locked by someone else. Are you sure that you want to do it?</p>");
    }

    $(this).next("form.submit_form").toggle("medium");
   })
});
