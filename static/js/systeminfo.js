$(document).ready(function() {
	systeminfo.getSystemInfo()
});

var allwirelessface = []
var allinetface = []

var systeminfo = {
	getSystemInfo:function(){
		$.post('/allinfo', {}, function(data, textStatus, xhr) {
			if(data.code == 0){
                // set system info
                var baseBox = $('.linuxBase');
                baseBox.find('.hostname').text(data.system.hostname);
                baseBox.find('.release').text(data.system.release);
                baseBox.find('.version').text(data.system.version[0]+'_'+data.system.version[1]+'_'+data.system.version[2]);
                baseBox.find('.machine').text(data.system.machine);
                baseBox.find('.processor').text(data.system.processor);
                baseBox.find('.starttime').text(data.system.starttime);
                // set hard info
                var heardBox = $('.hardBase');
                heardBox.find('.logiccore').text(data.hard.logiccore+"核心");
                heardBox.find('.phycore').text(data.hard.phycore+"核心");
                heardBox.find('.phymem').text(data.hard.phymem+"M");
                heardBox.find('.disktotal').text(data.hard.disktotal+"G");
                heardBox.find('.diskused').text(data.hard.diskused+"G");
                heardBox.find('.diskfree').text(data.hard.diskfree+"G");
                var nowBox = $('.nowBase');
                nowBox.find('.thispid').text(data.os.thisPid);

                systeminfo.getCurrentInfo()
				systeminfo.getIface()
                // setInterval(systeminfo.getCurrentInfo,10000);
			}else{
				alert(data.msg);
			}
		},"json");
	},
    getCurrentInfo:function () {
        $.post('/getCurrent', {}, function(data, textStatus, xhr) {
            if(data.code == 0){
                var nowBox = $('.nowBase');
                nowBox.find('.cpuused').text(data.current.cpuused+"%");
                nowBox.find('.memused').text(data.current.memused+"%");
                nowBox.find('.diskused').text(data.current.diskused+"%");
                nowBox.find('.pidcount').text(data.current.pidcount);
                nowBox.find('.uptime').text(data.current.uptime[0].split('average:')[1]);
            }else{
                alert(data.msg);
            }
        },"json")
    },
    getIface:function(){
        $.post('/getInterface', {}, function(data, textStatus, xhr) {
            if(data.code == 0){

				if(data.interfaces.length<1){
                    $('.interfaceBase').find('tbody').html('<tr><td colspan="4">未检测到网络接口</td></tr>');
                }else{
                    $('.interfaceBase').find('tbody').empty();
                }

                $('.innet_list').empty()
                allinetface = []

                for(var i=0;i<data.interfaces.length;i++){
                    if(data.interfaces[i].status == "连接"){
                        allinetface.push(data.interfaces[i].name)
                        $('.innet_list').append('<option value="'+data.interfaces[i].name+'">'+ data.interfaces[i].name +'</option>');
                    }
                    $('.interfaceBase').find('tbody').append('<tr><td>'+ data.interfaces[i].name +'</td><td>'+ data.interfaces[i].mac +'</td><td>'+ data.interfaces[i].status +'</td><td>'+data.interfaces[i].ip+'</td></tr>');
                }

                allwirelessface = []

                for(var w=0;w<data.wireless.length;w++){
                    allwirelessface.push(data.wireless[w])
                }

                if(allinetface.length < 1){
                    $('.inetlistbox').hide();
                    $('.wslistbox').hide();

                    $('.noinetiface').show();
                    $('.nowireiface').hide();
                }else{
                    $('.inetlistbox').show();
                    $('.wslistbox').hide();

                    $('.noinetiface').hide();
                    $('.nowireiface').hide();

                    systeminfo.setWireless()
                }

            }else{
                alert(data.msg);
            }
        },"json")
    },
    setWireless:function(){
        var inet = $('.innet_list').val(),useableWireless = [];

        $('.wireless_list').empty()
        for(var i=0;i<allwirelessface.length;i++){
            if(allwirelessface[i] != inet){
                useableWireless.push(allwirelessface[i])
                $('.wireless_list').append('<option value="'+allwirelessface[i] +'">'+ allwirelessface[i]  +'</option>');
            }
        }

        if(useableWireless.length < 1){
            $('.wslistbox').hide();
            $('.nowireiface').show();
        }else{
            $('.wslistbox').show();
            $('.nowireiface').hide();
        }
    },
    cleanEnv:function(){
        $.post('/rmMon', {}, function(data, textStatus, xhr) {
            if(data.code == 0){
                systeminfo.getIface()
                alert('Success!')
            }else{
                alert(data.msg)
            }
        },"json");
    },
    createap:function(){
        var iface = $('.wireless_list').val(),inet = $('.innet_list').val(),ssid = $("#wireless_ssid").val(),key = $("#wireless_key").val();

        if(ssid.length<1){ alert('SSID 不能为空');return; }
        $.post('/createAp', {"inet":inet,"ap":iface,"ssid":ssid,"key":key}, function(data, textStatus, xhr) {
            if(data.code == 0){
                systeminfo.getIface()
            }else{
                alert(data.msg)
            }
        },"json");
    }
}
