
function toggle_entries(entries_status){
    /*
    Toggle entries of the online translation form filtering the rows by the
    status of each entry.
    */
    $("textarea[name*='msgstr_field_'][class='"+entries_status+"']").each(function(){
        nkey = $(this).attr('name').split('msgstr_field_')[1];
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

    // Repaginate table
    $('table.trans_web_edit').trigger('setupPagination');

    // Update zebra rows in the table
    $("#trans_web_edit")
        .trigger("update")
        .trigger("appendCache");
}

$(function(){

    // Actions for when the Fuzzy checkbox changes
    $("input[name*='fuzzy_field_']").change(function () {
        nkey = $(this).attr('name').split('fuzzy_field_')[1];

        $("input[name*='changed_field_"+nkey+"']").attr('value', 'True');
        if(this.checked){
            $("textarea[name='msgstr_field_"+nkey+"']")
                .addClass('fuzzy')
                .removeClass('translated')
                .removeClass('untranslated');
        }else{
            $("textarea[name='msgstr_field_"+nkey+"']").removeClass('fuzzy');
            if($("textarea[name='msgstr_field_"+nkey+"']").val() == ''){
                $("textarea[name='msgstr_field_"+nkey+"']").addClass('untranslated');
            }else{
                $("textarea[name='msgstr_field_"+nkey+"']").addClass('translated');
            }
        }
    })

      // Actions for when the Translation field changes
    $("textarea[name*='msgstr_field_']").keyup(function () {
        nkey = $(this).attr('name').split('msgstr_field_')[1];

        $("input[name='changed_field_"+nkey+"']").attr('value', 'True');

        if($(this).val() == ''){
            $("textarea[name='msgstr_field_"+nkey+"']")
                .addClass('untranslated')
                .removeClass('fuzzy')
                .removeClass('translated');
            $("input[name='fuzzy_field_"+nkey+"']").attr('disabled', 'disabled');
        }else{
            $("textarea[name='msgstr_field_"+nkey+"']")
                .addClass('translated')
                .removeClass('fuzzy')
                .removeClass('untranslated');
            $("input[name='fuzzy_field_"+nkey+"']").attr('disabled', '');
        }
        $("input[name='fuzzy_field_"+nkey+"']").attr('checked', false);
    })

    // Disabling the Fuzzy checkbox for untranslated entries
    $("textarea[name*='msgstr_field_'][value='']").each(function(){
        nkey = $(this).attr('name').split('msgstr_field_')[1];
        $("input[name='fuzzy_field_"+nkey+"']").attr('disabled', 'disabled');
    });

    // Actions for show/hide translated entries
    $("input[name='only_translated']").change(function(){
          toggle_entries('translated')
    })

    // Making translated entries hidden by default
    $("input[name='only_translated']").attr('checked', false);
    toggle_entries('translated')

    // Actions for show/hide fuzzy entries
    $("input[name='only_fuzzy']").change(function () {
          toggle_entries('fuzzy')
    })

    // Actions for show/hide untranslated entries
    $("input[name='only_untranslated']").change(function () {
         toggle_entries('untranslated')
    })

    table_pagination('table.trans_web_edit')

});