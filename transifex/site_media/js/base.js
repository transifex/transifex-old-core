$(document).ready(function(){
    
      // Enable autosubmit form after a change on the language drop box switcher
      $("#language_switch").change(function() { this.form.submit(); });

});