function ContextMenu(menu, options){
	var self = this;
	var num = ContextMenu.count++;

	this.menu = menu;
	this.contextTarget = null;

	if(!(menu instanceof Array)){
		throw new Error("Parameter 1 must be of type Array");
	}

	if(typeof options !== "undefined"){
		if(typeof options !== "object"){
			throw new Error("Parameter 2 must be of type object");
		}
	}else{
		options = {};
	}

	window.addEventListener("resize", function(){
		if(ContextUtil.getProperty(options, "close_on_resize", true)){
			self.hide();
		}
	});

	this.setOptions = function(_options){
		if(typeof _options === "object"){
			options = _options;
		}else{
			throw new Error("Parameter 1 must be of type object")
		}
	}

	this.changeOption = function(option, value){
		if(typeof option === "string"){
			if(typeof value !== "undefined"){
				options[option] = value;
			}else{
				throw new Error("Parameter 2 must be set");
			}
		}else{
			throw new Error("Parameter 1 must be of type string");
		}
	}

	this.getOptions = function(){
		return options;
	}

	this.reload = function(){
		if(document.getElementById('cm_' + num) == null){
			var cnt = document.createElement("div");
			cnt.className = "cm_container";
			cnt.id = "cm_" + num;

			document.body.appendChild(cnt);
		}

		var container = document.getElementById('cm_' + num);
		container.innerHTML = "";

		container.appendChild(renderLevel(menu));
	}

	function renderLevel(level) {
		var ul_outer = document.createElement("ul");

		level.forEach(function(item) {
			var li = document.createElement("li");
			li.menu = self;

			if (ContextUtil.getProperty(item, "enabled", true) != true) {
				return
			}



			if(typeof item.type === "undefined" || item.type == ContextMenu.BUTTON){
				var icon_span = document.createElement("span");
				icon_span.className = 'cm_icon_span';

				if(ContextUtil.getProperty(item, "icon", "") != ""){
					icon_span.innerHTML = ContextUtil.getProperty(item, "icon", "");
				}else{
					icon_span.innerHTML = ContextUtil.getProperty(options, "default_icon", "");
				}

				var text_span = document.createElement("span");
				text_span.className = 'cm_text';

				if(ContextUtil.getProperty(item, "text", "") != ""){
					text_span.innerHTML = ContextUtil.getProperty(item, "text", "");
				}else{
					text_span.innerHTML = ContextUtil.getProperty(options, "default_text", "item");
				}

				var sub_span = document.createElement("span");
				sub_span.className = 'cm_sub_span';

				if(typeof item.sub !== "undefined"){
					if(ContextUtil.getProperty(options, "sub_icon", "") != ""){
						sub_span.innerHTML = ContextUtil.getProperty(options, "sub_icon", "");
					}else{
						sub_span.innerHTML = '&#155;';
					}
				}

				li.appendChild(icon_span);
				li.appendChild(text_span);
				li.appendChild(sub_span);

				if(!ContextUtil.getProperty(item, "enabled", true)){
					li.setAttribute("disabled", "");
				}else{
					if(typeof item.events === "object"){
						var keys = Object.keys(item.events);

						for(var i = 0; i < keys.length; i++){
							li.addEventListener(keys[i], item.events[keys[i]]);
						}
					}

					if(typeof item.sub !== "undefined"){
						li.appendChild(renderLevel(item.sub));
					}
				}
			}else{
				if(item.type == ContextMenu.DIVIDER){
					li.className = "cm_divider";
				}
			}

			ul_outer.appendChild(li);
		});

		return ul_outer;
	}

	this.display = function(e, target){
		if(typeof target !== "undefined"){
			self.contextTarget = target;
		}else{
			self.contextTarget = e.target;
		}

		var menu = document.getElementById('cm_' + num);

		var clickCoords = {x: e.clientX, y: e.clientY};
		var clickCoordsX = clickCoords.x;
		var clickCoordsY = clickCoords.y;

		var menuWidth = menu.offsetWidth + 4;
		var menuHeight = menu.offsetHeight + 4;

		var windowWidth = window.innerWidth;
		var windowHeight = window.innerHeight;

		var mouseOffset = parseInt(ContextUtil.getProperty(options, "mouse_offset", 2));

		if((windowWidth - clickCoordsX) < menuWidth){
			menu.style.left = windowWidth - menuWidth + "px";
		}else{
			menu.style.left = (clickCoordsX + mouseOffset) + "px";
		}

		if((windowHeight - clickCoordsY) < menuHeight){
			menu.style.top = windowHeight - menuHeight + "px";
		}else{
			menu.style.top = (clickCoordsY + mouseOffset) + "px";
		}

		var sizes = ContextUtil.getSizes(menu);

		if((windowWidth - clickCoordsX) < sizes.width){
			menu.classList.add("cm_border_right");
		}else{
			menu.classList.remove("cm_border_right");
		}

		if((windowHeight - clickCoordsY) < sizes.height){
			menu.classList.add("cm_border_bottom");
		}else{
			menu.classList.remove("cm_border_bottom");
		}

		menu.classList.add("display");

		if(ContextUtil.getProperty(options, "close_on_click", true)){
			window.addEventListener("click", documentClick);
		}

		e.preventDefault();
	}

	this.hide = function(){
		document.getElementById('cm_' + num).classList.remove("display");
		window.removeEventListener("click", documentClick);
	}

	function documentClick(){
		self.hide();
	}

	this.reload();
}

ContextMenu.count = 0;
ContextMenu.DIVIDER = "cm_divider";
ContextMenu.BUTTON = "cm_button";

const ContextUtil = {
	getProperty: function(options, opt, def){
		if(typeof options[opt] !== "undefined"){
			return options[opt];
		}else{
			return def;
		}
	},

	getSizes: function(obj){
		var lis = obj.getElementsByTagName('li');

		var width_def = 0;
		var height_def = 0;

		for(var i = 0; i < lis.length; i++){
			var li = lis[i];

			if(li.offsetWidth > width_def){
				width_def = li.offsetWidth;
			}

			if(li.offsetHeight > height_def){
				height_def = li.offsetHeight;
			}
		}

		var width = width_def;
		var height = height_def;

		for(var i = 0; i < lis.length; i++){
			var li = lis[i];

			var ul = li.getElementsByTagName('ul');
			if(typeof ul[0] !== "undefined"){
				var ul_size = ContextUtil.getSizes(ul[0]);

				if(width_def + ul_size.width > width){
					width = width_def + ul_size.width;
				}

				if(height_def + ul_size.height > height){
					height = height_def + ul_size.height;
				}
			}
		}

		return {
			"width": width,
			"height": height
		};
	}
};
