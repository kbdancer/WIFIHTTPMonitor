$(document).ready(function() {
	$('#frameBox').css({"width":$(document).width(),"height":$(document).height() - 50});
    $('#navbar').find('li').click(function(){
        $('#navbar').find('li').removeClass('active')
        $(this).addClass('active')
    });
});

function hideloading(){
	setTimeout(function(){$("#loading").hide()},1000);
}

function showloading(){
	$("#loading").show()
}