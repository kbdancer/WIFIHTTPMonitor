$(document).ready(function() {
	systeminfo.getSystemInfo()
});

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
                setInterval(systeminfo.getCurrentInfo,10000);
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
                nowBox.find('.uptime').text(data.current.uptime[0].split(',')[5]);
            }else{
                alert(data.msg);
            }
        },"json")
    }

}