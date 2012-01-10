$(document).ready(function (){
	$(".tipsy_enable").tipsy({'html':true, 'gravity':'s'});

  if($('input#id_project-tags').length>0) {
		$('input#id_project-tags').relatedTagsCloud();
	}
	
	var fieldColumnsa = {
    "fieldsLeft": [
        "project-slug",
        "project-description",
 				"project-source_language",
 				"project-private",
 				"project-fill_up_resources"
    ],
    "fieldsRight": [
        "project-name",
        "project-license",
 				"project-maintainers"
    ]
	};
	$("#project-forma").dualtxf(fieldColumnsa);

  var fieldColumnsb = {
    "fieldsLeft": [
        "project-homepage",
 				"project-feed",
 				"project-long_description"
 				"logo",
    ],
    "fieldsRight": [
        "project-trans_instructions",
 				"project-bug_tracker",
 				"project-webhook",
 				"project-auto_translate_select_service",
 				"project-auto_translate_api_key"
    ]
	};
  $("#project-formb").dualtxf(fieldColumnsb);
	
  
	if($("#project-edit-advanced ul.errorlist").length>0){
		$(".tx-form #project-edit-advanced").slideDown("fast",function(){$(".side-menu").css('height',$(".psettings-content").height());}); }			$(".side-menu").css('height',$(".psettings-content").height()+$("#project-tags").height());
  
  /* Prevent form submit when enter is pressed in maintainers input field */
  $('input#id_project-maintainers_text').bind('keypress', function(e){
      if (e.which == 13)
      return false;
  });

	$('.tx-form .required, .tx-form .field-helptext').each(function(){
		$(this).appendTo($(this).siblings('label'));
	});
	/*Check if there are errors in the slidable form. If yes then slides down*/
	$('.tx-form #display-advform').click(function(){
		$(this).toggleClass("active");
		$(".tx-form #project-edit-advanced").slideToggle("fast",function(){$(".side-menu").css('height',$(".psettings-content").height());});
	});
	

  var $source_language_select = $("select#id_project-source_language");
  $source_language_select.addClass("chzn-select");
  $('span#selectproject-source_language').remove();
  $source_language_select.chosen();
});


