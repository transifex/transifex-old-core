/o* API call URLs */

url_api_languages = '/api/languages/';
url_api_storage = '/api/storage/';
url_api_storage_file = '/api/storage/%s/';
url_api_project = '/api/project/%s/files/';

/* Global functions */
function json_request(type, url, struct, callback) {
    if (callback) {
        var fp = function(xmlhttpreq, textStatus) {
//            alert(textStatus + ": " + xmlhttpreq.responseText);
            callback(textStatus, JSON.parse(xmlhttpreq.responseText));
        }
    } else {
        var fp = null;
    }
    $.ajax({
        contentType : 'application/json', /* Workaround for django-piston */
        url: url,
        global : false,
        type : type,
        dataType: 'text', /* Workaround for django-piston */
        data: JSON.stringify(struct), /* Workaround for django-piston */
        complete: fp,
    });
}

function size_format (filesize) {
        if (filesize >= 1073741824)
             return sprintf("%dGb", filesize / 1073741824);
        if (filesize >= 1048576)
             return sprintf("%dMb", filesize / 1048576);
        if (filesize >= 1024)
             return sprintf("%dKb", filesize / 1024);
        return sprintf("%d bytes", filesize);
};


/* StorageFile class */
function StorageFile(storage, storage_file) {
    
    var this_storage_file = this;
    this.storage = storage;
    if (storage_file['language'])
        this.language_code = storage_file['language']['code']; /* TODO: Rename model */
    else
        this.language_code = "";
    this.name = storage_file['name'];
    this.uuid = storage_file['uuid'];

    storage.files[this.uuid] = this; /* For faster lookup */
    this.mime_type = storage_file['mime_type'];
    this.size = storage_file['size'];
    this.total_strings = storage_file['total_strings'];

    this.extract = function(complete) {
        json_request(
            'POST',
            sprintf(url_api_project, this_storage_file.storage.project.slug),
            {'uuid':this_storage_file.uuid},
            complete);
    }

    this.remove = function(complete) {
        $.ajax({
            url : sprintf(url_api_storage_file, this.uuid),
            type : 'DELETE',
            complete : complete
        });

    }

    this.set_language = function(new_code) {
        this_storage_file.language_code = new_code; // TODO: validate
        $.ajax({
          url : sprintf(url_api_storage_file, this.uuid),
          contentType : 'application/json',
          type : 'POST',
          dataType : 'text',
          data : JSON.stringify({'language':this_storage_file.language_code}),
        });
    }

    this.render_table_row = function() {
        extra_buttons = "";
        if (this.project != '')
            extra_buttons += sprintf(
                "<td><span class=\"i16 branch buttonized_simple tipsy_enable extract\" title=\"Extract strings from file '%s' and place them into new translation resource\"></span></td>",
                this.name);
//         if (this.resource != '')
//             extra_buttons += "<td><a href=\"#\" class=\"i16 merge buttonized_simple tipsy_enable\" title=\"Merge strings from file '"+this.name+"' to current translation resource\"></a></td>"+

        return sprintf(
            "<tr>" +
            "<input name=\"uuid\" type=\"hidden\" value=\"%s\"/>" +
            "<td class=\"i16 text\">%s</td>" + 
            "<td>%s</td>" + 
            "<td>%s</td>" + 
            "<td>%s</td>" + 
            "<td><span class=\"i16 delete buttonized_simple tipsy_enable\" title=\"Delete uploaded file\"></span></td>" +
            extra_buttons +
            "</tr>",

            this.uuid,
            this.name,
            (this.size > 0) && size_format(this.size) || "0 bytes",
            this.total_strings || "-",
            (this.total_strings > 0) && languages.render_selector(this.uuid, this.language_code) || "Unknown format"
        ); 
    }

    this.toString = function() {
        return sprintf("StorageFile(uuid='%s');", this.uuid);
    }
}

function Storage(files) {
    var this_storage = this;
    this_storage.files = []; /* Storage.files[uuid] = StorageFile() */
    content = "";

    for(var key in files) {
        var sf = new StorageFile(this, files[key]);
        content += sf.render_table_row();
        this_storage.files[sf.uuid] = sf;
    }

    /* Update table body */
    $("table#storage_files tbody").html(content);

    /* Language combobox */
    $("table#storage_files tbody tr td select.language").change(function(){
        var storage_file_uuid = $(this).attr('name');
        var new_lang_code = $("option:selected", this).val();
        this_storage.files[storage_file_uuid].set_language(new_lang_code);
    });

    /* Delete button */
    $("table#storage_files tbody tr td span.delete").click(function(){
        var tr = $(this).parents("tr");
        var uuid = $("input", tr).val();
        this_storage.files[uuid].remove(function(){
          tr.fadeOut("slow");
        });
    });
    
    /* Extract strings button */
    $("table#storage_files tbody tr td span.extract").click(function(){
        var tr = $(this).parents("tr");
        var uuid = $("input", tr).val();
        var storage_file = this_storage.files[uuid];
        if (storage_file.language_code == "") {
            alert("Please select language first");
            return
        }
        $("div#notification-container div").html(sprintf("Extracting strings from '%s', this might take a while...",storage_file.name));
        $("div#notification-container").fadeIn("slow");

        storage_file.extract(function(status, retval){
          $("div#notification-container").fadeOut("slow");
          window.location = retval['redirect'];
        });

    });
}


/* Language class */
function Language(code, aliases, name) {
    this.code = code;
    this.aliases = aliases;
    this.name = name;
    this.toString = function() {
        return sprintf("Language(code='%s',aliases='%s',name='%s');", this.code, this.aliases, this.name);
    }   
}

function Languages() {
    /* Languages class is used to pull languages 
     * from Transifex and to generate language 
     * selectors on client side */
    zork = this;
    this.languages = [];
    this.timestamp = null;

    /* Languages.pull() pulls languages from Transfifex */
    this.pull = function() {
        $.ajax({
            url : url_api_languages,
            contentType : 'application/json',
            data : '',
            type : 'GET',
            dataType : 'text',
            async : true,
            complete : function(xmlhttpreq, textStatus) {
                data = JSON.parse(xmlhttpreq.responseText);
                i = 0
                for (var key in data) {
                    zork.languages[i] = new Language(data[key]['code'], data[key]['code_aliases'], data[key]['name']);
                    i++;
                }
            }
        });
    }

    /* Languages.render_selector renders HTML fragment of combobox */
    this.render_selector = function(element_name, selected_language_code) {
        html = sprintf("<select name=\"%s\" class=\"language\"><option value=\"\">Not detected</option>", element_name);
        for (var i=0; i<zork.languages.length; i++) {
            html += sprintf(
                "<option value=\"%s\"%s>%s</option>",
                zork.languages[i].code,
                (zork.languages[i].code == selected_language_code) && " selected=\"selected\"",
                zork.languages[i].name
            );
        }
        return html + "</selected>";
    }
}
