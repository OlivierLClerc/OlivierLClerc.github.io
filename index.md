---
layout: default
title: Olivier Clerc
---

{% capture raw_content %}
{% include_relative main.md %}
{% endcapture %}
{% assign section_blocks = raw_content | split: '## ' %}

<div class="page-shell">
  <aside class="profile-sidebar">
    <img
      class="profile-image"
      src="{{ '/ressources/profil.png' | relative_url }}"
      alt="Portrait of Olivier Clerc"
    >
    <h1 class="profile-name">Olivier Clerc</h1>
    <p class="profile-role">AI and education research at Inria Bordeaux</p>
    <p class="profile-email"><a href="mailto:oclerc38@gmail.com">oclerc38@gmail.com</a></p>

    <div class="profile-links" aria-label="Profile links">
      <a href="{{ '/ressources/CV_Olivier_Clerc.pdf' | relative_url }}" aria-label="Curriculum Vitae">
        <i class="fa-regular fa-file-lines"></i>
      </a>
      <a href="https://github.com/OlivierLClerc" target="_blank" rel="noopener noreferrer" aria-label="GitHub">
        <i class="fa-brands fa-github"></i>
      </a>
      <a href="https://www.linkedin.com/in/olivier-clerc-592885150/" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn">
        <i class="fa-brands fa-linkedin"></i>
      </a>
      <a href="https://www.researchgate.net/profile/Olivier-Clerc-2?ev=hdr_xprf" target="_blank" rel="noopener noreferrer" aria-label="ResearchGate">
        <i class="fa-brands fa-researchgate"></i>
      </a>
      <a href="mailto:oclerc38@gmail.com" aria-label="Email">
        <i class="fa-regular fa-envelope"></i>
      </a>
    </div>
  </aside>

  <main class="content-area">
    <nav class="section-nav" aria-label="Section navigation">
      {% for block in section_blocks offset: 1 %}
        {% assign lines = block | split: '\n' %}
        {% assign heading = lines[0] | strip %}
        {% assign section_id = heading | slugify %}
        <a href="#{{ section_id }}">{{ heading }}</a>
      {% endfor %}
    </nav>

    <div class="panel-stack">
      {% for block in section_blocks offset: 1 %}
        {% assign lines = block | split: '\n' %}
        {% assign heading = lines[0] | strip %}
        {% assign section_id = heading | slugify %}
        {% capture section_markdown %}## {{ block }}{% endcapture %}
        <section class="panel" id="{{ section_id }}">
          {{ section_markdown | markdownify }}
        </section>
      {% endfor %}
    </div>
  </main>
</div>
