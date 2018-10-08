var vm = new Vue({
	el: '#app',
	data: {
		host:host,
		error_name: false,
		error_password: false,
		error_check_password: false,
		error_phone: false,
		error_allow: false,
		error_image_code: false,
		error_sms_code: false,
		sending_flag: false,

		username: '',
		password: '',
		password2: '',
		mobile: '', 
		image_code: '',
		sms_code: '',
		allow: false,
		error_name_message: '请输入5-20个字符的用户',
		error_phone_message: '您输入的手机号格式不正确',
		image_code_id: '',  // 图片验证码编号
    	image_code_url: '',  // 验证码图片路径
		sms_code_tip: '获取短信验证码',
		error_image_code_message: '请填写图片验证码',
		error_sms_code_message: '请填写短信验证码',

	},
		mounted: function() {
		this.generate_image_code();
	},
	methods: {
		 // 生成uuid
		generate_uuid: function(){
			var d = new Date().getTime();
			if(window.performance && typeof window.performance.now === "function"){
				d += performance.now(); //use high-precision timer if available
			}
			var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
				var r = (d + Math.random()*16)%16 | 0;
				d = Math.floor(d/16);
				return (c =='x' ? r : (r&0x3|0x8)).toString(16);
			});
			return uuid;
		},
		// 生成一个图片验证码的编号，并设置页面中图片验证码img标签的src属性
		generate_image_code: function(){
			// 生成一个编号
			// 严格一点的使用uuid保证编号唯一， 不是很严谨的情况下，也可以使用时间戳
			this.image_code_id = this.generate_uuid();

			// 设置页面中图片验证码img标签的src属性
			this.image_code_url = 'http://127.0.0.1:8000' + "/verifications/imagecodes/" + this.image_code_id + "/";
		},

		// 检查用户名
		check_username: function (){
			var len = this.username.length;
			if(len<5||len>20) {
				this.error_name = true;
			} else {
				this.error_name = false;
			}
			// 检查重名
            if (this.error_name == false) {
                axios.get(this.host +'/users/usernames/' + this.username + '/count/', {
                        responseType: 'json'
                    })
                    .then(response => {
                        if (response.data.count > 0) {
                            this.error_name_message = '用户名已存在';
                            this.error_name = true;
                        } else {
                            this.error_name = false;
                        }
                    })
                    .catch(error => {
                        console.log(error.response.data);
                    })
            }

		},

		// 检查密码
		check_pwd: function (){
			var len = this.password.length;
			if(len<8||len>20){
				this.error_password = true;
			} else {
				this.error_password = false;
			}		
		},
		//检查密码
		check_cpwd: function (){
			if(this.password!=this.password2) {
				this.error_check_password = true;
			} else {
				this.error_check_password = false;
			}		
		},

		// 检查手机号
		check_phone: function (){
			var re = /^1[3456789]\d{9}$/;
			if(re.test(this.mobile)) {
				this.error_phone = false;
			} else {
				this.error_phone = true;
			}
			 // 检查手机号是否重复
			 if (this.error_phone == false) {
                axios.get(this.host+'/users/phones/'+ this.mobile + '/count/', {
                        responseType: 'json'
                    })
                    .then(response => {
                        if (response.data.count > 0) {
                            this.error_phone_message = '手机号已存在';
                            this.error_phone = true;
                        } else {
                            this.error_phone = false;
                        }
                    })
                    .catch(error => {
                        console.log(error.response.data);
                    })
            }
		},

		// 检查图片验证码
		check_image_code: function (){
			if(!this.image_code) {
				this.error_image_code = true;
			} else {
				this.error_image_code = false;
			}	
		},

		//发送短信验证码
        send_sms_code: function () {
            if (this.sending_flag == true) {
                return;
            }
            this.sending_flag = true;

            // 校验参数，保证输入框有数据填写
            this.check_phone();
            this.check_image_code();

            if (this.error_phone == true || this.error_image_code == true) {
                this.sending_flag = false;
                return;
            }

            // 向后端接口发送请求，让后端发送短信验证码
            axios.get('http://127.0.0.1:8000' + '/verifications/smscodes/' + this.mobile + '/?text=' + this.image_code + '&image_code_id=' + this.image_code_id, {
                // 向后端声明，请返回json数据
                responseType: 'json'
            })
                .then(response => {
                    // 表示后端发送短信成功
                    // 倒计时60秒，60秒后允许用户再次点击发送短信验证码的按钮
                    var num = 60;
                    // 设置一个计时器
                    var t = setInterval(() => {
                        if (num == 1) {
                            // 如果计时器到最后, 清除计时器对象
                            clearInterval(t);
                            // 将点击获取验证码的按钮展示的文本回复成原始文本
                            this.sms_code_tip = '获取短信验证码';
                            // 将点击按钮的onclick事件函数恢复回去
                            this.sending_flag = false;
                        } else {
                            num -= 1;
                            // 展示倒计时信息
                            this.sms_code_tip = num + '秒';
                        }
                    }, 1000, 60)
                })
                .catch(error => {
                    if (error.response.status == 400) {
                        this.error_image_code_message = '图片验证码有误';
                        this.error_image_code = true;
                    } else {
                        console.log(error.response.data);
                    }
                    this.sending_flag = false;
                })
        },

		// 校验短信验证码
		check_sms_code: function(){
			if(!this.sms_code){
				this.error_sms_code = true;
			} else {
				this.error_sms_code = false;
			}
		},

		// 检查是否勾选
		check_allow: function(){
			if(!this.allow) {
				this.error_allow = true;
			} else {
				this.error_allow = false;
			}
		},


		// 注册
        on_submit: function(){
            this.check_username();
            this.check_pwd();
            this.check_cpwd();
            this.check_phone();
            this.check_sms_code();
            this.check_allow();


            if(this.error_name == false && this.error_password == false && this.error_check_password == false
                && this.error_phone == false && this.error_sms_code == false && this.error_allow == false) {
                axios.post('http://127.0.0.1:8000'+'/users/', {
                        username: this.username,
                        password: this.password,
                        password2: this.password2,
                        mobile: this.mobile,
                        sms_code: this.sms_code,
                        allow: this.allow.toString()
                    }, {
                        responseType: 'json'
                    })
                    .then(response => {
                        // 保存后端返回的token数据
                        localStorage.token = response.data.token;
                        localStorage.username = response.data.username;
                        localStorage.user_id = response.data.id;

                        location.href = '/index.html';
                    })
                    .catch(error=> {
                        if (error.response.status == 400) {
                            this.error_sms_code_message = '短信验证码错误';
                            this.error_sms_code = true;
                        } else {
                            console.log(error.response.data);
                        }
                    })
            }
        },
	}
});
