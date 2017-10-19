{% for host in hosts %}
host {{ host.host }} {
	hardware ethernet {{ host.mac }};
	fixed-address {{ host.ip}};
}
{% endfor %}

