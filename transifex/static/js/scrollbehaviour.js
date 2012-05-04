$(function(){

  var jscroll;

  createTableContainer()

   /* ================== Table Container ================== */

  function createTableContainer(){
    $("table.stats-table").wrap('<div class="jscrollwrapper" />')
    $('div.jscrollwrapper').css({
      'min-width': '1000px',
      'max-height': '500px',
      'overflow-y': 'scroll',
      'overflow-x': 'visible'

    });


    //start jscrollpane for beautiful scrollbars
    jscroll = $('.jscrollwrapper')
      .on('jsp-scroll-y', function(event, scrollPositionY, isAtTop, isAtBottom){
          console.log('Handle jsp-scroll-y', this,
								'scrollPositionY=', scrollPositionY,
								'isAtTop=', isAtTop,
								'isAtBottom=', isAtBottom);
						if(isAtBottom){
						jscroll.off('jsp-scroll-y');
						  $('#stat-row-container').infinitescroll('retrieve');
						}
      })
      .jScrollPane();

      setTimeout(function(){
     jscroll.data('jsp').reinitialise();
     //pause infinitescroll
    $('#stat-row-container').infinitescroll('pause');

    },50)


  }



  /* ================== Infinite Scroll ================== */


	// hide pagination the first time, cause infinite scroll can't manage to ;-)
  $('.pagination').hide();

  /* call infinite scroll plugin to load more rows when user reaches end of page */
  $('#stat-row-container').infinitescroll({

    navSelector  	: ".pagination",
    nextSelector 	: ".pagination a.next",
    itemSelector 	: "#stat-row-container tr.stat-row",
    debug		 	: false,
    dataType	 	: 'html',
    animate         : false,
	//	img             : "{% static "images/icons/progress.gif" %}",
    msgText         : "Loading more resources …" ,
    callback        : function(){console.log('Boom' + counter++);},
  }
  , function(newElements){

     // update scrollbar and reassign scroll listener and handler
      if(typeof jscroll !== 'undefined'){
        jscroll.data('jsp').reinitialise();
        jscroll = $('.jscrollwrapper')
      .on('jsp-scroll-y', function(event, scrollPositionY, isAtTop, isAtBottom){
          console.log('Handle jsp-scroll-y', this,
								'scrollPositionY=', scrollPositionY,
								'isAtTop=', isAtTop,
								'isAtBottom=', isAtBottom);
						if(isAtBottom){
						jscroll.off('jsp-scroll-y');
						  $('#stat-row-container').infinitescroll('retrieve');
						}
      })
      }

		//window.console && console.log('context: ',this);
		//window.console && console.log('returned: ', newElements);

    });


	});
