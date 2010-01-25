
function toggle_entries(entries_status){
    /*
    Toggle entries of the online translation form filtering the rows by the
    status of each entry.
    */
    $("textarea[name*='msgstr_field_']."+entries_status).each(function(){
        nkey = $(this).attr('name').split('msgstr_field_')[1].split('_')[0];
        if($("input[name='only_"+entries_status+"']").is(':checked')){
            $("tr[id='msgstr_field_"+nkey+"']")
                .attr('style', '')
                .removeClass('filtered');
        }else{
            $("tr[id='msgstr_field_"+nkey+"']")
                .attr('style', 'display: none;')
                .addClass('filtered');
        }
    });

    // Update zebra rows in the table
    $("#trans_web_edit")
        .trigger("update")
        .trigger("appendCache");
}

function toggle_occurrences(){
        if($("input[name='toggle_occurrences']").is(":checked")){
            $(".occurrences").show()
        }else{
            $(".occurrences").hide();
        }
    }

function toggle_contexts(){
        if($("input[name='toggle_contexts']").is(":checked")){
            $(".contexts").show();

        }else{
            $(".contexts").hide();
        }
    }

function fuzzy(nkey){
    $("input[name='fuzzy_field_"+nkey+"']").attr('checked', true);
    $("textarea.msgstr_field_"+nkey)
        .addClass('fuzzy')
        .removeClass('translated')
        .removeClass('untranslated');
}

function unfuzzy(nkey){
    $("input[name='fuzzy_field_"+nkey+"']").attr('checked', false);
    $node = $("textarea.msgstr_field_"+nkey)
    $node.removeClass('fuzzy');
    if($node.val() == ''){
        $node.addClass('untranslated');
    }else{
        $node.addClass('translated');
    }
}

/* Update totals functions */

// FIXME: This should be global or something, not calculated every time.
// These should be called once when the page loads. They make sure that the
// total sum shown reflects the actual table.
function get_total_sum() { return $("tr[id*='msgstr_field_'] textarea:first-child").length; }
function update_total_sum() {  $("#total_sum").text(get_total_sum()); }

function get_total(w) { return $("tr[id*='msgstr_field_'] textarea:first-child." + w).length; }



function get_total_perc(w) {
    // Return the percentage of the count
    if (w != 'untrans') {
        num = get_total(w);
    } else {
        // Hack to always have a total percentage sum of 100%:
        num = get_total_sum() - get_total("translated") - get_total("fuzzy");
    }
    return Math.floor(num * 100 / get_total_sum());
}

function update_total(w) {
    $("#total_" + w).text(get_total(w));
    $("#total_" + w + "_perc").text(get_total_perc(w) + '%');
}

function update_totals() {
    // Update the totals
    // Should be called whenever something on the table changes.
    update_total('translated');
    update_total('fuzzy');
    update_total('untranslated');
}


$(function(){
    // Run a first update on the totals, just to be sure they are accurate.
    update_total_sum();
    update_totals();

    // Actions for when the Fuzzy checkbox changes
    $("input[name*='fuzzy_field_']").change(function () {

        nkey = $(this).attr('name').split('fuzzy_field_')[1];
        if($(this).is(":checked")){
            fuzzy(nkey)
        }else{
            unfuzzy(nkey)
        }
        update_totals();
    })

    // Actions for when the Translation field changes
    $("textarea[name*='msgstr_field_']").keyup(function () {
        nkey = $(this).attr('name').split('msgstr_field_')[1].split('_')[0];

        if($(this).val() == ''){
            $("textarea.msgstr_field_"+nkey)
                .addClass('untranslated')
                .removeClass('fuzzy')
                .removeClass('translated');
            $("input[name='fuzzy_field_"+nkey+"']").attr('disabled', 'disabled');
        }else{
            $("textarea.msgstr_field_"+nkey)
                .addClass('translated')
                .removeClass('fuzzy')
                .removeClass('untranslated');
            $("input[name='fuzzy_field_"+nkey+"']").attr('disabled', '');
        }
        $("input[name='fuzzy_field_"+nkey+"']").attr('checked', false);
        update_totals();
    })

    // Disabling the Fuzzy checkbox for untranslated entries
    $("textarea[name*='msgstr_field_']").each(function(){
        if($(this).text() == ''){
            nkey = $(this).attr('name').split('msgstr_field_')[1].split('_')[0];
            $("input[name='fuzzy_field_"+nkey+"']").attr('disabled', 'disabled');
        }
    });

    // Actions for show/hide translated entries
    $("input[name='only_translated']").change(function(){
          toggle_entries('translated')
    })

    // Making translated entries hidden by default
    //$("input[name='only_translated']").attr('checked', false);
    //    toggle_entries('translated')

    // Actions for show/hide fuzzy entries
    $("input[name='only_fuzzy']").change(function () {
          toggle_entries('fuzzy')
    })

    // Actions for show/hide untranslated entries
    $("input[name='only_untranslated']").change(function () {
         toggle_entries('untranslated')
    })

    // Hide check fields for show/hide translated/fuzzy/untranslated fields
    $("input[name*='only_']").hide()

    // Actions for show/hide occurrence column in the table
    $("input[name='toggle_occurrences']").change(function(){
        toggle_occurrences()
    })
    toggle_occurrences()

    $("input[name='toggle_contexts']").change(function(){
        toggle_contexts()
    })
    toggle_contexts()

    // Copy source string button 
    $('span.copy_source').click(function() { 
        var a=$(this), str=a.html(); 
        orig=$('.msg', a.parents('tr')).find('p:first').html(); 
        trans=$('textarea', a.parents('tr')); 
        orig = unescape(orig).replace(/<br\s?\/?>/g,'\n').replace(/<code>/g,'').replace(/<\/code>/g,'').replace(/&gt;/g,'>').replace(/&lt;/g,'<'); 
        trans.val(orig) 
        nkey = trans.attr('name').split('msgstr_field_')[1]; 
        // from web_editor.js: 
        fuzzy(nkey); 
        $("input[name='fuzzy_field_"+nkey+"']").attr('disabled', ''); 
        update_totals(); 
        return false; 
    }) 

});

