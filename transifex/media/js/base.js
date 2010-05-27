
// General Tooltip function
function tooltip(targetnode, message){

    $(targetnode).qtip({
      content: message,
      position: {
         corner: {
            target: 'topRight',
            tooltip: 'bottomLeft'
         }
      },
      style: {
         name: 'cream',
         color: '#685D40',
         padding: '7px 13px',
         width: {
            max: 350,
            min: 0
         },
         border: {
            width: 3,
            radius: 3
         },
         tip: true
      }
    })
}


$(document).ready(function(){
    
      // Enable autosubmit form after a change on the language drop box switcher
      $("#language_switch").change(function() { this.form.submit(); });

});