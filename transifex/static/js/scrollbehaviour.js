$(function(){

  var jscroll;

   /* ================== Table Container ================== */


    $("table.stats-table").wrap('<div class="jscrollwrapper" />')
    $('div.jscrollwrapper').css({
      'min-width': '1000px',
      'max-height': '500px',
      'overflow-y': 'scroll',
      'overflow-x': 'visible'

    });


  /* ================== jScrollPane Scrolling Behaviour =====================*/


  //start jscrollpane for beautiful scrollbars
  jscroll = $('.jscrollwrapper')
    .on('jsp-scroll-y', jscrollBehaviour)
    .jScrollPane();

  function jscrollBehaviour(event, scrollPositionY, isAtTop, isAtBottom){
    if(isAtBottom){
      jscroll.off('jsp-scroll-y');
      $('#stat-row-container').infinitescroll('retrieve');
    }
  }


  //wait for drawing cause our bar is sensitive :-)
  setTimeout(function(){
    jscroll.data('jsp').reinitialise();
    $('.jscrollwrapper .jspVerticalBar').fadeOut(0);

    //pause infinitescroll
    $('#stat-row-container').infinitescroll('pause');
  },50)


  /* ================== BODY Scrolling Behavior =====================*/


    $('.jscrollwrapper').on('mouseleave.scrollbehaviour', function(){
      $('.jscrollwrapper .jspVerticalBar').stop().fadeOut()
    })
    .on('mouseenter.scrollbehaviour', function(){
      $('.jscrollwrapper .jspVerticalBar').stop().fadeIn()
    })
    .on('mousewheel.scrollbehaviour', function(event, delta){
      event.stopPropagation()
      event.preventDefault();
  })



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
    callback        : function(){console.log('Boom' + counter++);},
    loading: {
      img             : "http://www.deltametal.mk/system/pyrocms/themes/deltametal/images/loader_prodotti.gif",
       msgText         : "Loading more resources …" ,
    }
  }
  , function(newElements){

     // update scrollbar and reassign scroll listener and handler
      if(typeof jscroll !== 'undefined'){
        jscroll.data('jsp').reinitialise();
        $('.jscrollwrapper').on('jsp-scroll-y', jscrollBehaviour)
      }

		//window.console && console.log('context: ',this);
		//window.console && console.log('returned: ', newElements);

    });


	});
