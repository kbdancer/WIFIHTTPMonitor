$(document).ready(function() {
	getUsers();
	// setInterval(getUsers,5000);
});

function getUsers(){
	$.ajax({
		url: '/queryUser',
		type: 'GET',
		dataType: 'json',
		data: {},
		success:function(data){
			window.parent.hideloading();
			if(data.rows.length <1){
				$('.userstable').find('tbody').html('<tr><td colspan="7">No Data!</td></tr>')
			}else{
				$('.userstable').find('tbody').empty()
			}

			for(var user = 0;user < data.rows.length;user++){
				$('.userstable').find('tbody').append(
					'<tr>'+
                        '<td>'+ data.rows[user].client +'</th>'+
                        '<td>'+ data.rows[user].mac +'</td>'+
                        '<td>'+ data.rows[user].ip +'</td>'+
                        '<td>'+ data.rows[user].uid +'</td>'+
                        '<td>'+ data.rows[user].start +'</td>'+
                        '<td>'+ data.rows[user].createtime +'</td>'+
                    '</tr>'
                );
			}
			
		}
	})
}