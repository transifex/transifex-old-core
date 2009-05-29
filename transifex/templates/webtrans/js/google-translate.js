google.setOnLoadCallback(function() {
    $('.location a').show().toggle(function() {
        $('.hide', $(this).parent()).show();
    }, function() {
        $('.hide', $(this).parent()).hide();
    });

{% if WEBTRANS_SUGGESTIONS %}    
    is_supported_lang = google.language.isTranslatable('{{ pofile.language_code }}');
    if (is_supported_lang) {
	    $('a.suggest').click(function() {
	        var a=$(this), str=a.html();
            a.removeClass("action");
            a.addClass("action_go");
	        orig=$('.msg', a.parents('tr')).html();
	        trans=$('textarea', a.parents('tr'));
	        orig = unescape(orig).replace(/<br\s?\/?>/g,'\n').replace(/<code>/g,'').replace(/<\/code>/g,'').replace(/&gt;/g,'>').replace(/&lt;/g,'<');
	        google.language.translate(orig, "en", "{{ pofile.language_code }}", function(result) {
	            if (!result.error) {
	                trans.val(unescape(result.translation).replace(/&#39;/g,'\'').replace(/&quot;/g,'"').replace(/%\s+(\([^\)]+\))\s*s/g,' %$1s '));
                        nkey = trans.attr('name').split('msgstr_field_')[1];
                        fuzzy(nkey); // from web_editor.js
	                a.hide();
	            } else {
	                a.before($('<span class="alert">'+result.error.message+'</span>'))
	                a.hide();
	            }
	        });
	        return false;
	    })
	} else {
        $('.suggest_container').hide()	  
	}
{% endif %}
});
