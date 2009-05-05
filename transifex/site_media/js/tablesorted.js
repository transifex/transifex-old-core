$(document).ready(function(){

    // ordering for Release stats table
    $("#stats_release").tablesorter({
        widgets: ['zebra'],
        headers: {
            1: { sorter: "percent"}
        },
        textExtraction: { // Take value inside an object for the columns
            0: function(node) {
                return $("a", node).text();
            },
            1: function(node) {
                return $(".stats_string_comp", node).text();
            }
        }
    });

    // ordering for Language x Release stats table
    $("#stats_lang").tablesorter({
        widgets: ['zebra'],
        headers: {
            1: { sorter: "percent"},
            2: { sorter: false } // Do not sort the third column
        },
        textExtraction: { // Take value inside an object for the columns
            0: function(node) {
                return $("a", node).text();
            },
            1: function(node) {
                return $(".stats_string_comp", node).text();
            }
        }
    });

    // ordering for Component stats table
    if (calcstats) {
        $("#stats_comp").tablesorter({
            widgets: ['zebra'],
            headers: {
                1: { sorter: "percent"},
                2: { sorter: false } // Do not sort the third column
            },
            textExtraction: { // Take value inside an object for the columns
                0: function(node) {
                    return $("a", node).text();
                },
                1: function(node) {
                    return $(".stats_string_comp", node).text();
                }
            }
        });
    }

    // ordering for Component Multifile Language stats table
    $("#stats_comp_lang").tablesorter({
        widgets: ['zebra'],
        headers: {
            1: { sorter: "percent"},
            2: { sorter: false } // Do not sort the third column
        },
        textExtraction: { // Take value inside an object for the columns
            0: function(node) {
                return $("a", node).text();
            },
            1: function(node) {
                return $(".stats_string_comp", node).text();
            }
        }
    });

});
