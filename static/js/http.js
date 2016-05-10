$(document).ready(function() {
    getHTTP();
    setInterval(getHTTP,3000);
});

function getHTTP(){
    $.ajax({
        url: '/queryHttp',
        type: 'GET',
        dataType: 'json',
        data: {},
        success:function(data){
            window.parent.hideloading();
            if(data.rows.length <1){
                $('.httptable').find('tbody').html('<tr><td colspan="7">No Data!</td></tr>')
            }else{
                $('.httptable').find('tbody').empty()
            }

            for(var thishttp = 0;thishttp < data.rows.length;thishttp++){
                $('.httptable').find('tbody').append(
                    '<tr>'+
                        '<td>'+ data.rows[thishttp].type +'</th>'+
                        '<td><p title="'+ data.rows[thishttp].host +'">'+ data.rows[thishttp].host +'</p></td>'+
                        '<td><p title="'+ data.rows[thishttp].uri +'">'+ data.rows[thishttp].uri +'</p></td>'+
                        '<td><p title="'+ data.rows[thishttp].referer +'">'+ data.rows[thishttp].referer +'</p></td>'+
                        '<td><p title="'+ data.rows[thishttp].ua +'">'+ data.rows[thishttp].ua +'</p></td>'+
                        '<td><p title="'+ data.rows[thishttp].cookie +'">'+ data.rows[thishttp].cookie +'</p></td>'+
                        '<td>'+ data.rows[thishttp].createtime +'</td>'+
                    '</tr>'
                );
            }
            
        }
    })
}