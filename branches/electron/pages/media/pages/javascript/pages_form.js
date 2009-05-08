/* Initialization of the change_form page - this script is run once everything is ready. */

$(function() {
    // Hide form rows containing only hidden inputs
    $('.form-row').each(function() {
        if (!$('p, label, select, input:not([type=hidden])', this).length) {
            $(this).hide();
        }
    });
    
    // Focus the title
    $('#id_title').focus();
    
    // Automatically update the slug when typing the title
    var slug_auto = true;
    var slug = $("#id_slug").change(function() {
        slug_auto && (slug_auto = false);
    });
    $("#id_title").keyup(function() {
        slug_auto && slug.val(URLify(this.value, 64));
    });
    
    // Set the publication status
    var select = $('#id_status');
    var opt = ({ 0: 'draft', 1: 'published', 3: 'hidden' })[select.val()];
    var img = $('<img src="/media/pages/images/icons/'+opt+'.gif" alt="'+opt+'" />').insertAfter(select);
    select.change(function(e) {
        pages.update_published_icon('', select, img);
    });
    
    // Translation helper
    $('#translation-helper-select').change(function() {
        var index = this.selectedIndex;
        if (index) {
            $.get(window.location.href.split('?')[0]+'traduction/'+this.options[index].value+'/', function(html) {
                $('#translation-helper-content').html(html).show();
            });
        } else {
            $('#translation-helper-content').hide();
        }
    });
    
    // Select the appropriate template option
    var template = $.query.get('template');
    if (template) {
        $('#id_template option').each(function() {
            if (template == this.value) {
                $(this).attr('selected', true);
                return false;
            }
        });
    }
    
    // Confirm language and template change if page is not saved
    $.each(['language', 'template'], function(i, label) {
        var select = $('#id_'+label);
        if (select.length) {
            var orig_ = select.val();
            select.change(function() {
                var query = $.query.set(label, orig_).set('new_'+label,select.val()).toString();
                select.val(orig_);
                $('#page_form').attr('action',query);
                $('input[name=_continue]').click();
            });
        }
    });
    
    // Disable the page content if the page is a redirection
    var redirect = $('#id_redirect_to').change(update_redirect);
    var affected = $('.form-row:has(#id_language), .form-row:has(#id_template), .module-content .form-row')
        .css('position', 'relative');
    var overlay = $('<div class="overlay"></div>').css({
            'display': 'none',
            'position': 'absolute',
            'z-index': '1000',
            'top': '0',
            'left': '0',
            'height': '100%',
            'width': '100%',
            'opacity': '0.66',
            'background': 'white'
        }).appendTo(affected);
    function update_redirect() {
        redirect.val() ? overlay.show() : overlay.hide();
    }
    update_redirect();
    
    // Content revision selector
    $('.revisions').change(function () {
        var select = $(this);
        var val = select.val();
        if (val) {
            $.get(val, function (html) {
                var formrow = select.closest('.form-row');
                if ($('a.disable', formrow).length) {
                    $('iframe', formrow)[0].contentWindow.document.getElementsByTagName("body")[0].innerHTML = html;
                } else {
                    var formrow_textarea = $('textarea', formrow).val(html);
                    // support for WYMeditor
                    if (WYMeditor) {
                        $(WYMeditor.INSTANCES).each(function (i, wym) {
                            if (formrow_textarea.attr('id') === wym._element.attr('id')) {
                                wym.html(html);
                            }
                        });
                    }
                }
            });
        }
        return false;
    });
    
    $('.js-confirm-delete').click(function() {
        return confirm(gettext('Are you sure you want to delete this content?'));
    });
});
