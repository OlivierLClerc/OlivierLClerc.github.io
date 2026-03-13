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
  {% assign color_mode_data = gallery_data.modes.color %}
  {% assign bw_mode_data = gallery_data.modes.bw %}
  {% assign default_mode = gallery_data.default_mode | default: "color" %}
  {% if default_mode == "color" %}
    {% assign default_mode_data = color_mode_data %}
  {% else %}
    {% assign default_mode_data = bw_mode_data %}
  {% endif %}

  {% assign fallback_count = default_mode_data.default_selection.size %}
  {% assign max_gallery_count = default_mode_data.count %}
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
    <div class="gallery-control-cluster">
      <div class="gallery-mode-toggle" role="group" aria-label="Photo mode">
        <button
          class="gallery-mode-button{% if default_mode == 'color' %} is-active{% endif %}"
          type="button"
          data-gallery-mode="color"
          aria-pressed="{% if default_mode == 'color' %}true{% else %}false{% endif %}"
          {% if color_mode_data.count == 0 %}disabled{% endif %}
        >
          Color
        </button>
        <button
          class="gallery-mode-button{% if default_mode == 'bw' %} is-active{% endif %}"
          type="button"
          data-gallery-mode="bw"
          aria-pressed="{% if default_mode == 'bw' %}true{% else %}false{% endif %}"
          {% if bw_mode_data.count == 0 %}disabled{% endif %}
        >
          B&amp;W
        </button>
      </div>
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
      <label class="gallery-divergence-control" for="gallery-divergence-input">
        <span>Divergence</span>
        <div class="gallery-divergence-slider-wrap">
          <span class="gallery-divergence-edge">Close</span>
          <input
            id="gallery-divergence-input"
            class="gallery-divergence-input"
            type="range"
            min="0"
            max="100"
            step="1"
            value="0"
            data-gallery-divergence
            aria-describedby="gallery-divergence-state"
          >
          <span class="gallery-divergence-edge">Wide</span>
        </div>
        <span class="gallery-divergence-state" id="gallery-divergence-state" data-gallery-divergence-state>
          Applies on refresh
        </span>
      </label>
    </div>
    <button class="gallery-refresh-button" type="button" data-gallery-refresh>
      <i class="fa-solid fa-rotate-right" aria-hidden="true"></i>
      <span>Refresh</span>
    </button>
  </div>

  {% assign fallback_cursor = 0 %}
  <div class="gallery-layout" data-gallery-grid data-count="{{ fallback_count }}" data-mode="{{ default_mode }}">
    {% for columns in fallback_rows %}
      {% assign column_count = columns | plus: 0 %}
      <div class="gallery-row" data-columns="{{ column_count }}">
        {% for ignored in (1..column_count) %}
          {% assign photo_id = default_mode_data.default_selection[fallback_cursor] %}
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
      var divergenceInput = document.querySelector("[data-gallery-divergence]");
      var divergenceState = document.querySelector("[data-gallery-divergence-state]");
      var refreshButton = document.querySelector("[data-gallery-refresh]");
      var modeButtons = Array.from(document.querySelectorAll("[data-gallery-mode]"));
      var dataElement = document.getElementById("gallery-photo-data");
      var siteBaseUrl = {{ site.baseurl | default: "" | jsonify }} || "";
      var photoAssetOrigin = ({{ site.photo_asset_origin | default: "" | jsonify }} || "").replace(/\/+$/, "");

      if (!grid || !countInput || !divergenceInput || !refreshButton || !modeButtons.length || !dataElement) {
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
        divergenceInput.disabled = true;
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

      var galleryModes = galleryData.modes || {};
      var modeOrder = ["color", "bw"];
      var photos = galleryData.photos.slice();
      var photoMap = new Map(
        photos.map(function(photo) {
          return [photo.id, photo];
        })
      );
      var photoIdsByMode = modeOrder.reduce(function(result, mode) {
        result[mode] = photos
          .filter(function(photo) {
            return photo.photo_mode === mode;
          })
          .map(function(photo) {
            return photo.id;
          });
        return result;
      }, {});

      var currentMode = galleryData.default_mode || (photoIdsByMode.color.length ? "color" : "bw");
      if (!photoIdsByMode[currentMode] || photoIdsByMode[currentMode].length === 0) {
        currentMode = photoIdsByMode.color.length ? "color" : "bw";
      }

      var currentCount = 1;
      var appliedDivergence = 0;
      var pendingDivergence = 0;
      var previousSignatureByMode = { color: "", bw: "" };

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

      function getModeInfo(mode) {
        return galleryModes[mode] || { count: 0, default_anchor: "", default_selection: [] };
      }

      function getModeMaxCount(mode) {
        return Math.min(9, (photoIdsByMode[mode] || []).length);
      }

      function clampCount(rawValue, fallback) {
        var modeMax = getModeMaxCount(currentMode);
        var parsedValue = Number.parseInt(rawValue, 10);

        if (Number.isNaN(parsedValue)) {
          return Math.max(1, Math.min(modeMax, fallback));
        }

        return Math.max(1, Math.min(modeMax, parsedValue));
      }

      function clampDivergence(rawValue, fallback) {
        var parsedValue = Number.parseInt(rawValue, 10);
        if (Number.isNaN(parsedValue)) {
          return fallback;
        }
        return Math.max(0, Math.min(100, parsedValue));
      }

      function randomItem(items) {
        if (!items.length) {
          return null;
        }
        return items[Math.floor(Math.random() * items.length)];
      }

      function getSelectionSignature(items) {
        return items.join("|");
      }

      function updateModeButtons() {
        modeButtons.forEach(function(button) {
          var mode = button.getAttribute("data-gallery-mode");
          var enabled = getModeMaxCount(mode) > 0;
          button.disabled = !enabled;
          button.classList.toggle("is-active", mode === currentMode);
          button.setAttribute("aria-pressed", mode === currentMode ? "true" : "false");
        });
      }

      function updateDivergenceState() {
        if (!divergenceState) {
          return;
        }

        if (pendingDivergence === appliedDivergence) {
          divergenceState.textContent = "Applies on refresh";
          return;
        }

        divergenceState.textContent = "Pending: " + String(pendingDivergence) + "%";
      }

      function syncCountInput() {
        var modeMax = getModeMaxCount(currentMode);
        if (modeMax <= 0) {
          grid.innerHTML = "<p class=\"gallery-empty\">No photos available in this mode.</p>";
          countInput.disabled = true;
          divergenceInput.disabled = true;
          refreshButton.disabled = true;
          return false;
        }

        countInput.disabled = false;
        divergenceInput.disabled = false;
        refreshButton.disabled = false;
        countInput.max = String(modeMax);
        currentCount = clampCount(countInput.value || currentCount, currentCount || modeMax);
        countInput.value = String(currentCount);
        return true;
      }

      function buildSelection(anchorId, count, divergenceValue, mode) {
        var anchor = photoMap.get(anchorId);
        if (!anchor) {
          return [];
        }

        var modeIds = photoIdsByMode[mode] || [];
        var chosenIds = [anchorId];
        var usedIds = new Set(chosenIds);
        var neighborCount = Math.max(0, count - 1);
        var divergence = divergenceValue / 100;
        var orderedNeighbors = Array.isArray(anchor.neighbors)
          ? anchor.neighbors.filter(function(neighborId) {
              var neighbor = photoMap.get(neighborId);
              return neighbor && neighbor.photo_mode === mode && !usedIds.has(neighborId);
            })
          : [];

        if (neighborCount > 0 && orderedNeighbors.length > 0) {
          if (divergence === 0) {
            orderedNeighbors.slice(0, neighborCount).forEach(function(neighborId) {
              chosenIds.push(neighborId);
              usedIds.add(neighborId);
            });
          } else {
            var maxRankWindow = orderedNeighbors.length;
            var candidateWindow = Math.round(
              neighborCount + (divergence * Math.max(0, maxRankWindow - neighborCount))
            );
            candidateWindow = Math.max(neighborCount, Math.min(maxRankWindow, candidateWindow));

            var candidatePool = orderedNeighbors.slice(0, candidateWindow);

            for (var segmentIndex = 0; segmentIndex < neighborCount; segmentIndex += 1) {
              var segmentStart = Math.floor((segmentIndex * candidatePool.length) / neighborCount);
              var segmentEnd = Math.floor(((segmentIndex + 1) * candidatePool.length) / neighborCount);
              var segmentItems = candidatePool.slice(segmentStart, segmentEnd).filter(function(neighborId) {
                return !usedIds.has(neighborId);
              });
              var chosenNeighborId = randomItem(segmentItems);

              if (!chosenNeighborId) {
                continue;
              }

              chosenIds.push(chosenNeighborId);
              usedIds.add(chosenNeighborId);
            }

            candidatePool.forEach(function(neighborId) {
              if (chosenIds.length >= count || usedIds.has(neighborId)) {
                return;
              }
              chosenIds.push(neighborId);
              usedIds.add(neighborId);
            });
          }
        }

        orderedNeighbors.forEach(function(neighborId) {
          if (chosenIds.length >= count || usedIds.has(neighborId)) {
            return;
          }
          chosenIds.push(neighborId);
          usedIds.add(neighborId);
        });

        modeIds.forEach(function(photoId) {
          if (chosenIds.length >= count || usedIds.has(photoId)) {
            return;
          }
          chosenIds.push(photoId);
          usedIds.add(photoId);
        });

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

      function randomAnchorId(mode) {
        var modeIds = photoIdsByMode[mode] || [];
        return modeIds[Math.floor(Math.random() * modeIds.length)];
      }

      function chooseSelection(count, divergenceValue, mode) {
        var modeInfo = getModeInfo(mode);
        var defaultSelection = Array.isArray(modeInfo.default_selection) ? modeInfo.default_selection.slice(0, count) : [];

        if (!previousSignatureByMode[mode] && divergenceValue === 0 && defaultSelection.length === count) {
          previousSignatureByMode[mode] = getSelectionSignature(defaultSelection);
          return defaultSelection;
        }

        var selection = [];
        var signature = "";
        var tries = 0;

        while (tries < 12) {
          selection = buildSelection(randomAnchorId(mode), count, divergenceValue, mode);
          signature = getSelectionSignature(selection);

          if (signature !== previousSignatureByMode[mode] || (photoIdsByMode[mode] || []).length <= count) {
            previousSignatureByMode[mode] = signature;
            return selection;
          }

          tries += 1;
        }

        previousSignatureByMode[mode] = signature;
        return selection;
      }

      function renderGallery(count) {
        var layout = layoutMap[count] || layoutMap[9];
        var selectedPhotos = chooseSelection(count, appliedDivergence, currentMode);
        var cursor = 0;

        grid.innerHTML = "";
        grid.dataset.count = String(count);
        grid.dataset.mode = currentMode;

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

      function applyMode(mode) {
        if (!photoIdsByMode[mode] || photoIdsByMode[mode].length === 0) {
          return;
        }

        currentMode = mode;
        previousSignatureByMode[mode] = "";
        updateModeButtons();

        if (syncCountInput()) {
          renderGallery(currentCount);
        }
      }

      divergenceInput.value = "0";
      appliedDivergence = 0;
      pendingDivergence = 0;
      updateModeButtons();
      updateDivergenceState();

      if (syncCountInput()) {
        currentCount = Math.min(
          getModeMaxCount(currentMode),
          Array.isArray(getModeInfo(currentMode).default_selection) && getModeInfo(currentMode).default_selection.length
            ? getModeInfo(currentMode).default_selection.length
            : getModeMaxCount(currentMode)
        );
        countInput.value = String(currentCount);
        renderGallery(currentCount);
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

      divergenceInput.addEventListener("input", function() {
        pendingDivergence = clampDivergence(divergenceInput.value, pendingDivergence);
        divergenceInput.value = String(pendingDivergence);
        updateDivergenceState();
      });

      divergenceInput.addEventListener("change", function() {
        pendingDivergence = clampDivergence(divergenceInput.value, pendingDivergence);
        divergenceInput.value = String(pendingDivergence);
        updateDivergenceState();
      });

      refreshButton.addEventListener("click", function() {
        appliedDivergence = clampDivergence(divergenceInput.value, pendingDivergence);
        pendingDivergence = appliedDivergence;
        updateDivergenceState();
        renderGallery(clampCount(countInput.value, currentCount));
      });

      modeButtons.forEach(function(button) {
        button.addEventListener("click", function() {
          applyMode(button.getAttribute("data-gallery-mode"));
        });
      });
    })();
  </script>
{% else %}
  <p class="gallery-empty">
    Gallery metadata is not available yet. Run <code>python scripts/build_gallery_metadata.py</code> after adding photos.
  </p>
{% endif %}
