$(document).ready(function() {
  $('a.submit_button').click(function() {
    $(this).next("form.submit_form").toggle("medium");
  });
});
