var app = new Vue({
    el: '#app',
    mounted:function(){
        setTimeout(this.checkExportStatus, this.pollingInterval);
    },
    data: {
        isExporting:true,
        pollingInterval:5000, //5 secs
        successCount:0,
        fails:[]
    },
    methods: {
        checkExportStatus:function(){
            var self = this;
            return axios.get('/export/status', {
                params: {
                    export_id: exportId
                }
            }).then(function(response){
                if (response.data.data.is_finished) {
                    self.isExporting = false;
                    self.success = response.data.data.success;
                    self.failure = response.data.data.failure;
                } else {
                    setTimeout(self.checkExportStatus, self.pollingInterval);
                }
            })
        }
    }
})