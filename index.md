---
layout: default
title: About | Olivier Clerc
nav_key: about
permalink: /
---

{% capture home_content %}
{% include_relative main.md %}
{% endcapture %}
{{ home_content | markdownify }}
