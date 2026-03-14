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
      <div class="gallery-slider-control{% unless default_mode_data.default_color_enabled %} is-disabled{% endunless %}" data-gallery-color-control>
        <div class="gallery-slider-head">
          <span data-gallery-color-label>{% if default_mode == 'bw' %}Tone Proximity{% else %}Color Proximity{% endif %}</span>
          <button
            class="gallery-scale-toggle{% if default_mode_data.default_color_enabled %} is-active{% endif %}"
            type="button"
            data-gallery-color-toggle
            aria-pressed="{% if default_mode_data.default_color_enabled %}true{% else %}false{% endif %}"
          >
            {% if default_mode_data.default_color_enabled %}On{% else %}Off{% endif %}
          </button>
        </div>
        <div class="gallery-slider-wrap">
          <span class="gallery-slider-edge">Loose</span>
          <input
            id="gallery-color-proximity-input"
            class="gallery-slider-input"
            type="range"
            min="0"
            max="100"
            step="1"
            value="{{ default_mode_data.default_color_proximity | default: 70 }}"
            data-gallery-color-proximity
            {% unless default_mode_data.default_color_enabled %}disabled{% endunless %}
          >
          <span class="gallery-slider-edge">Tight</span>
        </div>
      </div>
      <div class="gallery-slider-control{% unless default_mode_data.default_geometry_enabled %} is-disabled{% endunless %}" data-gallery-geometry-control>
        <div class="gallery-slider-head">
          <span>Geometry Proximity</span>
          <button
            class="gallery-scale-toggle{% if default_mode_data.default_geometry_enabled %} is-active{% endif %}"
            type="button"
            data-gallery-geometry-toggle
            aria-pressed="{% if default_mode_data.default_geometry_enabled %}true{% else %}false{% endif %}"
          >
            {% if default_mode_data.default_geometry_enabled %}On{% else %}Off{% endif %}
          </button>
        </div>
        <div class="gallery-slider-wrap">
          <span class="gallery-slider-edge">Loose</span>
          <input
            id="gallery-geometry-proximity-input"
            class="gallery-slider-input"
            type="range"
            min="0"
            max="100"
            step="1"
            value="{{ default_mode_data.default_geometry_proximity | default: 70 }}"
            data-gallery-geometry-proximity
            {% unless default_mode_data.default_geometry_enabled %}disabled{% endunless %}
          >
          <span class="gallery-slider-edge">Tight</span>
        </div>
      </div>
      <span class="gallery-control-state" data-gallery-control-state>Refresh picks a new anchor</span>
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
      var colorProximityInput = document.querySelector("[data-gallery-color-proximity]");
      var geometryProximityInput = document.querySelector("[data-gallery-geometry-proximity]");
      var colorControl = document.querySelector("[data-gallery-color-control]");
      var geometryControl = document.querySelector("[data-gallery-geometry-control]");
      var colorToggleButton = document.querySelector("[data-gallery-color-toggle]");
      var geometryToggleButton = document.querySelector("[data-gallery-geometry-toggle]");
      var controlStateLabel = document.querySelector("[data-gallery-control-state]");
      var colorLabel = document.querySelector("[data-gallery-color-label]");
      var refreshButton = document.querySelector("[data-gallery-refresh]");
      var modeButtons = Array.from(document.querySelectorAll("[data-gallery-mode]"));
      var dataElement = document.getElementById("gallery-photo-data");
      var siteBaseUrl = {{ site.baseurl | default: "" | jsonify }} || "";
      var photoAssetOrigin = ({{ site.photo_asset_origin | default: "" | jsonify }} || "").replace(/\/+$/, "");

      if (!grid || !countInput || !colorProximityInput || !geometryProximityInput || !colorToggleButton || !geometryToggleButton || !refreshButton || !modeButtons.length || !dataElement) {
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
        colorProximityInput.disabled = true;
        geometryProximityInput.disabled = true;
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

      function normalizeEnabled(rawValue, fallback) {
        if (typeof rawValue === "boolean") {
          return rawValue;
        }
        if (typeof rawValue === "string") {
          return rawValue === "true";
        }
        if (typeof rawValue === "number") {
          return rawValue !== 0;
        }
        return fallback;
      }

      function createShuffleSeed(mode) {
        return [
          mode,
          Date.now().toString(36),
          Math.random().toString(36).slice(2)
        ].join("|");
      }

      var controlStateByMode = modeOrder.reduce(function(result, mode) {
        var modeInfo = getModeInfo(mode);
        var defaultColor = clampProximity(modeInfo.default_color_proximity, 70);
        var defaultGeometry = clampProximity(modeInfo.default_geometry_proximity, 70);
        var defaultColorEnabled = normalizeEnabled(modeInfo.default_color_enabled, true);
        var defaultGeometryEnabled = normalizeEnabled(modeInfo.default_geometry_enabled, true);
        result[mode] = {
          appliedColor: defaultColor,
          pendingColor: defaultColor,
          appliedGeometry: defaultGeometry,
          pendingGeometry: defaultGeometry,
          appliedColorEnabled: defaultColorEnabled,
          pendingColorEnabled: defaultColorEnabled,
          appliedGeometryEnabled: defaultGeometryEnabled,
          pendingGeometryEnabled: defaultGeometryEnabled,
          anchorId: modeInfo.default_anchor || "",
          signature: "",
          shuffleSeed: mode + "|default",
          initialized: false
        };
        return result;
      }, {});

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
        return galleryModes[mode] || {
          count: 0,
          default_anchor: "",
          default_selection: [],
          default_color_proximity: 70,
          default_geometry_proximity: 70,
          default_color_enabled: true,
          default_geometry_enabled: true
        };
      }

      function getModeControlState(mode) {
        return controlStateByMode[mode];
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

      function clampProximity(rawValue, fallback) {
        var parsedValue = Number.parseInt(rawValue, 10);
        if (Number.isNaN(parsedValue)) {
          return fallback;
        }
        return Math.max(0, Math.min(100, parsedValue));
      }

      function strictnessWindowSize(modeCount, count, proximity) {
        var totalNeighbors = Math.max(0, modeCount - 1);
        var neighborCount = Math.max(0, count - 1);
        if (totalNeighbors === 0 || neighborCount === 0) {
          return 0;
        }

        var strictness = clampProximity(proximity, 70) / 100;
        var windowFraction = 0.06 + Math.pow(1 - strictness, 2) * 0.44;
        var windowSize = Math.round(windowFraction * totalNeighbors);
        return Math.max(neighborCount, Math.min(totalNeighbors, windowSize));
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

      function updateControlLabels() {
        if (!colorLabel) {
          return;
        }
        colorLabel.textContent = currentMode === "bw" ? "Tone Proximity" : "Color Proximity";
      }

      function setScaleToggleState(button, enabled) {
        if (!button) {
          return;
        }

        button.classList.toggle("is-active", enabled);
        button.setAttribute("aria-pressed", enabled ? "true" : "false");
        button.textContent = enabled ? "On" : "Off";
      }

      function updateControlStateMessage() {
        if (!controlStateLabel) {
          return;
        }

        var modeState = getModeControlState(currentMode);
        var hasPendingChanges =
          modeState.pendingColor !== modeState.appliedColor ||
          modeState.pendingGeometry !== modeState.appliedGeometry ||
          modeState.pendingColorEnabled !== modeState.appliedColorEnabled ||
          modeState.pendingGeometryEnabled !== modeState.appliedGeometryEnabled;

        if (hasPendingChanges) {
          controlStateLabel.textContent = "Pending changes apply on refresh";
          return;
        }

        if (!modeState.appliedColorEnabled && !modeState.appliedGeometryEnabled) {
          controlStateLabel.textContent = "Refresh picks a new anchor and reseeds the random set";
          return;
        }

        controlStateLabel.textContent = "Refresh picks a new anchor and rebuilds the distance ladder";
      }

      function syncControlInputsFromState() {
        var modeState = getModeControlState(currentMode);
        colorProximityInput.value = String(modeState.pendingColor);
        geometryProximityInput.value = String(modeState.pendingGeometry);
        colorProximityInput.disabled = !modeState.pendingColorEnabled;
        geometryProximityInput.disabled = !modeState.pendingGeometryEnabled;
        if (colorControl) {
          colorControl.classList.toggle("is-disabled", !modeState.pendingColorEnabled);
        }
        if (geometryControl) {
          geometryControl.classList.toggle("is-disabled", !modeState.pendingGeometryEnabled);
        }
        setScaleToggleState(colorToggleButton, modeState.pendingColorEnabled);
        setScaleToggleState(geometryToggleButton, modeState.pendingGeometryEnabled);
        updateControlLabels();
        updateControlStateMessage();
      }

      function syncCountInput() {
        var modeMax = getModeMaxCount(currentMode);
        if (modeMax <= 0) {
          grid.innerHTML = "<p class=\"gallery-empty\">No photos available in this mode.</p>";
          countInput.disabled = true;
          colorProximityInput.disabled = true;
          geometryProximityInput.disabled = true;
          colorToggleButton.disabled = true;
          geometryToggleButton.disabled = true;
          refreshButton.disabled = true;
          return false;
        }

        countInput.disabled = false;
        colorToggleButton.disabled = false;
        geometryToggleButton.disabled = false;
        colorProximityInput.disabled = !getModeControlState(currentMode).pendingColorEnabled;
        geometryProximityInput.disabled = !getModeControlState(currentMode).pendingGeometryEnabled;
        refreshButton.disabled = false;
        countInput.max = String(modeMax);
        currentCount = clampCount(countInput.value || currentCount, currentCount || modeMax);
        countInput.value = String(currentCount);
        return true;
      }

      function sortCandidates(candidateIds, colorRank, geometryRank, colorNorm, geometryNorm) {
        var uniqueIds = Array.from(new Set(candidateIds));
        var maxColorNorm = Math.max(colorNorm, 1);
        var maxGeometryNorm = Math.max(geometryNorm, 1);

        return uniqueIds.sort(function(left, right) {
          var leftHasColor = Object.prototype.hasOwnProperty.call(colorRank, left);
          var rightHasColor = Object.prototype.hasOwnProperty.call(colorRank, right);
          var leftHasGeometry = Object.prototype.hasOwnProperty.call(geometryRank, left);
          var rightHasGeometry = Object.prototype.hasOwnProperty.call(geometryRank, right);
          var leftHits = Number(leftHasColor) + Number(leftHasGeometry);
          var rightHits = Number(rightHasColor) + Number(rightHasGeometry);

          if (leftHits !== rightHits) {
            return rightHits - leftHits;
          }

          var leftScore = (leftHasColor ? colorRank[left] / maxColorNorm : 1.35) + (leftHasGeometry ? geometryRank[left] / maxGeometryNorm : 1.35);
          var rightScore = (rightHasColor ? colorRank[right] / maxColorNorm : 1.35) + (rightHasGeometry ? geometryRank[right] / maxGeometryNorm : 1.35);

          if (leftScore !== rightScore) {
            return leftScore - rightScore;
          }

          var leftBestRank = leftHasColor ? colorRank[left] : 1000000000;
          if (leftHasGeometry) {
            leftBestRank = Math.min(leftBestRank, geometryRank[left]);
          }
          var rightBestRank = rightHasColor ? colorRank[right] : 1000000000;
          if (rightHasGeometry) {
            rightBestRank = Math.min(rightBestRank, geometryRank[right]);
          }

          if (leftBestRank !== rightBestRank) {
            return leftBestRank - rightBestRank;
          }

          return left.localeCompare(right);
        });
      }

      function stableHash(text) {
        var hash = 2166136261;

        for (var index = 0; index < text.length; index += 1) {
          hash ^= text.charCodeAt(index);
          hash = Math.imul(hash, 16777619);
        }

        return hash >>> 0;
      }

      function stableShuffleIds(identifiers, seedText) {
        return identifiers.slice().sort(function(left, right) {
          var leftHash = stableHash(seedText + "|" + left);
          var rightHash = stableHash(seedText + "|" + right);

          if (leftHash !== rightHash) {
            return leftHash - rightHash;
          }

          return left.localeCompare(right);
        });
      }

      function evenlySpacedSelection(orderedIds, count) {
        if (count <= 0 || !orderedIds.length) {
          return [];
        }

        if (orderedIds.length <= count) {
          return orderedIds.slice(0, count);
        }

        if (count === 1) {
          return [orderedIds[0]];
        }

        var chosen = [];
        var used = new Set();

        for (var slot = 0; slot < count; slot += 1) {
          var rawIndex = Math.round((slot * (orderedIds.length - 1)) / (count - 1));
          var candidateIndex = rawIndex;

          while (candidateIndex < orderedIds.length && used.has(orderedIds[candidateIndex])) {
            candidateIndex += 1;
          }

          if (candidateIndex >= orderedIds.length) {
            candidateIndex = rawIndex - 1;
            while (candidateIndex >= 0 && used.has(orderedIds[candidateIndex])) {
              candidateIndex -= 1;
            }
          }

          if (candidateIndex < 0) {
            continue;
          }

          chosen.push([candidateIndex, orderedIds[candidateIndex]]);
          used.add(orderedIds[candidateIndex]);
        }

        return chosen
          .sort(function(left, right) {
            return left[0] - right[0];
          })
          .map(function(entry) {
            return entry[1];
          });
      }

      function buildSelection(anchorId, count, mode, settings) {
        var anchor = photoMap.get(anchorId);
        if (!anchor) {
          return [];
        }

        var modeIds = photoIdsByMode[mode] || [];
        var boundedCount = Math.max(1, Math.min(count, modeIds.length));
        if (boundedCount === 1) {
          return [anchorId];
        }

        var modeSet = new Set(modeIds);
        var neighborCount = boundedCount - 1;
        var colorEnabled = settings.colorEnabled !== false;
        var geometryEnabled = settings.geometryEnabled !== false;
        var orderedColor = Array.isArray(anchor.color_neighbors)
          ? anchor.color_neighbors.filter(function(identifier) {
              return modeSet.has(identifier) && identifier !== anchorId;
            })
          : [];
        var orderedGeometry = Array.isArray(anchor.geometry_neighbors)
          ? anchor.geometry_neighbors.filter(function(identifier) {
              return modeSet.has(identifier) && identifier !== anchorId;
            })
          : [];

        if (!colorEnabled && !geometryEnabled) {
          return [anchorId].concat(
            evenlySpacedSelection(
              stableShuffleIds(
                modeIds.filter(function(identifier) {
                  return identifier !== anchorId;
                }),
                anchorId + "|" + (settings.shuffleSeed || "default")
              ),
              neighborCount
            )
          );
        }

        if (colorEnabled && !geometryEnabled) {
          return [anchorId].concat(
            evenlySpacedSelection(
              orderedColor.slice(0, strictnessWindowSize(modeIds.length, boundedCount, settings.colorProximity)),
              neighborCount
            )
          );
        }

        if (geometryEnabled && !colorEnabled) {
          return [anchorId].concat(
            evenlySpacedSelection(
              orderedGeometry.slice(0, strictnessWindowSize(modeIds.length, boundedCount, settings.geometryProximity)),
              neighborCount
            )
          );
        }

        var colorWindowSize = strictnessWindowSize(modeIds.length, boundedCount, settings.colorProximity);
        var geometryWindowSize = strictnessWindowSize(modeIds.length, boundedCount, settings.geometryProximity);
        var colorWindow = orderedColor.slice(0, colorWindowSize);
        var geometryWindow = orderedGeometry.slice(0, geometryWindowSize);
        var colorWindowRank = {};
        var geometryWindowRank = {};
        var colorFullRank = {};
        var geometryFullRank = {};

        colorWindow.forEach(function(identifier, index) {
          colorWindowRank[identifier] = index;
        });
        geometryWindow.forEach(function(identifier, index) {
          geometryWindowRank[identifier] = index;
        });
        orderedColor.forEach(function(identifier, index) {
          colorFullRank[identifier] = index;
        });
        orderedGeometry.forEach(function(identifier, index) {
          geometryFullRank[identifier] = index;
        });

        var coreCandidates = colorWindow.filter(function(identifier) {
          return Object.prototype.hasOwnProperty.call(geometryWindowRank, identifier);
        });
        var orderedCandidates = sortCandidates(coreCandidates, colorFullRank, geometryFullRank, orderedColor.length, orderedGeometry.length);

        if (orderedCandidates.length < neighborCount) {
          orderedCandidates = sortCandidates(
            colorWindow.concat(geometryWindow),
            colorFullRank,
            geometryFullRank,
            orderedColor.length,
            orderedGeometry.length
          );
        }

        if (orderedCandidates.length < neighborCount) {
          orderedCandidates = sortCandidates(
            orderedColor.concat(orderedGeometry).concat(modeIds).filter(function(identifier) {
              return identifier !== anchorId;
            }),
            colorFullRank,
            geometryFullRank,
            orderedColor.length,
            orderedGeometry.length
          );
        }

        return [anchorId].concat(evenlySpacedSelection(orderedCandidates, neighborCount));
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

      function createTile(photoId, isAnchor) {
        var photo = photoMap.get(photoId);
        var tile = document.createElement("button");
        tile.type = "button";
        tile.className = "gallery-tile gallery-tile-button";
        tile.setAttribute("data-gallery-photo", photoId || "");

        if (isAnchor) {
          tile.classList.add("is-anchor");
        }

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

      function renderGallery(count, selectedPhotos) {
        var layout = layoutMap[count] || layoutMap[9];
        var cursor = 0;

        grid.innerHTML = "";
        grid.dataset.count = String(count);
        grid.dataset.mode = currentMode;

        layout.forEach(function(columns) {
          var row = document.createElement("div");
          row.className = "gallery-row";
          row.dataset.columns = String(columns);

          for (var columnIndex = 0; columnIndex < columns; columnIndex += 1) {
            row.appendChild(createTile(selectedPhotos[cursor], cursor === 0));
            cursor += 1;
          }

          grid.appendChild(row);
        });

        countInput.value = String(count);
        currentCount = count;
      }

      function getColorControlLabel(mode) {
        return mode === "bw" ? "Tone Proximity" : "Color Proximity";
      }

      function randomAnchorId(mode) {
        var modeIds = photoIdsByMode[mode] || [];
        if (!modeIds.length) {
          return "";
        }
        return modeIds[Math.floor(Math.random() * modeIds.length)];
      }

      function getAppliedSettings(modeState) {
        return {
          colorProximity: modeState.appliedColor,
          geometryProximity: modeState.appliedGeometry,
          colorEnabled: modeState.appliedColorEnabled,
          geometryEnabled: modeState.appliedGeometryEnabled,
          shuffleSeed: modeState.shuffleSeed
        };
      }

      function deterministicSelectionForMode(mode, count) {
        var modeInfo = getModeInfo(mode);
        var modeState = getModeControlState(mode);
        var modeIds = photoIdsByMode[mode] || [];
        var boundedCount = Math.max(1, Math.min(count, modeIds.length));
        var defaultSelection = Array.isArray(modeInfo.default_selection) ? modeInfo.default_selection.slice(0, boundedCount) : [];
        var isDefaultState = !modeState.initialized &&
          modeState.anchorId === (modeInfo.default_anchor || "") &&
          modeState.appliedColor === clampProximity(modeInfo.default_color_proximity, 70) &&
          modeState.appliedGeometry === clampProximity(modeInfo.default_geometry_proximity, 70) &&
          modeState.appliedColorEnabled === normalizeEnabled(modeInfo.default_color_enabled, true) &&
          modeState.appliedGeometryEnabled === normalizeEnabled(modeInfo.default_geometry_enabled, true);

        if (isDefaultState && defaultSelection.length === boundedCount) {
          modeState.signature = getSelectionSignature(defaultSelection);
          modeState.anchorId = defaultSelection[0] || modeInfo.default_anchor || "";
          modeState.initialized = true;
          return defaultSelection;
        }

        var anchorId = modeState.anchorId || modeInfo.default_anchor || modeIds[0] || "";
        var selection = buildSelection(anchorId, boundedCount, mode, getAppliedSettings(modeState));
        if (!selection.length && defaultSelection.length) {
          selection = defaultSelection;
        }
        if (!selection.length && anchorId) {
          selection = [anchorId];
        }

        modeState.signature = getSelectionSignature(selection);
        modeState.anchorId = selection[0] || anchorId;
        modeState.initialized = true;
        return selection;
      }

      function refreshSelection(mode, count) {
        var modeState = getModeControlState(mode);
        var modeIds = photoIdsByMode[mode] || [];
        var boundedCount = Math.max(1, Math.min(count, modeIds.length));
        modeState.appliedColor = modeState.pendingColor;
        modeState.appliedGeometry = modeState.pendingGeometry;
        modeState.appliedColorEnabled = modeState.pendingColorEnabled;
        modeState.appliedGeometryEnabled = modeState.pendingGeometryEnabled;
        modeState.shuffleSeed = createShuffleSeed(mode);

        var selection = [];
        var signature = modeState.signature;
        var tries = 0;

        while (tries < 12) {
          var anchorId = randomAnchorId(mode);
          selection = buildSelection(anchorId, boundedCount, mode, getAppliedSettings(modeState));
          signature = getSelectionSignature(selection);

          if (signature !== modeState.signature || modeIds.length <= boundedCount) {
            modeState.signature = signature;
            modeState.anchorId = selection[0] || anchorId;
            modeState.initialized = true;
            return selection;
          }

          tries += 1;
        }

        selection = deterministicSelectionForMode(mode, boundedCount);
        modeState.signature = getSelectionSignature(selection);
        modeState.anchorId = selection[0] || modeState.anchorId;
        return selection;
      }

      function rerenderAroundAnchor(mode, count, anchorId) {
        var modeState = getModeControlState(mode);
        if (anchorId) {
          modeState.anchorId = anchorId;
        }
        modeState.initialized = true;

        var selection = buildSelection(modeState.anchorId, count, mode, getAppliedSettings(modeState));
        if (!selection.length) {
          selection = deterministicSelectionForMode(mode, count);
        }

        modeState.signature = getSelectionSignature(selection);
        modeState.anchorId = selection[0] || modeState.anchorId;
        renderGallery(count, selection);
      }

      function renderCurrentMode(count) {
        var selection = deterministicSelectionForMode(currentMode, count);
        renderGallery(count, selection);
      }

      function applyMode(mode) {
        if (!photoIdsByMode[mode] || photoIdsByMode[mode].length === 0) {
          return;
        }

        currentMode = mode;
        updateModeButtons();
        syncControlInputsFromState();

        if (syncCountInput()) {
          renderCurrentMode(currentCount);
        }
      }

      updateModeButtons();
      syncControlInputsFromState();

      if (syncCountInput()) {
        currentCount = Math.min(
          getModeMaxCount(currentMode),
          Array.isArray(getModeInfo(currentMode).default_selection) && getModeInfo(currentMode).default_selection.length
            ? getModeInfo(currentMode).default_selection.length
            : getModeMaxCount(currentMode)
        );
        countInput.value = String(currentCount);
        renderCurrentMode(currentCount);
      }

      countInput.addEventListener("input", function() {
        if (countInput.value.trim() === "") {
          return;
        }

        var nextCount = clampCount(countInput.value, currentCount);
        if (nextCount !== currentCount || countInput.value !== String(nextCount)) {
          renderCurrentMode(nextCount);
        }
      });

      countInput.addEventListener("change", function() {
        renderCurrentMode(clampCount(countInput.value, currentCount));
      });

      countInput.addEventListener("blur", function() {
        renderCurrentMode(clampCount(countInput.value, currentCount));
      });

      colorProximityInput.addEventListener("input", function() {
        var modeState = getModeControlState(currentMode);
        modeState.pendingColor = clampProximity(colorProximityInput.value, modeState.pendingColor);
        colorProximityInput.value = String(modeState.pendingColor);
        updateControlStateMessage();
      });

      colorProximityInput.addEventListener("change", function() {
        var modeState = getModeControlState(currentMode);
        modeState.pendingColor = clampProximity(colorProximityInput.value, modeState.pendingColor);
        colorProximityInput.value = String(modeState.pendingColor);
        updateControlStateMessage();
      });

      geometryProximityInput.addEventListener("input", function() {
        var modeState = getModeControlState(currentMode);
        modeState.pendingGeometry = clampProximity(geometryProximityInput.value, modeState.pendingGeometry);
        geometryProximityInput.value = String(modeState.pendingGeometry);
        updateControlStateMessage();
      });

      geometryProximityInput.addEventListener("change", function() {
        var modeState = getModeControlState(currentMode);
        modeState.pendingGeometry = clampProximity(geometryProximityInput.value, modeState.pendingGeometry);
        geometryProximityInput.value = String(modeState.pendingGeometry);
        updateControlStateMessage();
      });

      colorToggleButton.addEventListener("click", function() {
        var modeState = getModeControlState(currentMode);
        modeState.pendingColorEnabled = !modeState.pendingColorEnabled;
        syncControlInputsFromState();
      });

      geometryToggleButton.addEventListener("click", function() {
        var modeState = getModeControlState(currentMode);
        modeState.pendingGeometryEnabled = !modeState.pendingGeometryEnabled;
        syncControlInputsFromState();
      });

      refreshButton.addEventListener("click", function() {
        var nextCount = clampCount(countInput.value, currentCount);
        var selection = refreshSelection(currentMode, nextCount);
        renderGallery(nextCount, selection);
        syncControlInputsFromState();
      });

      modeButtons.forEach(function(button) {
        button.addEventListener("click", function() {
          applyMode(button.getAttribute("data-gallery-mode"));
        });
      });

      grid.addEventListener("click", function(event) {
        var tile = event.target.closest("[data-gallery-photo]");
        if (!tile) {
          return;
        }

        var photoId = tile.getAttribute("data-gallery-photo");
        if (!photoId || !photoMap.has(photoId)) {
          return;
        }

        rerenderAroundAnchor(currentMode, currentCount, photoId);
      });
    })();
  </script>
{% else %}
  <p class="gallery-empty">
    Gallery metadata is not available yet. Run <code>python scripts/build_gallery_metadata.py</code> after adding photos.
  </p>
{% endif %}
