$(document).ready(function() {
	$('#frameBox').css({"width":$(document).width(),"height":$(document).height() - 50});
});

function hideloading(){
	setTimeout(function(){$("#loading").hide()},1000);
}

function showloading(){
	$("#loading").show()
}