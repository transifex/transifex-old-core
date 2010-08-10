watch_classes = Array('watch_add', 'watch_remove');

function watch_handler(data, textStatus)
{
    j = JSON.parse(data);
    // TODO: It's a hack
    if(j.project)
        obj = $('#watch-project')
    else
        obj = $('#watch-resource-' + String(j.id))

    if (j.error)
    {
        obj.attr('title', j.error);
        obj.removeClass('waiting');
        obj.addClass(j.style);
    }
    else
    {
        obj.attr('title', j.title);
        obj.click(click_function(obj, j.url))
        obj.removeClass('waiting');
        obj.addClass(j.style);
    };
}

function click_function(obj, url)
{
    return function()
    {
        watch_toggle(obj, url);
    }
}

function watch_toggle(obj, url)
{
    obj.onclick = null;
    o = $(obj);
    o.unbind('click');
    for (cls in watch_classes)
    {
        if (o.hasClass(watch_classes[cls]))
        {
            o.removeClass(watch_classes[cls]);
        }
    }
    o.addClass('waiting'); /* will be removed in the callback */
    $.post(url=url, callback=watch_handler, type='json');
}
