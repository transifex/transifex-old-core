
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

/** 
  * This function escapes the html elements found in a html string!
  */
function html_escape(html)
{
  var escaped = html;
  escaped = escaped.replace(/&/g, "&amp;").replace(/</g, "&lt;")
        .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  return(escaped);
}

/**
  *@desc browse an array and escape all of his field
  *@return array escaped array
  */
function  array_escape(tab)
{
  var key;
  for (key in tab)
  {
      tab[key] = html_escape(tab[key]);
  }
  return(tab); 
}


$(document).ready(function(){
    
      // Enable autosubmit form after a change on the language drop box switcher
      $("#language_switch").change(function() { this.form.submit(); });

});