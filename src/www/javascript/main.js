var app = {
	init: function() {
		this.sorter = this._get_sorter();
		this.searcher = this._get_searcher();
		this.data = this._get_fetched_data();
		this.current_data = this.data;
	},
	restructure: function(reference) {
		var event = window.event;
		var target = event.target || event.srcElement;

		event.preventDefault();

		var data = this.current_data;
		var name = this.sorter[reference];
		var use_descending = this._has_class(target, "ascending");
		var is_integer = this._get_attribute(target, "data-sorter-is-integer");

		var get_value = function(target, key) {
			var parser = new DOMParser();
			var doc = parser.parseFromString(target[key], 'text/html');
			var span = doc.getElementsByTagName("span");

			if (span.length == 1) {
				return span[0].getAttribute("data-value");
			} else {
				return doc.body.innerHTML;
			}
		};

		data.sort(function(first, second) {
			var first_value = get_value(first, name);
			var second_value = get_value(second, name);

			if (is_integer === "true") {
				if (use_descending) {
					return first_value - second_value;
				} else {
					return second_value - first_value;
				}
			} else {
				if (use_descending) {
					return first_value < second_value ? 1 : -1;
				} else {
					return first_value > second_value ? 1 : -1;
				}
			}
		});

		this._clear_class();

		if (use_descending) {
			target.classList.add("descending");
		} else {
			target.classList.add("ascending");
		}

		document.getElementById("packages-content").innerHTML = this._rebuild_tbody(data);
	},
	search: function() {
		var keywords, line, text, skip, i, j;
		var data = this.data;
		var searcher = this.searcher;
		var results = [];
		var value = document.getElementById("search-box").value;

		value = value.replace(/\s{2,}/g, ' ').trim().toLowerCase();

		if (value == "") {
			results = this.data;
		} else {
			for (i = 0; i < data.length; i++) {
				line = data[i];
				skip = false;

				for (key in line) {
					if (searcher.includes(key)) {
						text = line[key].toLowerCase();

						if (!skip && text.indexOf(value) > -1) {
							results.push(line);
							skip = true;
						}
					}
				}
			}
		}

		this.current_data = results;

		if (results.length == 0) {
			document.getElementById("table-content").style.display = "none";
			document.getElementById("empty-content").innerHTML = "We did not find results for: <strong>" + value + "</strong>";
		} else {
			document.getElementById("table-content").style.display = "table";
			document.getElementById("empty-content").innerHTML = "";
			document.getElementById("packages-content").innerHTML = this._rebuild_tbody(results);
		}
	},
	_rebuild_tbody: function(data) {
		var line, i, key;
		var tbody = "";
		var content = "";
		var tr_tempate = "<tr>$content</tr>";

		for (i = 0; i < data.length; i++) {
			line = data[i];
			content = "";

			for (key in line) {
				content += "<td>" + line[key] + "</td>";
			}

			tbody += tr_tempate.replace("$content", content);
		}

		return tbody;
	},
	_has_class: function(target, name) {
		return new RegExp('(\\s|^)' + name + '(\\s|$)').test(target.className);
	},
	_get_attribute: function(target, name) {
		return target.getAttribute(name);
	},
	_clear_class: function() {
		var i;
		var th = document.getElementsByClassName("event-th");

		for (i = 0; i < th.length; i++) {
			th[i].classList.remove("ascending");
			th[i].classList.remove("descending");
		}

	},
	_get_searcher: function() {
		var i, reference, is_searchable;
		var data = [];
		var th = document.getElementsByClassName("event-th");

		for (i = 0; i < th.length; i++) {
			is_searchable = th[i].getAttribute("data-is-searchable");

			if (is_searchable == "true") {
				reference = th[i].getAttribute("data-sorter-reference");
				data.push(reference);
			}
		}

		return data;
	},
	_get_sorter: function() {
		var i;
		var data = [];
		var th = document.getElementsByClassName("event-th");

		for (i = 0; i < th.length; i++) {
			data[i] = th[i].getAttribute("data-sorter-reference");
		}

		return data;
	},
	_get_fetched_data: function() {
		var td, name, content, i, j;
		var data = [];
		var tr = document.getElementsByTagName("tr");

		for (i = 0; i < tr.length; i++) {
			td = tr[i].getElementsByTagName("td");
			content = {};

			for (j = 0; j < td.length; j++) {
				name = this.sorter[j];
				content[name] = td[j].innerHTML;
			}

			if (td.length > 0) {
				data.push(content);
			}
		}

		return data;
	}
};
