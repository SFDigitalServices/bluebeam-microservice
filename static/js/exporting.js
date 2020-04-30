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
                    self.successCount = response.data.data.success_count;
                    self.fails = response.data.data.failures;
                } else {
                    setTimeout(self.checkExportStatus, self.pollingInterval);
                }
            })
        }
    }
})