---
layout: default
title: Olivier Clerc
---

<div class="hero">
  <h1>Olivier Clerc</h1>
  <p class="lead">
    Starting Researcher at Inria Bordeaux working at the intersection of AI and education.
  </p>
  <p class="hero-cta">
    <a class="cta-button" href="{{ '/ressources/CV_Olivier_Clerc.pdf' | relative_url }}">Download CV</a>
    <a class="cta-button cta-secondary" href="mailto:oclerc38@gmail.com">Email</a>
  </p>
</div>

<nav class="section-nav">
  <a href="#about">About</a>
  <a href="#current-work">Current Work</a>
  <a href="#previous-research">Previous Research</a>
  <a href="#publications">Publications</a>
  <a href="#teaching">Teaching</a>
  <a href="#other-stuff">Other Stuff</a>
  <a href="#links">Links</a>
</nav>

{% capture content_markdown %}
{% include_relative main.md %}
{% endcapture %}
{{ content_markdown | markdownify }}

