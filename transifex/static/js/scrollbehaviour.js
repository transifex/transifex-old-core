$(function(){
  //create and cache the more link button
  var $morelink = $("<a/>", {
                  id: 'more-link',
                  href: '#',
                  text: 'Fetch more',
                  style: 'position:relative;color:#fff; background-color:#3D658D; top:10px; left:300px;height:30px; line-height:30px; text-align:center; width:400px;display:block; border: 1px solid #3D658D; border-radius:5px; font-weight:bold'
                });

  var hasButtonBehaviour = false;

  var jscroll;


  /* ================== Checkbox Logic ================= */

  var $chkboxlabel = $("<span>", {
                  id: 'chk-scrollbar',
                  label: 'Scrollbars',
                  text: 'Scrollbar ',
                  style: 'color: #C57230;font-weight: 600;'
                });

   var $chkbox = $("<input type='checkbox'/>", {
                  id: 'chk-scrollbar',
                  label: 'Scrollbars',
                  style: ''
                });

  var $scrolloption =  $("<div>", {
                          id: 'scrolloption',
                          style : 'position:absolute; top:240px; left:1050px;'
                        }).append($chkboxlabel, $chkbox);

  $('.separate-header').eq(0).append($scrolloption);


  if(typeof $.cookie('loadmore.scrollbar') === 'undefined'){
      $.cookie('loadmore.scrollbar', 'false', 1)
  }else{
       if($.cookie('loadmore.scrollbar') == 'true'){
          $chkbox.attr('checked', true)
       }
  }


  $chkbox.on('change.loadmore', function(){
    if ($chkbox.attr('checked') == 'checked'){
      $.cookie('loadmore.scrollbar', 'true', 1)

    }else{
      $.cookie('loadmore.scrollbar', 'false', 1)

    }
    init($chkbox.attr('checked'))
  })

  init($chkbox.attr('checked'))

  function init(hasScrollbar){
    //console.log('hasScrollbar '+ hasScrollbar);

    if(typeof hasScrollbar !== 'undefined' && hasScrollbar == 'checked'){
      createTableContainer()
      hasButtonBehaviour = false;
      $morelink.remove();
    }else{
      removeTableContainer()
      hasButtonBehaviour = true;
    }
  }

   /* ================== Table Container ================== */

  function createTableContainer(){
    $("table.stats-table").wrap('<div class="tablewrapper" />')
    $('div.tablewrapper').css({
      'min-width': '1000px',
      'max-height': '500px',
      'overflow-y': 'scroll',
      'overflow-x': 'visible'

    });


    //start jscrollpane for beautiful scrollbars
    jscroll = $('.tablewrapper')
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

   /*
 $('div.tablewrapper').on('mouseover.loadmore', function(){
        $('#stat-row-container').infinitescroll('resume');
    });

    $('div.tablewrapper').on('mouseout.loadmore', function(){
        $('#stat-row-container').infinitescroll('pause');
    });
*/

  }

    function removeTableContainer(){

    //removescrollbar
    /*
if(typeof jscroll !== 'undefined'){
      console.log(jscroll);
      jscroll.data('jsp').destroy();
    }
*/
    $("table.stats-table").unwrap('.tablewrapper')



    $('div.tablewrapper').off('mouseover.loadmore');
    $('div.tablewrapper').off('mouseout.loadmore');

    $('#stat-row-container').infinitescroll('resume');


  }


  /* ================== Infinite Scroll ================== */

  // count how many ajax calls we make and threshold for showing more button
  var cnt = 0
  , autoLoadThreshold = 2




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

      if(typeof jscroll !== 'undefined'){
        jscroll.data('jsp').reinitialise();
        jscroll = $('.tablewrapper')
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


      if(++cnt % autoLoadThreshold == 0){
        if(hasButtonBehaviour)showMoreButton();
        //pause infinitescroll and append 'more-link'

      }
		//window.console && console.log('context: ',this);
		//window.console && console.log('returned: ', newElements);

    });

    function showMoreButton(){
      $('#stat-row-container').infinitescroll('pause');
      $('#stat-row-container').append($morelink)

       //add 'more-link' button click handler exactly once
       //we remove and add the listener to deal with the fact that
       //when the $morelink is removed from the DOM, the e.preventDefault
       //behaviour breaks

       $morelink.off('click.loadmore')
       $morelink.on('click.loadmore', function(e){
      e.preventDefault();

      //remove more link, fetch more data and resume infinite scroll
      $morelink.remove();
       $('#stat-row-container').infinitescroll('retrieve');
       $('#stat-row-container').infinitescroll('resume');
    })

    }

    setTimeout(function(){
     if(hasButtonBehaviour)showMoreButton();
    },50)


	});
