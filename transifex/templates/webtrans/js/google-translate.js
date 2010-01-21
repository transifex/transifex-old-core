google.setOnLoadCallback(function() {
    $('.location a').show().toggle(function() {
        $('.hide', $(this).parent()).show();
    }, function() {
        $('.hide', $(this).parent()).hide();
    });

{% if WEBTRANS_SUGGESTIONS %}    
    source_lang = '{{ pofile.object.source_lang }}';
    file_lang = '{{ pofile.language_code }}';
    is_supported_lang = google.language.isTranslatable(file_lang);
    // If the main language code is not supported, try to find one from the code aliases
    if (!(is_supported_lang)){
        // Get aliases
        code_aliases = '{{ pofile.language.code_aliases }}';
        if(code_aliases){
            // Drop spaces in the beginning/end of the string and split it
            list = code_aliases.replace(/^ /,'').replace(/ $/,'').split(' ');
            for (i=0; i<list.length; i++){
                is_supported_lang = google.language.isTranslatable(list[i]);
                if (is_supported_lang){
                    i=list.length;
                }
            }
        }
    }
    is_supported_source_lang = google.language.isTranslatable(source_lang);
    if (is_supported_lang && is_supported_source_lang) {
	    $('a.suggest').click(function() {
	        var a=$(this), str=a.html();
            a.removeClass("action");
            a.addClass("action_go");
	        orig=$('.msg', a.parents('tr')).find('p:first').html();
	        trans=$('textarea', a.parents('tr'));
	        orig = unescape(orig).replace(/<br\s?\/?>/g,'\n').replace(/<code>/g,'').replace(/<\/code>/g,'').replace(/&gt;/g,'>').replace(/&lt;/g,'<');
	        google.language.translate(orig, source_lang, file_lang, function(result) {
	            if (!result.error) {
	                trans.val(unescape(result.translation).replace(/&#39;/g,'\'').replace(/&quot;/g,'"').replace(/%\s+(\([^\)]+\))\s*s/g,' %$1s '));
                        nkey = trans.attr('name').split('msgstr_field_')[1];
                        // from web_editor.js:
                        fuzzy(nkey);
                        $("input[name='fuzzy_field_"+nkey+"']").attr('disabled', '');
                        update_totals();
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
