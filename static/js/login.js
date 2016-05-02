function login(argument) {
	var username = $('input[name="username"]').val(),password = $('input[name="password"]').val();

	$.post('/login', {"username": username,"password":md5(password)}, function(data, textStatus, xhr) {
		if(data.code == 0){
			alert('登录成功');
			window.location.href = '/manage';
		}else{
			alert(data.msg);
		}
	},"json");
}