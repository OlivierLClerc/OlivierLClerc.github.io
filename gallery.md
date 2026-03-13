---
layout: default
title: Gallery | Olivier Clerc
nav_key: gallery
permalink: /gallery/
page_variant: gallery-wide
show_page_heading: true
page_kicker: Photography
page_heading: Gallery
page_intro: A small rotating selection from the square images in the photo archive.
---

{% assign gallery_data = site.data.gallery_metadata %}

{% if gallery_data and gallery_data.photos and gallery_data.photos.size > 0 %}
  {% assign fallback_count = gallery_data.default_selection.size %}
  {% assign max_gallery_count = gallery_data.photos.size %}
  {% if max_gallery_count > 9 %}
    {% assign max_gallery_count = 9 %}
  {% endif %}

  {% case fallback_count %}
    {% when 1 %}
      {% assign fallback_rows = "1" | split: "," %}
    {% when 2 %}
      {% assign fallback_rows = "2" | split: "," %}
    {% when 3 %}
      {% assign fallback_rows = "3" | split: "," %}
    {% when 4 %}
      {% assign fallback_rows = "2,2" | split: "," %}
    {% when 5 %}
      {% assign fallback_rows = "2,1,2" | split: "," %}
    {% when 6 %}
      {% assign fallback_rows = "3,3" | split: "," %}
    {% when 7 %}
      {% assign fallback_rows = "2,3,2" | split: "," %}
    {% when 8 %}
      {% assign fallback_rows = "4,4" | split: "," %}
    {% else %}
      {% assign fallback_rows = "3,3,3" | split: "," %}
  {% endcase %}

  <div class="gallery-controls" aria-label="Gallery controls">
    <label class="gallery-count-control" for="gallery-count-input">
      <span>Photos</span>
      <input
        id="gallery-count-input"
        class="gallery-count-input"
        type="number"
        min="1"
        max="{{ max_gallery_count }}"
        step="1"
        value="{{ fallback_count }}"
        inputmode="numeric"
        data-gallery-count
      >
    </label>
    <button class="gallery-refresh-button" type="button" data-gallery-refresh>
      <i class="fa-solid fa-rotate-right" aria-hidden="true"></i>
      <span>Refresh</span>
    </button>
  </div>

  {% assign fallback_cursor = 0 %}
  <div class="gallery-layout" data-gallery-grid data-count="{{ fallback_count }}">
    {% for columns in fallback_rows %}
      {% assign column_count = columns | plus: 0 %}
      <div class="gallery-row" data-columns="{{ column_count }}">
        {% for ignored in (1..column_count) %}
          {% assign photo_id = gallery_data.default_selection[fallback_cursor] %}
          {% assign photo = gallery_data.photos | where: "id", photo_id | first %}
          {% if photo %}
            <div class="gallery-tile">
              {% if site.photo_asset_origin and site.photo_asset_origin != "" %}
                <img src="{{ site.photo_asset_origin }}{{ photo.src }}" alt="" loading="lazy">
              {% else %}
                <img src="{{ photo.src | relative_url }}" alt="" loading="lazy">
              {% endif %}
            </div>
          {% endif %}
          {% assign fallback_cursor = fallback_cursor | plus: 1 %}
        {% endfor %}
      </div>
    {% endfor %}
  </div>

  <script id="gallery-photo-data" type="application/json">{{ gallery_data | jsonify }}</script>
  <script>
    (function() {
      var frame = document.querySelector(".site-frame--gallery-wide");
      var sidebarToggle = document.querySelector("[data-gallery-sidebar-toggle]");
      var grid = document.querySelector("[data-gallery-grid]");
      var countInput = document.querySelector("[data-gallery-count]");
      var refreshButton = document.querySelector("[data-gallery-refresh]");
      var dataElement = document.getElementById("gallery-photo-data");
      var siteBaseUrl = {{ site.baseurl | default: "" | jsonify }} || "";
      var photoAssetOrigin = ({{ site.photo_asset_origin | default: "" | jsonify }} || "").replace(/\/+$/, "");

      if (!grid || !countInput || !refreshButton || !dataElement) {
        return;
      }

      var galleryData;
      try {
        galleryData = JSON.parse(dataElement.textContent);
      } catch (error) {
        return;
      }

      if (!galleryData || !Array.isArray(galleryData.photos) || galleryData.photos.length === 0) {
        grid.innerHTML = "<p class=\"gallery-empty\">No photos available yet.</p>";
        refreshButton.disabled = true;
        countInput.disabled = true;
        return;
      }

      var layoutMap = {
        1: [1],
        2: [2],
        3: [3],
        4: [2, 2],
        5: [2, 1, 2],
        6: [3, 3],
        7: [2, 3, 2],
        8: [4, 4],
        9: [3, 3, 3]
      };

      var photos = galleryData.photos.slice();
      var photoIds = photos.map(function(photo) {
        return photo.id;
      });
      var photoMap = new Map(
        photos.map(function(photo) {
          return [photo.id, photo];
        })
      );

      var maxCount = Math.min(9, photoIds.length);
      var currentCount = Math.min(maxCount, Array.isArray(galleryData.default_selection) ? galleryData.default_selection.length : maxCount);
      var previousSignature = "";

      function updateSidebarToggle(collapsed) {
        if (!sidebarToggle) {
          return;
        }

        sidebarToggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
        sidebarToggle.querySelector(".sidebar-toggle-label").textContent = collapsed ? "Extend panel" : "Reduce panel";
      }

      if (frame && sidebarToggle) {
        updateSidebarToggle(frame.classList.contains("is-sidebar-collapsed"));

        sidebarToggle.addEventListener("click", function() {
          var collapsed = frame.classList.toggle("is-sidebar-collapsed");
          updateSidebarToggle(collapsed);
        });
      }

      countInput.max = String(maxCount);
      countInput.value = String(currentCount);

      function clampCount(rawValue, fallback) {
        var parsedValue = Number.parseInt(rawValue, 10);
        if (Number.isNaN(parsedValue)) {
          return fallback;
        }
        return Math.max(1, Math.min(maxCount, parsedValue));
      }

      function shuffle(items) {
        var copy = items.slice();
        for (var index = copy.length - 1; index > 0; index -= 1) {
          var randomIndex = Math.floor(Math.random() * (index + 1));
          var temp = copy[index];
          copy[index] = copy[randomIndex];
          copy[randomIndex] = temp;
        }
        return copy;
      }

      function getSelectionSignature(items) {
        return items.join("|");
      }

      function buildSelection(anchorId, count) {
        var anchor = photoMap.get(anchorId);
        if (!anchor) {
          return [];
        }

        var chosenIds = [anchorId];
        var usedIds = new Set(chosenIds);

        if (Array.isArray(anchor.neighbors)) {
          anchor.neighbors.forEach(function(neighborId) {
            if (chosenIds.length >= count || usedIds.has(neighborId) || !photoMap.has(neighborId)) {
              return;
            }
            chosenIds.push(neighborId);
            usedIds.add(neighborId);
          });
        }

        if (chosenIds.length < count) {
          photoIds.forEach(function(photoId) {
            if (chosenIds.length >= count || usedIds.has(photoId)) {
              return;
            }
            chosenIds.push(photoId);
            usedIds.add(photoId);
          });
        }

        return chosenIds.slice(0, count);
      }

      function resolvePhotoSrc(photoPath) {
        if (!photoPath) {
          return "";
        }

        if (/^https?:\/\//.test(photoPath)) {
          return photoPath;
        }

        if (photoAssetOrigin) {
          return photoAssetOrigin + photoPath;
        }

        return siteBaseUrl + photoPath;
      }

      function createTile(photoId) {
        var photo = photoMap.get(photoId);
        var tile = document.createElement("div");
        tile.className = "gallery-tile";

        if (!photo) {
          return tile;
        }

        var image = document.createElement("img");
        image.src = resolvePhotoSrc(photo.src);
        image.alt = "";
        image.loading = "lazy";

        tile.appendChild(image);
        return tile;
      }

      function randomAnchorId() {
        return photoIds[Math.floor(Math.random() * photoIds.length)];
      }

      function chooseSelection(count) {
        var defaultSelection = Array.isArray(galleryData.default_selection) ? galleryData.default_selection.slice(0, count) : [];
        if (!previousSignature && defaultSelection.length === count) {
          previousSignature = getSelectionSignature(defaultSelection);
          return defaultSelection;
        }

        var selection = [];
        var signature = "";
        var tries = 0;

        while (tries < 12) {
          selection = buildSelection(randomAnchorId(), count);
          signature = getSelectionSignature(selection);

          if (signature !== previousSignature || photoIds.length <= count) {
            previousSignature = signature;
            return selection;
          }

          tries += 1;
        }

        previousSignature = signature;
        return selection;
      }

      function renderGallery(count) {
        var layout = layoutMap[count] || layoutMap[9];
        var selectedPhotos = chooseSelection(count);
        var cursor = 0;

        grid.innerHTML = "";
        grid.dataset.count = String(count);

        layout.forEach(function(columns) {
          var row = document.createElement("div");
          row.className = "gallery-row";
          row.dataset.columns = String(columns);

          for (var columnIndex = 0; columnIndex < columns; columnIndex += 1) {
            row.appendChild(createTile(selectedPhotos[cursor]));
            cursor += 1;
          }

          grid.appendChild(row);
        });

        countInput.value = String(count);
        currentCount = count;
      }

      countInput.addEventListener("input", function() {
        if (countInput.value.trim() === "") {
          return;
        }

        var nextCount = clampCount(countInput.value, currentCount);
        if (nextCount !== currentCount || countInput.value !== String(nextCount)) {
          renderGallery(nextCount);
        }
      });

      countInput.addEventListener("change", function() {
        renderGallery(clampCount(countInput.value, currentCount));
      });

      countInput.addEventListener("blur", function() {
        renderGallery(clampCount(countInput.value, currentCount));
      });

      refreshButton.addEventListener("click", function() {
        renderGallery(clampCount(countInput.value, currentCount));
      });

      renderGallery(currentCount);
    })();
  </script>
{% else %}
  <p class="gallery-empty">
    Gallery metadata is not available yet. Run <code>python scripts/build_gallery_metadata.py</code> after adding photos.
  </p>
{% endif %}
