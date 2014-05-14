sidebarSize = '165px';
sidebarVisible = false;
function toggleSidebar(){
	if(sidebarVisible){
		$('#sidebar').css("width",0);		
		$('div[data-role=page]').css("margin-left","0");
		$('div[data-role=content]').css("opacity","1");
		$(document).unbind("touchmove");
		$('body').width($(window).width());
	}else{
		$('#sidebar').css("width",sidebarSize);
		$('div[data-role=page]').css("margin-left",sidebarSize);
		$('div[data-role=content]').css("opacity","0.5");
		$(document).bind("touchmove",function(e){
            e.preventDefault();
        });
	}
	sidebarVisible = !sidebarVisible;		
}
